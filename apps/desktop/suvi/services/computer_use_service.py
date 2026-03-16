import asyncio
import io
from typing import List
from google import genai
from google.genai import types
from google.genai.types import (
    Content,
    GenerateContentConfig,
    Part,
    Tool
)
import mss
from PIL import Image
from PyQt6.QtCore import QObject, pyqtSignal

from apps.desktop.suvi.executor.dispatcher import ActionDispatcher

class ComputerUseService(QObject):
    voice_confirmation_requested = pyqtSignal(str, str)
    MODEL_ID = "gemini-2.5-computer-use-preview-10-2025"

    def __init__(self, client: genai.Client, ui_widget=None, firestore_service=None, logger=None, env_scanner=None):
        super().__init__()
        self.client = client
        self.ui_widget = ui_widget
        self.firestore = firestore_service
        self.logger = logger
        self.env_scanner = env_scanner
        self._interrupt_requested = False
        self._voice_response_future = None

        self.dispatcher = ActionDispatcher(ui_widget, env_scanner=env_scanner)

    def interrupt(self):
        self._interrupt_requested = True

    def _capture_screen(self) -> bytes:
        with mss.mss() as sct:
            
            frame = sct.grab(sct.monitors[1])

        img = Image.frombytes("RGB", frame.size, frame.bgra, "raw", "BGRX")
        img = img.resize((1440, 900), Image.Resampling.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=85)
        return buf.getvalue()

    def _get_tools(self) -> List[Tool]:
        computer_use_tool = Tool(
            computer_use=types.ComputerUse(
                environment=types.Environment.ENVIRONMENT_UNSPECIFIED,
            )
        )
        
        custom_tool = Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="launch_application",
                    description="Launch a desktop application",
                    parameters={
                        "type": "object",
                        "properties": {
                            "app_name": {
                                "type": "string"
                            }
                        },
                        "required": ["app_name"]
                    }
                ),
                types.FunctionDeclaration(
                    name="open_url",
                    description="Open a URL in the default browser",
                    parameters={
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string"
                            }
                        },
                        "required": ["url"]
                    }
                ),
                types.FunctionDeclaration(
                    name="voice_confirmation",
                    description="Ask the user for confirmation",
                    parameters={
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string"
                            }
                        },
                        "required": ["question"]
                    }
                )
            ]
        )

        return [computer_use_tool, custom_tool]

    async def execute_task(
        self,
        intent: str,
        user_id: str,
        session_id: str,
        on_action: callable = None,
        on_screenshot: callable = None,
    ) -> dict:
        self._interrupt_requested = False
        max_turns = 30
        actions_taken = []

        system_instruction = (
            "You are an expert Windows desktop automation agent.\n"
            "Your ONLY job is to execute the user's intent by invoking tools.\n"
            "CRITICAL RULES:\n"
            "1. You MUST always call at least one tool per turn. Never respond with just text.\n"
            "2. For multi-step tasks (e.g., 'open spotify and play a song'), do ONE logical step per turn. Wait for the app to load before interacting with it.\n"
            "3. If an app takes time to load, use the 'wait' tool or 'click_at' a safe blank space to give it time.\n"
            "4. LOOK at the screenshot CAREFULLY. Base your clicks on what you actually see, not what you expect to see.\n"
            "5. If an action failed, try an alternative approach (e.g., use Search or Start menu).\n"
        )

        config = GenerateContentConfig(
            system_instruction=system_instruction,
            tools=self._get_tools(),
            temperature=0.0
        )

        screenshot_bytes = self._capture_screen()

        if on_screenshot:
            on_screenshot(screenshot_bytes)

        contents = [
            Content(
                role="user",
                parts=[
                    Part.from_text(text=intent),
                    Part.from_bytes(data=screenshot_bytes, mime_type="image/jpeg"),
                ],
            )
        ]

        print(f"Starting Agent Loop with prompt: '{intent}'")

        for turn in range(max_turns):
            if self._interrupt_requested:
                return {"success": False, "reason": "user_interrupted"}

            response = await self.client.aio.models.generate_content(
                model=self.MODEL_ID,
                contents=contents,
                config=config
            )

            if not response.candidates:
                print("No candidates returned")
                break

            contents.append(response.candidates[0].content)

            function_calls = []

            for part in response.candidates[0].content.parts:
                if part.function_call:
                    function_calls.append(part.function_call)

            if not function_calls:
                print("Agent finished")
                return {"success": True, "actions_taken": actions_taken}

            execution_results = []

            for call in function_calls:
                action_name = call.name
                args = call.args or {}

                print(f"Executing {action_name} {args}")

                
                if on_action:
                    on_action(f"Executing {action_name}")

                result = await self.dispatcher.execute(action_name, args)

                actions_taken.append({
                    "step": turn,
                    "action": action_name
                })

                execution_results.append((call.id, action_name, result))

            await asyncio.sleep(1.0)

            screenshot_bytes = self._capture_screen()

            if on_screenshot:
                on_screenshot(screenshot_bytes)

            response_parts = []

            for call_id, name, result in execution_results:
                response_parts.append(
                    Part.from_function_response(
                        name=name,
                        response={
                            "result": str(result),
                            "current_url": "local://desktop"
                        }
                    )
                )

            response_parts.append(
                Part.from_bytes(data=screenshot_bytes, mime_type="image/jpeg")
            )

            contents.append(Content(role="user", parts=response_parts))

        return {"success": False, "reason": "max_steps_reached"}

    def set_voice_response(self, response: str):
        if self._voice_response_future and not self._voice_response_future.done():
            self._voice_response_future.set_result(response)

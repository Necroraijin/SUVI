import asyncio
import io
from typing import Optional, List, Tuple, Dict
from google import genai
from google.genai import types
from google.genai.types import (
    ComputerUse, Content, Environment,
    FunctionResponse, FunctionResponseBlob,
    GenerateContentConfig, Part, Tool, ThinkingConfig
)
import pyautogui
import mss
from PIL import Image
from PyQt6.QtCore import QObject, pyqtSignal

from apps.desktop.suvi.executor.dispatcher import ActionDispatcher

class ComputerUseService(QObject):
    """
    Drives the Gemini Computer Use model via Vertex AI.
    Perfectly aligned with Google's official Jupyter Notebook implementation.
    """
    # Signal to UI to request voice confirmation from the user
    voice_confirmation_requested = pyqtSignal(str, str) # title, message

    # Use the correct Gemini 2.5 computer use preview model
    MODEL_ID = "gemini-2.5-computer-use-preview-10-2025"

    def __init__(self, client: genai.Client, ui_widget=None, firestore_service=None, logger=None, env_scanner=None):
        super().__init__()
        self.client = client
        self.firestore = firestore_service
        self.logger = logger
        self.env_scanner = env_scanner
        self._interrupt_requested = False
        self._voice_response_future = None
        
        # Security: Use the dispatcher for all physical actions
        self.dispatcher = ActionDispatcher(ui_widget, env_scanner=env_scanner)

    def interrupt(self):
        """Called when user says 'stop' or clicks cancel."""
        self._interrupt_requested = True

    def _capture_screen(self) -> bytes:
        """Capture screen as image bytes for the Computer Use model.
        
        Google recommends 1440x900 as the optimal resolution.
        Uses JPEG for faster encoding and smaller payload.
        """
        with mss.mss() as sct:
            frame = sct.grab(sct.monitors[1])
        img = Image.frombytes("RGB", frame.size, frame.bgra, "raw", "BGRX")
        
        # Resize to 1440x900 (Google's recommended resolution for Computer Use)
        img = img.resize((1440, 900), Image.Resampling.LANCZOS)
            
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=85)
        return buf.getvalue()

    async def describe_screen(self) -> str:
        """
        Captures the screen and uses the vision model to provide a 
        vivid, helpful description for visually impaired users.
        """
        screenshot_bytes = self._capture_screen()
        
        prompt = """Describe this desktop screen in detail for a blind user.
Mention open windows, visible text, icons on the taskbar, and any notifications.
Be spatial (e.g., 'On the top right, there is a close button').
Be a helpful companion."""

        try:
            response = await self.client.aio.models.generate_content(
                model=self.MODEL_ID,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_bytes(data=screenshot_bytes, mime_type="image/png"),
                            types.Part.from_text(text=prompt)
                        ]
                    )
                ]
            )
            return response.text
        except Exception as e:
            return f"I'm sorry, I'm having trouble seeing the screen right now. Error: {e}"

    def _get_tools(self) -> List[Tool]:
        """Returns the tools for desktop automation.
        
        The Computer Use model REQUIRES types.Tool(computer_use=...) to be present.
        Custom functions go in a SEPARATE types.Tool(function_declarations=...).
        See: https://ai.google.dev/gemini-api/docs/computer-use#custom-functions
        """
        # Combine into a SINGLE Tool object to avoid AFC array index errors
        combined_tool = Tool(
            computer_use=types.ComputerUse(
                environment=types.Environment.ENVIRONMENT_UNSPECIFIED,
            ),
            function_declarations=[
                types.FunctionDeclaration(
                    name="launch_application",
                    description="Launches a desktop application by name. Use this instead of trying to find and click app icons.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "app_name": types.Schema(type=types.Type.STRING, description="Name of the application (e.g., 'chrome', 'notepad', 'firefox').")
                        },
                        required=["app_name"]
                    )
                ),
                types.FunctionDeclaration(
                    name="open_url",
                    description="Opens a URL in the default web browser.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "url": types.Schema(type=types.Type.STRING, description="The URL to open.")
                        },
                        required=["url"]
                    )
                ),
                types.FunctionDeclaration(
                    name="voice_confirmation",
                    description="Asks the user for verbal confirmation before performing a risky action.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "question": types.Schema(type=types.Type.STRING, description="The yes/no question to ask the user.")
                        },
                        required=["question"]
                    )
                ),
            ]
        )
        
        return [combined_tool]

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
        
        # System instruction for the Computer Use agent
        # Inject environment awareness context so the model knows what's available
        env_context = ""
        if self.env_scanner:
            env_context = self.env_scanner.get_context_for_ai()
        
        system_instruction = (
            "You are an expert Windows desktop automation engine. Your ONLY job is to execute the user's intent by invoking tools.\n\n"
            + (f"{env_context}\n\n" if env_context else "")
            + "CRITICAL RULES (DO NOT IGNORE):\n"
            "1. You MUST use at least one tool per turn. NEVER just reply with text.\n"
            "2. DO NOT return empty candidates or generic text. If you don't know what to do next, do NOT terminate. Instead, use the 'wait' tool to give the UI more time to load, or use 'click_at' on a safe blank space.\n"
            "3. LOOK at the screenshot CAREFULLY. Base clicks on what you actually SEE.\n"
            "4. For multi-step tasks, do ONE logical step per turn, verify with the next screenshot, then continue.\n"
            "5. If a website is needed, use 'open_url' or launch the default browser and then search.\n"
            "6. NEVER claim you completed an action without seeing visual confirmation in the screenshot.\n"
            "7. If something didn't work (e.g. click failed), try an alternative approach (e.g., use the Start menu, use search, or use keyboard shortcuts).\n"
            "8. You are operating a REAL computer. The user is watching you. Do NOT explain your actions—just execute the tools.\n\n"
            "EXAMPLES:\n"
            "- 'play a song on youtube' → open_url({'url': 'youtube.com'}) → wait → type_text_at(search bar, 'song name') → click result\n"
            "- 'open notepad and type hello' → launch_application({'app_name': 'notepad'}) → wait → type_text({'text': 'hello'})"
        )

        config = GenerateContentConfig(
            system_instruction=system_instruction,
            tools=self._get_tools(),
            temperature=0.0
        )

        # ──────────────────────────────────────────────────────────
        # 2. Initial Setup: Capture desktop + send user intent
        # ──────────────────────────────────────────────────────────
        screenshot_bytes = self._capture_screen()
        if on_screenshot:
            on_screenshot(screenshot_bytes)

        contents = [
            Content(
                role="user",
                parts=[
                    Part(text=intent),
                    Part.from_bytes(data=screenshot_bytes, mime_type="image/jpeg"),
                ],
            )
        ]

        print(f"Starting Agent Loop with prompt: '{intent}'")
        print(f"  📸 Initial screenshot captured ({len(screenshot_bytes)} bytes)")

        # ──────────────────────────────────────────────────────────
        # 3. Main Agent Loop — screenshot → think → act → screenshot
        # ──────────────────────────────────────────────────────────
        for turn in range(max_turns):
            if self._interrupt_requested:
                return {"success": False, "reason": "user_interrupted", "actions_taken": actions_taken}

            print(f"\n═══ Turn {turn + 1}/{max_turns} ═══")
            
            # ── Call the model ──
            max_retries = 3
            retry_count = 0
            response = None
            
            while retry_count < max_retries:
                try:
                    response = await self.client.aio.models.generate_content(
                        model=self.MODEL_ID, 
                        contents=contents, 
                        config=config
                    )
                    break
                except Exception as e:
                    error_str = str(e)
                    if "503" in error_str or "UNAVAILABLE" in error_str:
                        retry_count += 1
                        print(f"⏳ Google servers busy (503). Retrying in 3s... ({retry_count}/{max_retries})")
                        await asyncio.sleep(3)
                    else:
                        print(f"❗️ API Error: {e}")
                        return {"success": False, "reason": f"api_error: {e}", "actions_taken": actions_taken}
            
            if not response:
                print("❌ Failed after maximum retries due to server demand.")
                return {"success": False, "reason": "api_error_503_max_retries", "actions_taken": actions_taken}

            if not response.candidates:
                print("⚠️ Model returned no candidates (safety filter?). Terminating.")
                break

            # Append model's response to conversation history
            contents.append(response.candidates[0].content)

            # ── Extract function calls vs text ──
            function_calls = []
            model_thoughts = []
            for part in response.candidates[0].content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    function_calls.append(part.function_call)
                elif hasattr(part, "text") and part.text:
                    model_thoughts.append(part.text)
            
            if model_thoughts:
                thought_text = " ".join(model_thoughts)[:200]
                print(f"  🧠 Model thinking: {thought_text}")

            # ── If no function calls, agent is done ──
            if not function_calls:
                final_text = " ".join(model_thoughts)
                print(f"✅ Agent Finished: {final_text[:200]}")
                
                # Save Memory to Firestore
                try:
                    if not self.firestore:
                        from google.cloud import firestore
                        import os
                        project_id = os.getenv("GCP_PROJECT_ID")
                        if project_id:
                            self.firestore = firestore.AsyncClient(project=project_id)
                    if self.firestore:
                        from datetime import datetime
                        doc_ref = self.firestore.collection("suvi_memory").document()
                        await doc_ref.set({
                            "user_id": user_id,
                            "session_id": session_id,
                            "timestamp": datetime.utcnow(),
                            "intent": intent,
                            "actions_taken": actions_taken,
                            "status": "success",
                        })
                        print(f"💾 Memory saved to Firestore: {len(actions_taken)} actions.")
                except Exception as e:
                    print(f"⚠️ Failed to save memory to Firestore: {e}")
                
                return {"success": True, "actions_taken": actions_taken, "final_screenshot": screenshot_bytes}

            # ── Execute each action ──
            print(f"  ⚡ Executing {len(function_calls)} action(s)...")
            execution_results = []
            
            for call in function_calls:
                action_name = call.name
                action_args = {k: v for k, v in call.args.items()} if call.args else {}
                call_id = call.id if hasattr(call, 'id') and call.id else ""
                
                print(f"    → {action_name}({action_args})")
                if on_action:
                    on_action(f"Executing: {action_name}")
                
                # Voice confirmation for risky actions
                if action_name == "voice_confirmation":
                    message = action_args.get("question", action_args.get("message", "Is it okay?"))
                    autopilot_on = self.dispatcher.is_autopilot_enabled()
                    
                    if autopilot_on and "dangerous" not in message.lower():
                        print(f"    ✈️ Autopilot: Auto-confirming: {message}")
                        result = "yes"
                    else:
                        print(f"    🎙️ Asking user: {message}")
                        self.voice_confirmation_requested.emit("SUVI Security", message)
                        self._voice_response_future = asyncio.get_event_loop().create_future()
                        try:
                            result = await asyncio.wait_for(self._voice_response_future, timeout=30.0)
                        except asyncio.TimeoutError:
                            result = "User did not respond in time."
                else:
                    result = await self.dispatcher.execute(action_name, action_args)
                
                actions_taken.append({"step": turn + 1, "action": action_name, "result": str(result)[:100]})
                execution_results.append((call_id, action_name, result))
                
                status_emoji = "✅" if result == "success" else "⚠️"
                print(f"    {status_emoji} {action_name} → {result}")

            # ── Wait for UI to settle after actions ──
            # Longer wait for app launches (they take time to render)
            has_launch = any(name in ["launch_application", "open_web_browser", "navigate"] for _, name, _ in execution_results)
            wait_time = 2.0 if has_launch else 0.8
            print(f"  ⏱️ Waiting {wait_time}s for UI to settle...")
            await asyncio.sleep(wait_time)
            
            # ── Capture new screenshot — THIS IS CRITICAL ──
            # The model MUST see the result of its actions to plan the next step
            screenshot_bytes = self._capture_screen()
            if on_screenshot:
                on_screenshot(screenshot_bytes)
            print(f"  📸 New screenshot captured ({len(screenshot_bytes)} bytes)")
            
            # ── Build FunctionResponse with screenshot embedded ──
            # Per Google docs: each FunctionResponse should include the new screenshot
            # so the model can see what the screen looks like after the action
            response_parts = []
            for call_id, name, result in execution_results:
                response_parts.append(
                    Part.from_function_response(
                        name=name,
                        response={
                            "result": str(result),
                            "url": "local://desktop"  # Required by the API schema even for local actions
                        },
                    )
                )
            # Attach the fresh screenshot so the model can SEE the current state
            response_parts.append(
                Part.from_bytes(data=screenshot_bytes, mime_type="image/jpeg")
            )
            
            contents.append(Content(role="user", parts=response_parts))
            print(f"  📤 Sent {len(execution_results)} results + screenshot to model (history: {len(contents)} msgs)")

        return {"success": False, "reason": "max_steps_reached", "actions_taken": actions_taken}


    def set_voice_response(self, response: str):
        """Called by SUVIApplication when the user answers via voice."""
        if self._voice_response_future and not self._voice_response_future.done():
            self._voice_response_future.set_result(response)

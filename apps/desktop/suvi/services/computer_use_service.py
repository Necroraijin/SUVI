import asyncio
import io
from typing import Optional, List, Tuple
from google import genai
from google.genai.types import (
    ComputerUse, Content, Environment,
    FunctionResponse, FunctionResponseBlob,
    GenerateContentConfig, Part, Tool, ThinkingConfig
)
import pyautogui
import mss
from PIL import Image

from apps.desktop.suvi.executor.dispatcher import ActionDispatcher

class ComputerUseService:
    """
    Drives the Gemini Computer Use model via Vertex AI.
    Perfectly aligned with Google's official Jupyter Notebook implementation.
    """

    # Using the Gemini 3 Flash Preview as supported by the notebook
    MODEL_ID = "gemini-3-flash-preview"

    def __init__(self, client: genai.Client, ui_widget=None, firestore_service=None, logger=None):
        self.client = client
        self.firestore = firestore_service
        self.logger = logger
        self._interrupt_requested = False
        
        # Security: Use the dispatcher for all physical actions
        self.dispatcher = ActionDispatcher(ui_widget)

    def interrupt(self):
        """Called when user says 'stop' or clicks cancel."""
        self._interrupt_requested = True

    def _capture_screen(self) -> bytes:
        """Capture screen as PNG bytes (Required by Computer Use model)."""
        with mss.mss() as sct:
            frame = sct.grab(sct.monitors[1])
        img = Image.frombytes("RGB", frame.size, frame.bgra, "raw", "BGRX")
        
        # Resize to maintain reasonable resolution but faster
        w, h = img.size
        if w > 1366:
            img = img.resize((1366, int(1366 * h / w)), Image.Resampling.LANCZOS)
            
        buf = io.BytesIO()
        img.save(buf, "PNG", optimize=False)
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

    async def execute_task(
        self,
        intent: str,
        user_id: str,
        session_id: str,
        on_action: callable = None,
        on_screenshot: callable = None,
    ) -> dict:
        self._interrupt_requested = False
        max_turns = 15
        actions_taken = []
        
        # 1. Base Configuration
        config_kwargs = {
            "tools": [
                Tool(
                    computer_use=ComputerUse(
                        environment=Environment.ENVIRONMENT_BROWSER,
                        excluded_predefined_functions=["drag_and_drop", "open_web_browser"]
                    )
                )
            ]
        }
        
        # Add thinking config for Gemini 3
        if "gemini-3" in self.MODEL_ID:
            config_kwargs["thinking_config"] = ThinkingConfig(include_thoughts=True)
            
        config = GenerateContentConfig(**config_kwargs)

        # 2. Initial Setup: Prompt + Initial Screenshot
        screenshot_bytes = self._capture_screen()
        if on_screenshot:
            on_screenshot(screenshot_bytes)

        contents = [
            Content(
                role="user",
                parts=[
                    Part(text=intent),
                    Part.from_bytes(data=screenshot_bytes, mime_type="image/png"),
                ],
            )
        ]

        print(f"Starting Agent Loop with prompt: '{intent}'")

        # 3. Main Agent Loop
        for turn in range(max_turns):
            if self._interrupt_requested:
                return {"success": False, "reason": "user_interrupted", "actions_taken": actions_taken}

            print(f"\n Turn {turn + 1}")
            
            # Retry logic for 503 High Demand errors
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
                    break # Success, exit retry loop
                except Exception as e:
                    error_str = str(e)
                    if "503" in error_str or "UNAVAILABLE" in error_str:
                        retry_count += 1
                        print(f"⏳ Google servers busy (503). Retrying in 3 seconds... ({retry_count}/{max_retries})")
                        await asyncio.sleep(3)
                    else:
                        print(f"❗️ API Error: {e}")
                        return {"success": False, "reason": f"api_error: {e}", "actions_taken": actions_taken}
            
            if not response:
                print("❌ Failed after maximum retries due to server demand.")
                return {"success": False, "reason": "api_error_503_max_retries", "actions_taken": actions_taken}

            if not response.candidates:
                print("Model returned no candidates (safety filter?). Terminating.")
                break

            # Append model's response to history
            contents.append(response.candidates[0].content)

            # Extract Function Calls
            function_calls = [
                part.function_call
                for part in response.candidates[0].content.parts
                if hasattr(part, "function_call") and part.function_call
            ]

            # If no function calls, the model thinks it is done
            if not function_calls:
                final_text = "".join(
                    part.text for part in response.candidates[0].content.parts if hasattr(part, "text") and part.text
                )
                print(f"Agent Finished: {final_text}")
                
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

            # Execute Actions via the Dispatcher
            status, execution_results = await self._execute_function_calls(response, on_action)
            
            # Record actions
            for call_id, name, result in execution_results:
                actions_taken.append({"step": turn + 1, "action": name})

            if status == "NO_ACTION":
                continue

            # 4. Capture New State and Create FunctionResponse
            # We wait briefly so the UI can settle
            await asyncio.sleep(0.5) 
            screenshot_bytes = self._capture_screen()
            if on_screenshot:
                on_screenshot(screenshot_bytes)
            
            # Use raw dictionaries to avoid Pydantic union type mismatch errors
            function_response_parts = []
            for call_id, name, result in execution_results:
                function_response_parts.append({
                    "function_response": {
                        "id": call_id,
                        "name": name,
                        "response": {"result": result, "url": "desktop"},
                        "parts": [
                            {
                                "inline_data": {
                                    "mime_type": "image/png",
                                    "data": screenshot_bytes
                                }
                            }
                        ]
                    }
                })
                
            # Append the user's feedback to history
            contents.append(Content(role="user", parts=function_response_parts))
            print(f"State captured. History now has {len(contents)} messages.")

        return {"success": False, "reason": "max_steps_reached", "actions_taken": actions_taken}

    async def _execute_function_calls(self, response, on_action) -> Tuple[str, List[Tuple[str, str, str]]]:
        """Extracts and executes function calls via the secure dispatcher."""
        candidate = response.candidates[0]
        function_calls = []
        thoughts = []

        for part in candidate.content.parts:
            if hasattr(part, "function_call") and part.function_call:
                function_calls.append(part.function_call)
            elif hasattr(part, "text") and part.text:
                thoughts.append(part.text)

        if thoughts:
            print(f" 🧠 Model Reasoning: {' '.join(thoughts)}")

        if not function_calls:
            return "NO_ACTION", []

        results = []
        for call in function_calls:
            print(f"⚡ Requesting Action: {call.name}")
            if on_action:
                on_action(f"Requesting: {call.name}")

            call_id = call.id if hasattr(call, 'id') and call.id else ""
            
            # Delegate to the dispatcher
            result = await self.dispatcher.execute(call.name, call.args)
                
            results.append((call_id, call.name, result))
            
        return "CONTINUE", results

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

class ComputerUseService:
    """
    Drives the Gemini Computer Use model via Vertex AI.
    Perfectly aligned with Google's official Jupyter Notebook implementation.
    """

    # Using the Gemini 3 Flash Preview as supported by the notebook
    MODEL_ID = "gemini-3-flash-preview"

    def __init__(self, client: genai.Client, firestore_service=None, logger=None):
        self.client = client
        self.firestore = firestore_service
        self.logger = logger
        self._interrupt_requested = False
        
        # Determine screen resolution once for normalization
        self.screen_width, self.screen_height = pyautogui.size()

    def _normalize_x(self, x: int) -> int:
        return int(x / 1000 * self.screen_width)

    def _normalize_y(self, y: int) -> int:
        return int(y / 1000 * self.screen_height)

    def interrupt(self):
        """Called when user says 'stop' or clicks cancel."""
        self._interrupt_requested = True

    def _capture_screen(self) -> bytes:
        """Capture screen as JPEG bytes for faster processing and lower latency."""
        with mss.mss() as sct:
            frame = sct.grab(sct.monitors[1])
        img = Image.frombytes("RGB", frame.size, frame.bgra, "raw", "BGRX")
        
        # Resize to maintain reasonable resolution but faster
        w, h = img.size
        if w > 1366:
            img = img.resize((1366, int(1366 * h / w)), Image.Resampling.LANCZOS)
            
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=80)
        return buf.getvalue()

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
                        excluded_predefined_functions=["drag_and_drop"]
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
                    Part.from_bytes(data=screenshot_bytes, mime_type="image/jpeg"),
                ],
            )
        ]

        print(f"Starting Agent Loop with prompt: '{intent}'")

        # 3. Main Agent Loop
        for turn in range(max_turns):
            if self._interrupt_requested:
                return {"success": False, "reason": "user_interrupted", "actions_taken": actions_taken}

            print(f"\n Turn {turn + 1}")
            
            try:
                response = await self.client.aio.models.generate_content(
                    model=self.MODEL_ID, 
                    contents=contents, 
                    config=config
                )
            except Exception as e:
                print(f"❗️ API Error: {e}")
                return {"success": False, "reason": f"api_error: {e}", "actions_taken": actions_taken}

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
                return {"success": True, "actions_taken": actions_taken, "final_screenshot": screenshot_bytes}

            # Execute Actions
            status, execution_results = await self._execute_function_calls(response, on_action)
            
            for name, _ in execution_results:
                actions_taken.append({"step": turn + 1, "action": name})

            if status == "NO_ACTION":
                continue

            # 4. Capture New State and Create FunctionResponse
            function_response_parts = []
            for name, result in execution_results:
                # Capture new state after the action
                await asyncio.sleep(0.2) # Faster UI settle wait
                screenshot_bytes = self._capture_screen()
                if on_screenshot:
                    on_screenshot(screenshot_bytes)
                
                # Format exactly as the notebook requires
                function_response_parts.append(
                    Part(
                        function_response=FunctionResponse(
                            name=name,
                            response={"result": result, "url": "desktop"}, # Mocking URL since we are on desktop
                            parts=[
                                Part(
                                    inline_data=FunctionResponseBlob(
                                        mime_type="image/jpeg", data=screenshot_bytes
                                    )
                                )
                            ],
                        )
                    )
                )
                
            # Append the user's feedback to history
            contents.append(Content(role="user", parts=function_response_parts))
            print(f"State captured. History now has {len(contents)} messages.")

        return {"success": False, "reason": "max_steps_reached", "actions_taken": actions_taken}

    async def _execute_function_calls(self, response, on_action) -> Tuple[str, List[Tuple[str, str]]]:
        """Extracts and executes PyAutoGUI function calls based on model response."""
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
            result = "success"
            action_desc = call.name
            
            print(f"⚡ Executing Action: {call.name}")
            if on_action:
                on_action(f"Executing: {call.name}")

            try:
                if call.name == "click_at":
                    x = self._normalize_x(call.args["x"])
                    y = self._normalize_y(call.args["y"])
                    action_desc = f"Clicking at ({x}, {y})"
                    pyautogui.click(x, y)
                    
                elif call.name == "type_text_at":
                    x = self._normalize_x(call.args["x"])
                    y = self._normalize_y(call.args["y"])
                    text = call.args["text"]
                    action_desc = f"Typing '{text}' at ({x}, {y})"
                    
                    pyautogui.click(x, y)
                    await asyncio.sleep(0.1)
                    pyautogui.write(text, interval=0.03)
                    
                    if call.args.get("press_enter", False):
                        pyautogui.press("enter")
                        
                elif call.name == "scroll_document":
                    direction = call.args.get("direction", "down")
                    action_desc = f"Scrolling {direction}"
                    clicks = 5 if direction == "up" else -5
                    pyautogui.scroll(clicks)
                    
                else:
                    print(f"⚠️ Ignoring unsupported browser action: {call.name}")
                    result = "success_ignored" # Don't crash on unsupported browser actions
                    
            except Exception as e:
                print(f"❗️ Error executing {call.name}: {e}")
                result = f"error: {str(e)}"
                
            results.append((call.name, result))
            
        return "CONTINUE", results

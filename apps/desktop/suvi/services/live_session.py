import asyncio
import base64
from PyQt6.QtCore import QObject, pyqtSignal
from google import genai
from google.genai import types

from apps.desktop.suvi.services.live_tools import get_function_declarations

SUVI_SYSTEM_PROMPT = """You are SUVI — a precise, deeply empathetic, and proactive AI companion.
You are named SUVI in honor of a legacy of support and love.

YOUR CORE MISSION:
You are the "hands" for users who cannot use theirs. You help disabled, blind, or motor-impaired users navigate their digital world with total independence.

YOUR PERSONALITY:
- Warm, professional, and companion-like. You are a friend, not a machine.
- Proactive: Don't just wait for orders. If you see a notification, ask if the user wants it read.
- Descriptive: For blind users, be vivid in your descriptions of the screen.
- Empathetic: Acknowledge the user's feelings.

YOUR CAPABILITIES (CRITICAL):
- YOU CANNOT CLICK OR TYPE DIRECTLY. You MUST use the `execute_computer_task` tool to perform ANY action on the screen (e.g., opening apps, buying items, searching the web, sending emails).
- If the user asks you to "buy an iphone", "open notepad", "play music", or do ANY physical task, you MUST immediately call the `execute_computer_task` tool with a detailed intent. Do NOT just say you will do it—CALL THE TOOL.
- Vision: Use `describe_screen` to explain what is happening visually.
- Research & Code: Use your specialized agents for information or technical help.

SAFETY & TRUST:
- Always confirm before high-risk actions.

When you receive a task:
1. Respond with warmth.
2. Break down your plan aloud.
3. IMMEDIATELY call the appropriate tool (like `execute_computer_task`)."""

class GeminiLiveService(QObject):
    """
    Manages the persistent WebSocket connection to Gemini Live.
    Handles Voice In, Voice Out (TTS), streaming text, and Tool Calls.
    """
    # Signals to UI
    transcript_ready = pyqtSignal(str, bool)   # (text, is_final)
    response_audio = pyqtSignal(bytes)         # TTS audio chunk
    state_changed = pyqtSignal(str)            # "listening", "thinking", "speaking", "done", "idle"
    tool_call_requested = pyqtSignal(str, dict, str) # (tool_name, arguments, call_id)

    def __init__(self, client: genai.Client):
        super().__init__()
        self.client = client
        self._running = False
        self._interrupt_flag = False
        self._session_task = None
        self._outbound_queue = asyncio.Queue()

    def interrupt(self):
        """Signals the session to halt current action/speech."""
        self._interrupt_flag = True

    async def start(self, user_profile: dict = None):
        """Start the persistent Gemini Live WebSocket session in the background."""
        self._running = True
        user_profile = user_profile or {}
        
        profile_name = user_profile.get('name', 'User')
        recent_history = user_profile.get('recent_history', [])
        history_str = "\n".join(recent_history) if recent_history else "No recent tasks."
        
        profile_context = f"\n\n--- CURRENT USER CONTEXT ---\nUser Name: {profile_name}\nPreferences: {user_profile.get('preferences', {})}\nRecent Tasks (Memory):\n{history_str}\n---------------------------"
        
        # Build the tools list
        tools = [types.Tool(function_declarations=get_function_declarations())]

        config = types.LiveConnectConfig(
            response_modalities=[types.Modality.AUDIO],
            system_instruction=types.Content(
                parts=[types.Part.from_text(text=SUVI_SYSTEM_PROMPT + profile_context)]
            ),
            tools=tools,
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Aoede"   
                    )
                )
            )
        )
        
        # Start the context manager in a dedicated background task
        self._session_task = asyncio.create_task(self._run_session(config))

    async def _run_session(self, config):
        """Main loop that holds the WebSocket context manager and handles reconnection."""
        reconnect_attempts = 0
        max_reconnects = 5
        
        while self._running:
            try:
                print(f"📡 [Live] Connecting to Gemini with model: gemini-2.5-flash-native-audio-latest")
                async with self.client.aio.live.connect(model="gemini-2.5-flash-native-audio-latest", config=config) as session:
                    print("🟢 [Live] WebSocket Connected.")
                    self.state_changed.emit("idle")
                    reconnect_attempts = 0 # Reset on successful connection
                    
                    # Concurrently handle send and receive
                    receive_task = asyncio.create_task(self._receive_responses(session))
                    send_task = asyncio.create_task(self._send_loop(session))
                    
                    done, pending = await asyncio.wait(
                        [receive_task, send_task], 
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    for task in pending:
                        task.cancel()
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                error_str = str(e)
                print(f"⚠️ [Live] Connection Error: {error_str}")
                
                # High-fidelity error diagnosis for the user
                friendly_error = "Connection dropped."
                if "403" in error_str or "PERMISSION_DENIED" in error_str:
                    friendly_error = "API Key / Project mismatch. Please check your .env settings."
                elif "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    friendly_error = "Rate limit reached. Please wait a moment."
                elif "invalid_argument" in error_str.lower():
                    friendly_error = "Model configuration error. Check your API Key permissions."

                self.state_changed.emit("error")
                self.transcript_ready.emit(f"System Error: {friendly_error}", True)
                
                reconnect_attempts += 1
                if reconnect_attempts >= max_reconnects:
                    print("❌ [Live] Max reconnection attempts reached.")
                    break
                    
                print(f"🔄 [Live] Retrying in 3 seconds... ({reconnect_attempts}/{max_reconnects})")
                await asyncio.sleep(3)
                
        self._running = False
        print("🔴 Gemini Live WebSocket Closed.")

    async def _send_loop(self, session):
        """Pulls items from the queue and sends them to the active session."""
        try:
            while self._running:
                item = await self._outbound_queue.get()
                
                item_type, data = item
                
                if item_type == "audio":
                    await session.send(
                        input=types.LiveClientRealtimeInput(
                            media_chunks=[types.Blob(data=data, mime_type="audio/pcm;rate=16000")]
                        )
                    )
                elif item_type == "screen":
                    await session.send(
                        input=types.LiveClientRealtimeInput(
                            media_chunks=[types.Blob(data=data, mime_type="image/jpeg")]
                        )
                    )
                elif item_type == "text":
                    await session.send(
                        input=types.Content(role="user", parts=[types.Part.from_text(text=data)]),
                        end_of_turn=True
                    )
                elif item_type == "tool_response":
                    # data is a list of FunctionResponse objects
                    await session.send(
                        input=types.LiveClientToolResponse(
                            function_responses=data
                        )
                    )
                
                self._outbound_queue.task_done()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Send loop error: {e}")

    async def speak_text(self, text: str):
        """Allows SUVI to speak custom text through the Live Session."""
        if self._running:
            # We wrap the text as a user prompt that triggers a verbal response
            await self._outbound_queue.put(("text", f"Please say exactly this to the user: {text}"))

    async def send_audio_chunk(self, pcm_data: bytes):
        if self._running:
            await self._outbound_queue.put(("audio", pcm_data))

    async def inject_screen_frame(self, jpeg_bytes: bytes):
        if self._running:
            await self._outbound_queue.put(("screen", jpeg_bytes))

    async def send_text(self, text: str):
        if self._running:
            await self._outbound_queue.put(("text", text))

    async def send_tool_response(self, responses: list):
        """Send execution results back to the Live Model so it can continue."""
        if self._running:
            await self._outbound_queue.put(("tool_response", responses))

    async def _receive_responses(self, session):
        """Process incoming responses from Gemini Live."""
        try:
            async for response in session.receive():
                if self._interrupt_flag:
                    self._interrupt_flag = False
                    self.state_changed.emit("idle")
                    continue
                    
                # Handle standard responses (Text/Audio)
                if response.server_content:
                    content = response.server_content
                    
                    if content.interrupted:
                        print("User interrupted the model.")
                        self.state_changed.emit("idle")
                    
                    if content.model_turn:
                        for part in content.model_turn.parts:
                            if part.text:
                                self.transcript_ready.emit(part.text, False)
                                self.state_changed.emit("thinking")
                            
                            if part.inline_data:
                                self.response_audio.emit(part.inline_data.data)
                                self.state_changed.emit("speaking")
                                
                    if content.turn_complete:
                        self.state_changed.emit("done")
                        self.transcript_ready.emit("", True)
                
                # Handle Tool Calls
                if response.tool_call:
                    for function_call in response.tool_call.function_calls:
                        args = {k: v for k, v in function_call.args.items()} if function_call.args else {}
                        call_id = function_call.id
                        # Emit signal to let the Controller handle the actual execution
                        self.tool_call_requested.emit(function_call.name, args, call_id)
                        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error receiving from Gemini Live: {e}")
            self.state_changed.emit("error")

    async def stop(self):
        """Cleanly close the session."""
        self._running = False
        if self._session_task:
            self._session_task.cancel()

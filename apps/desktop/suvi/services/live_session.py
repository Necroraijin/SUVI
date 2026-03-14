import asyncio
import base64
from PyQt6.QtCore import QObject, pyqtSignal
from google import genai
from google.genai import types

from apps.desktop.suvi.services.live_tools import get_function_declarations

SUVI_SYSTEM_PROMPT = """You are SUVI, a voice-controlled desktop assistant.

STRICT FORMAT - Your response MUST follow this EXACT pattern for ALL computer tasks:

"<2-4 word confirmation> [CALL_TOOL: execute_computer_task] <exact user command>"

EXAMPLES - Copy these EXACTLY:
- User: "Open Chrome" → Say: "Opening Chrome. [CALL_TOOL: execute_computer_task] open chrome"
- User: "Open Notepad" → Say: "Opening Notepad. [CALL_TOOL: execute_computer_task] open notepad"
- User: "Write a story in notepad" → Say: "Writing in Notepad. [CALL_TOOL: execute_computer_task] write a story in notepad"
- User: "Search for cats on Chrome" → Say: "Searching. [CALL_TOOL: execute_computer_task] search for cats on chrome"
- User: "Type hello world" → Say: "Typing. [CALL_TOOL: execute_computer_task] type hello world in notepad"

MANDATORY RULES:
1. ALWAYS output the FULL user command after [CALL_TOOL: execute_computer_task]
2. If user says "write a story in notepad", output "write a story in notepad" - NOT "format" or anything else
3. NEVER add text BETWEEN your confirmation and [CALL_TOOL: execute_computer_task]
4. NEVER explain or describe what you're about to do - just do it
5. Never use markdown headers like **Thinking** or **Confirming**

WRONG OUTPUTS (WILL BE IGNORED):
- "Acknowledging request. [CALL_TOOL: execute_computer_task]" ← NO INTENT AFTER TRIGGER!
- "I'll open Notepad now. [CALL_TOOL: execute_computer_task] open" ← INTENT TOO SHORT!
- "**Analyzing** Opening Notepad. [CALL_TOOL: execute_computer_task] open notepad" ← NO MARKDOWN!

If you don't include the actual user command after the trigger, the task will NOT execute.
Your response must contain: <confirmation> + [CALL_TOOL: execute_computer_task] + <full user command>

For non-computer tasks: respond normally, no trigger needed."""

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
        if self._running:
            return
        self._running = True
        user_profile = user_profile or {}
        
        profile_name = user_profile.get('name', 'User')
        recent_history = user_profile.get('recent_history', [])
        history_str = "\n".join(recent_history) if recent_history else "No recent tasks."
        
        profile_context = f"\n\n--- CURRENT USER CONTEXT ---\nUser Name: {profile_name}\nPreferences: {user_profile.get('preferences', {})}\nRecent Tasks (Memory):\n{history_str}\n---------------------------"
        
        # REMOVE tools from Live config — handle tool calls via text channel/Orchestrator
        config = types.LiveConnectConfig(
            response_modalities=[types.Modality.AUDIO],
            system_instruction=types.Content(
                parts=[types.Part.from_text(text=SUVI_SYSTEM_PROMPT + profile_context)]
            ),
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
                    
                    # ═══════════════════════════════════════════════════════════
                    # CRITICAL: Send initial greeting immediately after connecting.
                    # Without this, both loops sit idle and the Gemini server
                    # closes the session due to inactivity within seconds.
                    # ═══════════════════════════════════════════════════════════
                    try:
                        await session.send_client_content(
                            turns=types.Content(
                                role="user",
                                parts=[types.Part.from_text(
                                    text="Hello SUVI, I just connected. Please greet me briefly and wait for my voice command."
                                )]
                            ),
                            turn_complete=True
                        )
                        print("📤 [Live] Initial greeting sent to keep session alive.")
                    except Exception as greet_err:
                        print(f"⚠️ [Live] Failed to send greeting: {greet_err}")
                    
                    # Concurrently handle send and receive
                    receive_task = asyncio.create_task(
                        self._receive_responses(session), name="receive_responses"
                    )
                    send_task = asyncio.create_task(
                        self._send_loop(session), name="send_loop"
                    )
                    
                    done, pending = await asyncio.wait(
                        [receive_task, send_task], 
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # Analyze WHY a task completed — important for debugging
                    should_reconnect = False
                    for task in done:
                        task_name = task.get_name()
                        try:
                            task.result()
                            print(f"⚠️ [Live] '{task_name}' exited normally (server may have closed session).")
                            should_reconnect = True
                        except asyncio.CancelledError:
                            print(f"⚠️ [Live] '{task_name}' was cancelled.")
                        except Exception as e:
                            print(f"⚠️ [Live] '{task_name}' failed with error: {type(e).__name__}: {e}")
                            should_reconnect = True
                    
                    for task in pending:
                        task_name = task.get_name()
                        print(f"⏹️ [Live] Cancelling pending task: '{task_name}'")
                        task.cancel()
                        try:
                            await task
                        except (asyncio.CancelledError, Exception):
                            pass
                    
                    # Only reconnect if we're still supposed to be running
                    if not self._running:
                        break
                    if not should_reconnect:
                        break
                        
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
                    
                wait_time = min(3 * reconnect_attempts, 15)
                print(f"🔄 [Live] Retrying in {wait_time} seconds... ({reconnect_attempts}/{max_reconnects})")
                await asyncio.sleep(wait_time)
                
        self._running = False
        print("🔴 Gemini Live WebSocket Closed.")

    async def _send_loop(self, session):
        """Pulls items from the queue and sends them to the active session.
        Sends keepalive pings to prevent server-side timeouts during long operations."""
        try:
            while self._running:
                try:
                    # Wait for data, but timeout after 25s to send keepalive
                    item = await asyncio.wait_for(self._outbound_queue.get(), timeout=25.0)
                except asyncio.TimeoutError:
                    # No data for 25s — send keepalive to prevent server timeout
                    try:
                        await session.send_client_content(
                            turns=types.Content(
                                role="user",
                                parts=[types.Part.from_text(text=".")]
                            ),
                            turn_complete=False  # Don't trigger a model response
                        )
                    except Exception as ping_err:
                        print(f"⚠️ [Live] Keepalive failed: {ping_err}")
                        break  # Connection is dead, exit loop
                    continue
                
                item_type, data = item
                
                try:
                    if item_type == "audio":
                        await session.send_realtime_input(
                            media=types.Blob(data=data, mime_type="audio/pcm;rate=16000")
                        )
                    elif item_type == "screen":
                        await session.send_realtime_input(
                            media=types.Blob(data=data, mime_type="image/jpeg")
                        )
                    elif item_type == "text":
                        await session.send_client_content(
                            turns=types.Content(
                                role="user",
                                parts=[types.Part.from_text(text=data)]
                            ),
                            turn_complete=True
                        )
                    elif item_type == "tool_response":
                        pass
                except Exception as inner_e:
                    print(f"Failed to send {item_type}: {inner_e}")
                    break  # If send fails, the connection is dead
                
                self._outbound_queue.task_done()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Send loop fatal error: {e}")

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
        # Tool responses disabled since we removed tools array
        pass

    async def _receive_responses(self, session):
        """Process incoming responses from Gemini Live.
        
        IMPORTANT: session.receive() yields messages for ONE turn only.
        After the model finishes responding, the generator ends.
        We must restart it in a loop to keep receiving across multiple turns.
        """
        total_msg_count = 0
        turn_count = 0
        print("👂 [Live] _receive_responses started, waiting for server messages...")
        try:
            while self._running:
                turn_count += 1
                turn_msg_count = 0
                
                try:
                    async for response in session.receive():
                        total_msg_count += 1
                        turn_msg_count += 1
                        
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
                                        print(f"📝 [Live] Model text: {part.text[:80]}...")
                                        self.transcript_ready.emit(part.text, False)
                                        self.state_changed.emit("thinking")
                                    
                                    if part.inline_data:
                                        self.response_audio.emit(part.inline_data.data)
                                        self.state_changed.emit("speaking")
                                        
                            if content.turn_complete:
                                self.state_changed.emit("done")
                                self.transcript_ready.emit("", True)
                        
                        # Handle Tool Calls (If any somehow sneak through)
                        if response.tool_call:
                            for function_call in response.tool_call.function_calls:
                                args = {k: v for k, v in function_call.args.items()} if function_call.args else {}
                                call_id = function_call.id
                                self.tool_call_requested.emit(function_call.name, args, call_id)
                    
                    # Generator ended normally — this is expected after each turn.
                    # Loop back to start a new receive() for the next turn.
                    print(f"🔄 [Live] Turn {turn_count} complete ({turn_msg_count} msgs). Listening for next turn...")
                    self.state_changed.emit("listening")
                    
                except asyncio.CancelledError:
                    raise  # Propagate to outer handler
                except Exception as e:
                    # If receive() itself throws, the session is truly dead
                    print(f"❌ [Live] receive() error on turn {turn_count}: {type(e).__name__}: {e}")
                    self.state_changed.emit("error")
                    break
                        
        except asyncio.CancelledError:
            print(f"⏹️ [Live] _receive_responses cancelled after {turn_count} turns, {total_msg_count} total messages.")
        except Exception as e:
            print(f"❌ [Live] Fatal error in receive loop: {type(e).__name__}: {e}")
            self.state_changed.emit("error")

    async def stop(self):
        """Cleanly close the session."""
        self._running = False
        if self._session_task:
            self._session_task.cancel()
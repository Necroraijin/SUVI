import asyncio
from PyQt6.QtCore import QObject, pyqtSignal
from google import genai
from google.genai import types

SUVI_SYSTEM_PROMPT = """You are SUVI, a desktop voice assistant.

For ANY computer task you MUST respond EXACTLY in this format:

[CALL_TOOL: execute_computer_task] ACTION_TO_PERFORM

Examples:
User: "open chrome"
Output: [CALL_TOOL: execute_computer_task] open chrome

User: "search for cute cats on youtube"
Output: [CALL_TOOL: execute_computer_task] search for cute cats on youtube

User: "open spotify and play the most recent song"
Output: [CALL_TOOL: execute_computer_task] open spotify and play the most recent song

CRITICAL RULES:
1. Output ONLY the trigger line.
2. DO NOT output the literal string "<user command>". Replace "ACTION_TO_PERFORM" with what the user actually wants.
3. NO explanation or markdown.
4. If the user is chatting normally (not asking you to do a computer task), respond normally with voice.
"""

class GeminiLiveService(QObject):
    transcript_ready = pyqtSignal(str, bool)
    response_audio = pyqtSignal(bytes)
    state_changed = pyqtSignal(str)
    tool_call_requested = pyqtSignal(str, dict, str)

    def __init__(self, client: genai.Client):
        super().__init__()
        self.client = client
        self._running = False
        self._interrupt_flag = False
        self._session_task = None
        self._outbound_queue = asyncio.Queue()

    def interrupt(self):
        self._interrupt_flag = True

    async def start(self, user_profile: dict = None):
        if self._running:
            return

        self._running = True
        user_profile = user_profile or {}

        profile_name = user_profile.get("name", "User")

        config = types.LiveConnectConfig(
            response_modalities=[types.Modality.AUDIO],
            system_instruction=types.Content(
                parts=[types.Part.from_text(text=SUVI_SYSTEM_PROMPT)]
            ),
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Aoede"
                    )
                )
            )
        )

        self._session_task = asyncio.create_task(self._run_session(config))

    async def _run_session(self, config):
        reconnect_attempts = 0

        while self._running:
            try:
                print("📡 [Live] Connecting to Gemini Live...")

                async with self.client.aio.live.connect(
                    model="gemini-2.5-flash-native-audio-latest",
                    config=config,
                ) as session:

                    print("🟢 [Live] WebSocket Connected.")
                    self.state_changed.emit("idle")
                    reconnect_attempts = 0

                    await session.send_client_content(
                        turns=types.Content(
                            role="user",
                            parts=[
                                types.Part.from_text(
                                    text="Hello SUVI. Please greet me briefly."
                                )
                            ],
                        ),
                        turn_complete=True,
                    )

                    receive_task = asyncio.create_task(
                        self._receive_responses(session),
                        name="receive_responses",
                    )

                    send_task = asyncio.create_task(
                        self._send_loop(session),
                        name="send_loop",
                    )

                    done, pending = await asyncio.wait(
                        [receive_task, send_task],
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                    for task in pending:
                        task.cancel()

            except Exception as e:
                print(f"⚠️ [Live] Connection Error: {e}")

                reconnect_attempts += 1
                if reconnect_attempts > 5:
                    print("❌ Max reconnect attempts reached.")
                    break

                wait_time = min(3 * reconnect_attempts, 15)
                print(f"🔄 Reconnecting in {wait_time}s...")
                await asyncio.sleep(wait_time)

        print("🔴 Gemini Live session closed.")

    async def _send_loop(self, session):
        try:
            while self._running:
                try:
                    item = await asyncio.wait_for(
                        self._outbound_queue.get(), timeout=25
                    )
                except asyncio.TimeoutError:
                    await session.send_client_content(
                        turns=types.Content(
                            role="user",
                            parts=[types.Part.from_text(text=".")],
                        ),
                        turn_complete=False,
                    )
                    continue

                item_type, data = item

                if item_type == "audio":
                    await session.send_realtime_input(
                        media=types.Blob(
                            data=data, mime_type="audio/pcm;rate=16000"
                        )
                    )
                elif item_type == "text":
                    await session.send_client_content(
                        turns=types.Content(
                            role="user",
                            parts=[types.Part.from_text(text=data)],
                        ),
                        turn_complete=True,
                    )

                self._outbound_queue.task_done()
        except Exception as e:
            print("Send loop error:", e)

    async def send_audio_chunk(self, pcm_data: bytes):
        if self._running:
            await self._outbound_queue.put(("audio", pcm_data))

    async def send_text(self, text: str):
        if self._running:
            await self._outbound_queue.put(("text", text))

    async def speak_text(self, text: str):
        if self._running:
            await self._outbound_queue.put(
                ("text", f"Please say exactly this: {text}")
            )

    async def _receive_responses(self, session):
        print("👂 Listening for model responses...")
        try:
            while self._running:
                async for response in session.receive():
                    if self._interrupt_flag:
                        self._interrupt_flag = False
                        self.state_changed.emit("idle")
                        continue

                    if response.server_content:
                        content = response.server_content

                        if content.model_turn:
                            for part in content.model_turn.parts:
                                if part.text:
                                    text = part.text.strip()
                                    print("📝 Model:", text)
                                    self.transcript_ready.emit(text, False)
                                    self.state_changed.emit("thinking")
                                if part.inline_data:
                                    self.response_audio.emit(
                                        part.inline_data.data
                                    )
                                    self.state_changed.emit("speaking")

                        if content.turn_complete:
                            self.transcript_ready.emit("", True)
                            self.state_changed.emit("done")
        except Exception as e:
            print("Receive loop error:", e)

    async def stop(self):
        self._running = False
        if self._session_task:
            self._session_task.cancel()

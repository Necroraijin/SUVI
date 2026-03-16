import asyncio
import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PyQt6.QtWidgets import QApplication
import qasync
import sounddevice as sd


root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from apps.desktop.suvi.workers.voice_worker import VoiceWorker
from apps.desktop.suvi.workers.wake_word_worker import WakeWordWorker
from apps.desktop.suvi.workers.replay_worker import ReplayWorker
from apps.desktop.suvi.services.live_session import GeminiLiveService
from apps.desktop.suvi.services.computer_use_service import ComputerUseService
from apps.desktop.suvi.ui.widget.chat_widget import ChatWidget

load_dotenv()

class IntegrationController:
    def __init__(self, ui_widget, voice_client, vision_client, orchestrator_client):
        self.ui = ui_widget
        self.live_service = GeminiLiveService(voice_client)
        self.computer_service = ComputerUseService(vision_client)
        self.orchestrator_client = orchestrator_client
        self.voice_worker = VoiceWorker()
        self.wake_word_worker = WakeWordWorker()
        self.replay_worker = ReplayWorker()
        
        self.speaker_stream = sd.RawOutputStream(
            samplerate=24000,
            channels=1,
            dtype='int16'
        )
        self.speaker_stream.start()
        self._setup_connections()

    def _setup_connections(self):
        # Wake Word
        self.wake_word_worker.wake_word_detected.connect(self.start_session)
        
        # Replay
        self.replay_worker.replay_saved.connect(lambda path: print(f"\n[SUVI Replay Ready] -> {path}"))

        # Audio input
        self.voice_worker.audio_chunk_captured.connect(self._on_mic_audio)
        self.voice_worker.amplitude_updated.connect(self._on_amplitude)
        
        # Live Session signals -> UI and Engine
        self.live_service.transcript_ready.connect(self._on_transcript)
        self.live_service.response_audio.connect(self._on_tts_audio)
        self.live_service.state_changed.connect(self._on_state)
        self.live_service.tool_call_requested.connect(self._on_tool_call)
        
        # UI signals -> Engine
        self.ui.interrupt_requested.connect(self._on_user_interrupt)

    def _on_user_interrupt(self):
        print("\n🛑 User pressed STOP button!")
        self.ui.update_state("idle")
        self.ui.update_transcript("Session stopped. Waiting for 'Hey SUVI'...")
        
        # Stop background tasks
        self.computer_service.interrupt()
        
        # Stop the microphone
        if self.voice_worker.isRunning():
            self.voice_worker.stop()
            
        # Close the WebSocket connection to save tokens and stop the agent loop
        asyncio.create_task(self.live_service.stop())

        # Start listening for the wake word again
        if not self.wake_word_worker.isRunning():
            self.wake_word_worker.start()

    def start_session(self):
        """Starts the active session (triggered by wake word)"""
        print("\n🟢 Wake word detected! Starting session...")
        
        # Stop wake word listener so they don't clash on the microphone
        if self.wake_word_worker.isRunning():
            self.wake_word_worker.stop()

        self.ui.update_state("listening")
        self.ui.update_transcript("How can I help you?")
        
        # Start mic
        if not self.voice_worker.isRunning():
            self.voice_worker.start()
            
        # Start WebSocket
        asyncio.create_task(self.live_service.start(user_profile={"name": "Sumit"}))

    def _on_mic_audio(self, pcm_chunk: bytes):
        asyncio.create_task(self.live_service.send_audio_chunk(pcm_chunk))

    def _on_amplitude(self, amp: float):
        # We could use this to animate a waveform later
        pass

    def _on_transcript(self, text: str, is_final: bool):
        if text.strip():
            self.ui.update_transcript(text)

    def _on_tts_audio(self, audio_chunk: bytes):
        self.speaker_stream.write(audio_chunk)

    def _on_state(self, state: str):
        self.ui.update_state(state)

    def _on_tool_call(self, tool_name: str, args: dict, call_id: str):
        self.ui.update_state("executing")
        
        if tool_name == "execute_computer_task":
            intent = args.get("intent", "")
            self.ui.update_transcript(f"Executing: {intent}")
            asyncio.create_task(self._execute_vision_loop(intent, call_id))
        else:
            self.ui.update_transcript(f"Using tool: {tool_name}")
            asyncio.create_task(self._handle_general_tool(tool_name, args, call_id))

    async def _execute_vision_loop(self, intent: str, call_id: str):
        # Start a new replay session
        self.replay_worker.set_session(call_id)
        
        # Connect the screenshot callback to the replay worker
        def on_screenshot(img_bytes):
            self.replay_worker.add_frame(img_bytes)

        result = await self.computer_service.execute_task(
            intent=intent,
            user_id="test_user",
            session_id="test_session",
            on_action=lambda d: self.ui.update_transcript(f"Action: {d}"),
            on_screenshot=on_screenshot
        )
        
        # Save the GIF in the background
        self.replay_worker.start()
        
        response = types.FunctionResponse(
            id=call_id,
            name="execute_computer_task",
            response={"status": "success" if result.get('success') else "failed", "summary": "Task executed on screen."}
        )
        await self.live_service.send_tool_response([response])

    async def _handle_general_tool(self, name: str, args: dict, call_id: str):
        await asyncio.sleep(1)
        response = types.FunctionResponse(
            id=call_id,
            name=name,
            response={"result": f"Simulated data for {name}"}
        )
        await self.live_service.send_tool_response([response])

    async def run(self):
        print("\n🚀 Starting Full SUVI System with UI...")
        self.ui.update_state("idle")
        self.ui.update_transcript("Waiting for wake word ('Hey SUVI')...")
        
        # Start only the wake word listener initially
        self.wake_word_worker.start()
        
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            self.wake_word_worker.stop()
            self.voice_worker.stop()
            await self.live_service.stop()
            self.speaker_stream.stop()

def main():
    # Setup PyQt Application for UI
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Initialize the Widget
    widget = ChatWidget()
    widget.show()

    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})

    controller = IntegrationController(widget, client, client, client)

    # Run Controller loop
    with loop:
        try:
            
            asyncio.ensure_future(controller.run())
            loop.run_forever()
        except KeyboardInterrupt:
            print("\nShutting down integration test...")

if __name__ == "__main__":
    main()

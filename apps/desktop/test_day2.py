import sys
import os
import asyncio
import qasync
from dotenv import load_dotenv
from google import genai

from PyQt6.QtCore import QCoreApplication
import sounddevice as sd


sys.path.append(os.path.dirname(__file__))

from suvi.workers.voice_worker import VoiceWorker
from suvi.services.live_session import GeminiLiveService
from suvi.services.computer_use_service import ComputerUseService


root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(root_dir, '.env'))

class TestController:
    def __init__(self, app, live_client, computer_client):
        self.app = app
        self.live_service = GeminiLiveService(live_client)
        self.computer_service = ComputerUseService(computer_client)
        self.voice_worker = VoiceWorker()
        
        
        self.speaker_stream = sd.RawOutputStream(
            samplerate=24000, 
            channels=1,
            dtype='int16'
        )
        self.speaker_stream.start()

        self._setup_connections()

    def _setup_connections(self):
        
        self.voice_worker.audio_chunk_captured.connect(self._on_mic_audio)

        
        self.live_service.transcript_ready.connect(self._on_transcript)
        self.live_service.response_audio.connect(self._on_tts_audio)
        self.live_service.state_changed.connect(self._on_state)
        
        
        self.live_service.tool_call_requested.connect(self._on_tool_call)

    def _on_mic_audio(self, pcm_chunk: bytes):
        asyncio.create_task(self.live_service.send_audio_chunk(pcm_chunk))

    def _on_transcript(self, text: str, is_final: bool):
        if text.strip():
            print(f"\rSUVI: {text}\033[K", end="\n" if is_final else "", flush=True)

    def _on_tts_audio(self, audio_chunk: bytes):
        self.speaker_stream.write(audio_chunk)

    def _on_state(self, state: str):
        if state == "listening":
            print("\n🟢 Listening...")

    def _on_tool_call(self, tool_name: str, args: dict, call_id: str):
        if tool_name == "execute_computer_task":
            intent = args.get("intent", "")
            print(f"\n⚡ Live AI requested computer execution: {intent}")
            
            
            asyncio.create_task(self._execute_and_respond(intent, call_id))
            
        elif tool_name == "stop_execution":
            print("\n🛑 Live AI requested execution stop.")
            self.computer_service.interrupt()
            
            
            from google.genai import types
            response = types.FunctionResponse(id=call_id, name=tool_name, response={"status": "halted"})
            asyncio.create_task(self.live_service.send_tool_response([response]))

    async def _execute_and_respond(self, intent: str, call_id: str):
        print("  [ACTION LOOP] Starting Vision loop...")
        
        def on_action(desc):
            print(f"    -> {desc}")
            
        result = await self.computer_service.execute_task(
            intent=intent,
            user_id="test",
            session_id="test",
            on_action=on_action
        )
        
        print(f"  [ACTION LOOP] Completed. Success: {result.get('success')}")
        
        
        from google.genai import types
        response = types.FunctionResponse(
            id=call_id,
            name="execute_computer_task", 
            response={"status": "success" if result.get('success') else "failed", "details": str(result.get('actions_taken', []))}
        )
        await self.live_service.send_tool_response([response])

    async def run(self):
        print("Starting FULL SUVI Test (Voice + Vision)...")
        print("Say something like: 'Can you click the Windows Start button?'")
        
        self.voice_worker.start()
        await self.live_service.start(user_profile={"name": "Sumit"})
        
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            self.voice_worker.stop()
            await self.live_service.stop()
            self.speaker_stream.stop()

async def main():
    app = QCoreApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "<your_key>":
        print("❌ ERROR: Please set your GEMINI_API_KEY in the .env file.")
        return

    print("✅ Initializing AI Studio Client for Voice...")
    live_client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})

    
    print("✅ Initializing AI Studio Client for Vision...")
    computer_client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})

    controller = TestController(app, live_client, computer_client)

    with loop:
        try:
            loop.run_until_complete(controller.run())
        except KeyboardInterrupt:
            print("\nShutting down...")

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import os
from google import genai
from google.genai import types
import sounddevice as sd

from PyQt6.QtWidgets import QApplication

from apps.desktop.suvi.ui.widget.chat_widget import ChatWidget
from apps.desktop.suvi.ui.login.login_window import LoginWindow
from apps.desktop.suvi.workers.voice_worker import VoiceWorker
from apps.desktop.suvi.workers.wake_word_worker import WakeWordWorker
from apps.desktop.suvi.workers.replay_worker import ReplayWorker
from apps.desktop.suvi.services.live_session import GeminiLiveService
from apps.desktop.suvi.services.computer_use_service import ComputerUseService
from apps.desktop.suvi.services.orchestrator_service import OrchestratorService
from apps.desktop.suvi.services.memory_service import MemoryService

class SUVIApplication:
    """
    The main controller for the SUVI Desktop Application.
    Manages the UI, background workers, and AI service connections.
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.ui = None
        self.login_window = None
        self.live_service = None
        self.computer_service = None
        self.orchestrator = None
        self.memory = MemoryService()
        self.user_persona = {}
        
        self.voice_worker = VoiceWorker()
        self.wake_word_worker = WakeWordWorker()
        self.replay_worker = ReplayWorker()
        
        # Audio output stream for TTS playback
        self.speaker_stream = sd.RawOutputStream(
            samplerate=24000,
            channels=1,
            dtype='int16'
        )

    def init_services(self, api_key: str, ui_widget):
        self.api_key = api_key
        print("✅ Initializing AI Services...")
        # Note: Using v1alpha for native-audio and computer-use preview access
        client = genai.Client(api_key=self.api_key, http_options={'api_version': 'v1alpha'})
        self.live_service = GeminiLiveService(client)
        self.computer_service = ComputerUseService(client, ui_widget=ui_widget)
        self.orchestrator = OrchestratorService(client)

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
        
        self.computer_service.interrupt()
        
        if self.voice_worker.isRunning():
            self.voice_worker.stop()
            
        asyncio.create_task(self.live_service.stop())

        if not self.wake_word_worker.isRunning():
            self.wake_word_worker.start()

    def start_session(self):
        """Starts the active session (triggered by wake word)"""
        print("\n🟢 Wake word detected! Starting session...")
        
        if self.wake_word_worker.isRunning():
            self.wake_word_worker.stop()

        self.ui.update_state("listening")
        self.ui.update_transcript("How can I help you?")
        
        if not self.voice_worker.isRunning():
            self.voice_worker.start()
            
        # Pass the user persona to provide context to the companion
        asyncio.create_task(self.live_service.start(user_profile=self.user_persona))

    def _on_mic_audio(self, pcm_chunk: bytes):
        asyncio.create_task(self.live_service.send_audio_chunk(pcm_chunk))

    def _on_amplitude(self, amp: float):
        pass

    def _on_transcript(self, text: str, is_final: bool):
        if text.strip():
            self.ui.update_transcript(text)

    def _on_tts_audio(self, audio_chunk: bytes):
        self.speaker_stream.write(audio_chunk)

    def _on_state(self, state: str):
        self.ui.update_state(state)

    def _on_tool_call(self, tool_name: str, args: dict, call_id: str):
        self.ui.update_state("thinking")
        
        if tool_name == "execute_computer_task":
            intent = args.get("intent", "")
            asyncio.create_task(self._execute_vision_loop(intent, call_id))
            
        elif tool_name == "coder_agent":
            prompt = args.get("prompt", "")
            lang = args.get("language")
            self.ui.update_transcript(f"Coding Agent: Working...")
            asyncio.create_task(self._run_coder_agent(prompt, lang, call_id))
            
        elif tool_name == "research_agent":
            query = args.get("query", "")
            self.ui.update_transcript(f"Research Agent: Searching...")
            asyncio.create_task(self._run_research_agent(query, call_id))
            
        elif tool_name == "describe_screen":
            self.ui.update_state("thinking")
            self.ui.update_transcript("Analyzing screen...")
            asyncio.create_task(self._run_describe_screen(call_id))
            
        elif tool_name == "stop_execution":
            self._on_user_interrupt()
            asyncio.create_task(self.live_service.send_tool_response([
                types.FunctionResponse(id=call_id, name=tool_name, response={"status": "stopped"})
            ]))

    async def _run_coder_agent(self, prompt: str, lang: str, call_id: str):
        result = await self.orchestrator.generate_coding_solution(prompt, lang)
        self.ui.update_state("speaking")
        self.ui.update_transcript(f"Solution ready.")
        await self.live_service.send_tool_response([
            types.FunctionResponse(id=call_id, name="coder_agent", response={"solution": result})
        ])

    async def _run_research_agent(self, query: str, call_id: str):
        result = await self.orchestrator.perform_research(query)
        self.ui.update_state("speaking")
        self.ui.update_transcript(f"Research complete.")
        await self.live_service.send_tool_response([
            types.FunctionResponse(id=call_id, name="research_agent", response={"findings": result})
        ])

    async def _run_describe_screen(self, call_id: str):
        description = await self.computer_service.describe_screen()
        self.ui.update_state("speaking")
        self.ui.update_transcript("Screen description ready.")
        await self.live_service.send_tool_response([
            types.FunctionResponse(id=call_id, name="describe_screen", response={"description": description})
        ])

    async def _execute_vision_loop(self, intent: str, call_id: str):
        # Accessibility Step: Use the Brain (Pro) to plan the task if it sounds complex
        self.ui.update_transcript("Planning task...")
        refined_intent = await self.orchestrator.plan_complex_task(intent)
        
        self.ui.update_state("executing")
        self.ui.update_transcript(f"Executing: {intent}")
        
        # Start a new replay session
        self.replay_worker.set_session(call_id)
        
        def on_screenshot(img_bytes):
            self.replay_worker.add_frame(img_bytes)

        result = await self.computer_service.execute_task(
            intent=refined_intent,
            user_id="suvi_user",
            session_id="suvi_session",
            on_action=lambda d: self.ui.update_transcript(f"Action: {d}"),
            on_screenshot=on_screenshot
        )
        
        # Save Memory to Firestore
        await self.memory.log_task_execution(
            user_id="suvi_user",
            session_id=call_id,
            intent=intent,
            actions=result.get("actions_taken", []),
            status="success" if result.get("success") else "failed"
        )
        
        # Save the GIF
        self.replay_worker.start()
        
        response = types.FunctionResponse(
            id=call_id,
            name="execute_computer_task",
            response={"status": "success" if result.get('success') else "failed", "summary": "Task executed on screen."}
        )
        await self.live_service.send_tool_response([response])

    async def _on_launch_requested(self, settings: dict):
        """Callback when user clicks 'Launch' in the login window."""
        # Show the main Widget first so we can pass it to services
        self.ui = ChatWidget()
        self.ui.show()
        
        self.init_services(settings["GEMINI_API_KEY"], self.ui)
        
        # Fetch User Persona
        print("👤 Fetching User Persona...")
        self.user_persona = await self.memory.get_user_persona("suvi_user")
        if not self.user_persona:
            self.user_persona = {"name": "User", "role": "Friend"}
            
        # Setup real-time connections
        self._setup_connections()
        
        self.speaker_stream.start()
        self.ui.update_state("idle")
        self.ui.update_transcript("Waiting for 'Hey SUVI'...")
        
        self.wake_word_worker.start()

    async def start(self):
        print("Starting SUVI Desktop Application...")
        
        # Show Login/Settings Window First
        self.login_window = LoginWindow()
        self.login_window.ready_to_start.connect(lambda s: asyncio.ensure_future(self._on_launch_requested(s)))
        self.login_window.show()
        
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            self.wake_word_worker.stop()
            self.voice_worker.stop()
            if self.live_service:
                await self.live_service.stop()
            self.speaker_stream.stop()

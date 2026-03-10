import asyncio
import os
import sys
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
from apps.desktop.suvi.services.gateway_service import GatewayService

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
        self.gateway = GatewayService()
        self.memory = MemoryService()
        self.user_persona = {}
        self.user_id = None
        self._expecting_voice_confirmation = False
        self._current_state = "idle"
        
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
        print(f"✅ Initializing AI Services with API Key: {api_key[:10]}...")
        try:
            client = genai.Client(api_key=self.api_key, http_options={'api_version': 'v1alpha'})
            self.live_service = GeminiLiveService(client)
            self.computer_service = ComputerUseService(client, ui_widget=ui_widget)
            self.orchestrator = OrchestratorService(client)
        except Exception as e:
            print(f"❌ Critical Error initializing AI services: {e}")

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
        
        # Computer Use signals
        if self.computer_service:
            self.computer_service.voice_confirmation_requested.connect(self._on_voice_confirmation_requested)
        
        # UI signals -> Engine
        self.ui.interrupt_requested.connect(self._on_user_interrupt)

    def _on_voice_confirmation_requested(self, title: str, message: str):
        self.ui.update_state("speaking")
        self.ui.update_transcript(f"SUVI: {message}")
        asyncio.create_task(self.live_service.speak_text(message))
        self._expecting_voice_confirmation = True

    def _on_user_interrupt(self):
        print("\n🛑 User pressed STOP button!")
        self.ui.update_state("idle")
        self.ui.update_transcript("Session stopped. Waiting for 'Hey SUVI'...")
        
        if self.computer_service:
            self.computer_service.interrupt()
        
        if self.voice_worker.isRunning():
            self.voice_worker.stop()
            
        if self.live_service:
            asyncio.create_task(self.live_service.stop())

        if not self.wake_word_worker.isRunning():
            self.wake_word_worker.start()

    def start_session(self):
        print("\n🟢 Wake word detected! Starting session...")
        
        if self.wake_word_worker.isRunning():
            self.wake_word_worker.stop()

        self.ui.update_state("listening")
        self.ui.update_transcript("How can I help you?")
        
        if not self.voice_worker.isRunning():
            self.voice_worker.start()
            
        if self.live_service:
            asyncio.create_task(self.live_service.start(user_profile=self.user_persona))

    def _on_mic_audio(self, pcm_chunk: bytes):
        # Prevent self-interruption (Echo loop): Do not send mic data if SUVI is speaking
        if self.live_service and self._current_state != "speaking":
            asyncio.create_task(self.live_service.send_audio_chunk(pcm_chunk))

    def _on_amplitude(self, amp: float):
        pass

    def _on_transcript(self, text: str, is_final: bool):
        if text.strip():
            self.ui.update_transcript(text)
            
            # Pipe voice confirmation back to ComputerUse if active
            if is_final and self._expecting_voice_confirmation and self.computer_service:
                print(f"🎙️ Captured voice confirmation answer: {text}")
                self.computer_service.set_voice_response(text)
                self._expecting_voice_confirmation = False

    def _on_tts_audio(self, audio_chunk: bytes):
        try:
            self.speaker_stream.write(audio_chunk)
        except Exception as e:
            print(f"Speaker Output Error: {e}")

    def _on_state(self, state: str):
        self._current_state = state
        self.ui.update_state(state)

    def _on_tool_call(self, tool_name: str, args: dict, call_id: str):
        self.ui.update_state("thinking")
        
        if tool_name == "execute_computer_task":
            intent = args.get("intent", "")
            asyncio.create_task(self._execute_vision_loop(intent, call_id))
            
        elif tool_name == "coder_agent":
            prompt = args.get("prompt", "")
            lang = args.get("language")
            asyncio.create_task(self._run_coder_agent(prompt, lang, call_id))
            
        elif tool_name == "research_agent":
            query = args.get("query", "")
            asyncio.create_task(self._run_research_agent(query, call_id))
            
        elif tool_name == "describe_screen":
            asyncio.create_task(self._run_describe_screen(call_id))
            
        elif tool_name == "stop_execution":
            self._on_user_interrupt()
            if self.live_service:
                asyncio.create_task(self.live_service.send_tool_response([
                    types.FunctionResponse(id=call_id, name=tool_name, response={"status": "stopped"})
                ]))

    async def _run_coder_agent(self, prompt: str, lang: str, call_id: str):
        if not self.orchestrator or not self.live_service: return
        result = await self.orchestrator.generate_coding_solution(prompt, lang)
        await self.live_service.send_tool_response([
            types.FunctionResponse(id=call_id, name="coder_agent", response={"solution": result})
        ])

    async def _run_research_agent(self, query: str, call_id: str):
        if not self.orchestrator or not self.live_service: return
        result = await self.orchestrator.perform_research(query)
        await self.live_service.send_tool_response([
            types.FunctionResponse(id=call_id, name="research_agent", response={"findings": result})
        ])

    async def _run_describe_screen(self, call_id: str):
        if not self.computer_service or not self.live_service: return
        description = await self.computer_service.describe_screen()
        await self.live_service.send_tool_response([
            types.FunctionResponse(id=call_id, name="describe_screen", response={"description": description})
        ])

    async def _execute_vision_loop(self, intent: str, call_id: str):
        if not self.computer_service or not self.live_service: return
        self.ui.update_transcript("Planning task...")
        
        # Query via Gateway if available, otherwise local orchestrator
        if self.gateway.ws:
            refined_intent = await self.gateway.query_orchestrator("plan", intent)
        elif self.orchestrator:
            refined_intent = await self.orchestrator.plan_complex_task(intent)
        else:
            refined_intent = intent
        
        self.ui.update_state("executing")
        self.ui.update_transcript(f"Executing: {intent}")
        
        self.replay_worker.set_session(call_id)
        
        def on_screenshot(img_bytes):
            self.replay_worker.add_frame(img_bytes)

        result = await self.computer_service.execute_task(
            intent=refined_intent,
            user_id=self.user_id,
            session_id=call_id,
            on_action=lambda d: self.ui.update_transcript(f"Action: {d}"),
            on_screenshot=on_screenshot
        )
        
        await self.memory.log_task_execution(
            user_id=self.user_id,
            session_id=call_id,
            intent=intent,
            actions=result.get("actions_taken", []),
            status="success" if result.get("success") else "failed"
        )
        
        self.replay_worker.start()
        
        response = types.FunctionResponse(
            id=call_id,
            name="execute_computer_task",
            response={"status": "success" if result.get('success') else "failed", "summary": "Task executed on screen."}
        )
        await self.live_service.send_tool_response([response])

    def _save_settings_to_env(self, settings: dict):
        """Persist settings to .env file for auto-login."""
        try:
            # Read existing .env to preserve comments and other vars
            env_lines = []
            if os.path.exists(".env"):
                with open(".env", "r") as f:
                    env_lines = f.readlines()

            # Update or add settings
            env_vars = {
                "GEMINI_API_KEY": settings.get("GEMINI_API_KEY", ""),
                "GCP_PROJECT_ID": settings.get("GCP_PROJECT_ID", ""),
                "USER_ID": settings.get("USER_ID", ""),
                "ID_TOKEN": settings.get("ID_TOKEN", "")
            }

            with open(".env", "w") as f:
                for line in env_lines:
                    key = line.split("=")[0].strip() if "=" in line else ""
                    if key in env_vars:
                        f.write(f"{key}={env_vars[key]}\n")
                        del env_vars[key] # Remove from dict so we don't duplicate
                    else:
                        f.write(line)
                
                # Write any remaining new vars at the bottom
                for key, val in env_vars.items():
                    if val:
                        f.write(f"{key}={val}\n")
                        
            print("💾 Settings saved to .env")
        except Exception as e:
            print(f"⚠️ Failed to save settings to .env: {e}")

    async def _on_launch_requested(self, settings: dict):
        """Callback when user clicks 'Launch' in the login window."""
        print("🚀 [App] Launch requested with production settings.")
        self.user_id = settings.get("USER_ID")
        
        # Save settings for next time
        self._save_settings_to_env(settings)
        
        self.ui = ChatWidget()
        self.ui.show()
        self.ui.update_transcript("SUVI Initializing...")
        
        # 1. Initialize core AI services
        self.init_services(settings["GEMINI_API_KEY"], self.ui)
        
        # 2. Setup connections
        self._setup_connections()

        # 3. Connect to Gateway with real token
        token = settings.get("ID_TOKEN")
        if token:
            print(f"🔗 [App] Connecting to Gateway with token: {token[:15]}...")
            asyncio.create_task(self.gateway.connect(
                session_id=f"session_{self.user_id}",
                token=token
            ))
        
        # 4. Fetch User Persona & Memory
        self.user_persona = await self.memory.get_user_persona(self.user_id)
        if not self.user_persona:
            self.user_persona = {"name": settings.get("USER_NAME", "User"), "role": "Friend"}
            
        recent_memory = await self.memory.get_recent_memory(self.user_id)
        self.user_persona["recent_history"] = recent_memory
            
        self.speaker_stream.start()
        self.ui.update_state("idle")
        self.ui.update_transcript("Waiting for 'Hey SUVI'...")
        self.wake_word_worker.start()

    async def start(self):
        print("Starting SUVI Desktop Application...")
        self.login_window = LoginWindow()
        self.login_window.ready_to_start.connect(lambda s: asyncio.ensure_future(self._on_launch_requested(s)))
        
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

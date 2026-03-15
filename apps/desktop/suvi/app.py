import asyncio
import os
import sys
from google import genai
from google.genai import types
import sounddevice as sd

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QBrush
from PyQt6.QtCore import Qt

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
from apps.desktop.suvi.services.environment_scanner import EnvironmentScanner

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
        self.env_scanner = EnvironmentScanner()
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
        project_id = os.getenv("GCP_PROJECT_ID")
        print(f"✅ Initializing AI Services (Project: {project_id})")
        
        try:
            # Scan the user's system environment (installed apps, capabilities)
            env_data = self.env_scanner.scan()
            print(f"🌍 Environment: {env_data.get('os')}, {len(env_data.get('installed_apps', []))} apps, "
                  f"browser: {env_data.get('default_browser')}")
            
            client = genai.Client(api_key=self.api_key)
            
            self.live_service = GeminiLiveService(client)
            self.computer_service = ComputerUseService(client, ui_widget=ui_widget, env_scanner=self.env_scanner)
            self.orchestrator = OrchestratorService(client)
        except Exception as e:
            print(f"❌ Critical Error initializing AI services: {e}")
            self.ui.update_transcript(f"System Error: Failed to initialize AI services. {e}")

    def _setup_connections(self):
        # Wake Word
        self.wake_word_worker.wake_word_detected.connect(self.start_session)
        
        # Replay
        self.replay_worker.replay_saved.connect(lambda path: print(f"\n[SUVI Replay Ready] -> {path}"))

        # Audio input
        self.voice_worker.audio_chunk_captured.connect(self._on_mic_audio)
        self.voice_worker.amplitude_updated.connect(self._on_amplitude)
        
        # Live Session signals -> UI and Engine
        if self.live_service:
            self.live_service.transcript_ready.connect(self._on_transcript)
            self.live_service.response_audio.connect(self._on_tts_audio)
            self.live_service.state_changed.connect(self._on_state)
            self.live_service.tool_call_requested.connect(self._on_tool_call)
        
        # Computer Use signals
        if self.computer_service:
            self.computer_service.voice_confirmation_requested.connect(self._on_voice_confirmation_requested)
        
        # UI signals -> Engine
        self.ui.interrupt_requested.connect(self._on_user_interrupt)
        self.ui.session_toggle_requested.connect(self._on_session_toggle)
        self.ui.text_submitted.connect(self._on_text_submitted)

    def _on_session_toggle(self, start: bool):
        if start:
            self.start_session()
        else:
            self._on_user_interrupt()

    def _on_text_submitted(self, text: str):
        self.ui.update_transcript(f"You: {text}")
        if self.live_service:
            asyncio.create_task(self.live_service.send_text(text))

    def _on_voice_confirmation_requested(self, title: str, message: str):
        self.ui.update_state("speaking")
        self.ui.update_transcript(f"SUVI: {message}")
        asyncio.create_task(self.live_service.speak_text(message))
        self._expecting_voice_confirmation = True

    def _setup_system_tray(self):
        """Setup system tray icon with menu"""
        # Create tray icon
        self.tray_icon = QSystemTrayIcon()

        # Create a simple icon (purple circle for SUVI)
        icon = QIcon()
        # Use a simple colored icon
        from PyQt6.QtGui import QPixmap, QPainter, QColor, QBrush
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QBrush(QColor("#BB86FC")))
        painter.drawEllipse(4, 4, 24, 24)
        painter.end()
        icon.addPixmap(pixmap)

        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("SUVI - Voice Assistant")

        # Create context menu
        menu = QMenu()

        show_panel = QAction("📋 Open SUVI Panel")
        show_panel.triggered.connect(self.show_panel)
        menu.addAction(show_panel)

        toggle_overlay = QAction("🎙️ Toggle Voice Overlay")
        toggle_overlay.triggered.connect(self._toggle_overlay)
        menu.addAction(toggle_overlay)

        menu.addSeparator()

        quit_action = QAction("❌ Quit SUVI")
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)

        # Double-click to show panel
        self.tray_icon.activated.connect(self._on_tray_double_click)

        self.tray_icon.show()
        print("✅ System tray initialized")

    def _on_tray_double_click(self, reason):
        """Handle tray icon double-click"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_panel()

    def _toggle_overlay(self):
        """Toggle the voice overlay visibility"""
        if self.ui.isVisible():
            self.ui.hide()
        else:
            self.ui.show()

    def _on_user_interrupt(self):
        print("\n🛑 User pressed STOP button!")
        self.ui.update_state("idle")
        self.ui.update_transcript("Session stopped. Say 'Hey SUVI' or click Start...")

        if self.computer_service:
            self.computer_service.interrupt()

        if self.voice_worker.isRunning():
            self.voice_worker.stop()

    def show_panel(self):
        """Show the SUVI Panel"""
        if self.login_window:
            self.login_window.show_panel()

    def hide_panel(self):
        """Hide the SUVI Panel"""
        if self.login_window:
            self.login_window.hide_panel()

    def toggle_panel(self):
        """Toggle the SUVI Panel"""
        if self.login_window:
            self.login_window.toggle_panel()
            
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

            # Guard: don't re-trigger while a task is already running
            if getattr(self, '_is_executing', False):
                return

            # ── Special commands for SUVI Panel ──
            text_lower = text.lower()
            # Check for panel commands
            if any(phrase in text_lower for phrase in ["open suvi panel", "show panel", "show suvi settings", "open settings"]):
                print("🖥️ Opening SUVI Panel...")
                self.show_panel()
                return

            if any(phrase in text_lower for phrase in ["close panel", "hide panel", "close suvi", "minimize panel"]):
                print("🖥️ Hiding SUVI Panel...")
                self.hide_panel()
                return

            import re
            
            # ══════════════════════════════════════════════════════════
            # INTENT DETECTION — extract WHAT the user wants done
            # The native audio model outputs "thinking" text with headers
            # like **Confirming Action: YouTube Playback** and phrases
            # like "the user intends to open Chrome"
            # ══════════════════════════════════════════════════════════
            trigger_found = False
            intent = ""
            # ── Method 1: Exact trigger text (case-insensitive) ──────
            # We strictly rely on the [CALL_TOOL: execute_computer_task] syntax
            # to prevent hallucinating intents from internal model thought headers.

            # First, strip markdown headers like **Thinking** etc before processing
            text_clean = re.sub(r'\*+[^*]+\*+', '', text)  # Remove **markdown headers**

            trigger_pattern = re.search(r'\[call_tool\s*:\s*execute_computer_task\]', text_clean, re.IGNORECASE)
            if trigger_pattern:
                trigger_found = True
                trigger_start = trigger_pattern.start()
                trigger_end = trigger_pattern.end()
                after = text_clean[trigger_end:].strip()
                before = text_clean[:trigger_start].strip()

                # Try to extract intent from AFTER the trigger first
                intent = ""
                after_clean = re.sub(r'^[`\s:.\-"\'>]+', '', after).strip()

                if after_clean and len(after_clean) >= 3:
                    # Text after trigger - take first sentence/phrase
                    intent = re.split(r'[.!]', after_clean)[0].strip()

                # If no intent after trigger, try BEFORE the trigger (the actual command)
                if not intent or len(intent) < 3:
                    # Look for verb + object pattern in the text BEFORE trigger
                    full_text = (before + " " + after).lower()
                    full_text = re.sub(r'\*+', '', full_text)  # Remove markdown
                    verb_match = re.search(
                        r'\b(open|launch|start|play|search for|search|close|navigate|go to|browse to|browse|type|click|create|delete|run|write|read|save|delete)\s+([a-z][a-z0-9 ]{2,50})',
                        full_text
                    )
                    if verb_match:
                        intent = f"{verb_match.group(1)} {verb_match.group(2)}".strip()
                        intent = re.split(r'[.,!;]', intent)[0].strip()

                # Clean up intent - remove trailing quotes, punctuation, backticks
                if intent:
                    intent = re.sub(r'["\'\`]+$', '', intent).strip()  # Remove trailing quotes/backticks
                    intent = re.sub(r'^["\'\`]+', '', intent).strip()  # Remove leading quotes

                # Last resort: look for quoted text anywhere
                if not intent or len(intent) < 3:
                    quoted = re.findall(r'["\u201c]([^"\u201d]{3,50})["\u201d]', text_clean, re.IGNORECASE)
                    if quoted:
                        intent = quoted[0]

                # ULTIMATE FALLBACK: Look for common command patterns anywhere in original text
                if not intent or len(intent) < 5:
                    # Find any complete command pattern
                    command_patterns = [
                        r'\b(write\s+(?:a\s+)?(?:story|note|message|text|email|letter|code|function|list|content)\s+(?:in|on|using|with)\s+\w+)',
                        r'\b(open|launch|start|play|search\s+for|search|close|navigate|go\s+to|browse|type|click|create|delete|run|read|save)\s+[a-z][a-z0-9\s]{2,40}',
                    ]
                    for pattern in command_patterns:
                        match = re.search(pattern, text_clean.lower())
                        if match:
                            intent = match.group(0).strip()
                            break

                clean_text = re.sub(r'\[call_tool\s*:\s*execute_computer_task\]', '', text_clean, flags=re.IGNORECASE).strip()
                self.ui.update_transcript(clean_text)
                print(f"✅ Method 1 (exact trigger) matched.")
                print(f"   📝 Text after trigger: '{after[:80] if after else '(empty)'}'")
                print(f"   📝 Text before trigger: '{before[:80] if before else '(empty)'}'")
                print(f"   📝 Final intent: '{intent}'")
            
            # ── Method 2: "user intends to" phrase detection ─────────
            if not trigger_found:
                body_lower = re.sub(r'\*+', '', text.lower())
                intent_match = re.search(
                    r'(?:user(?:\'s)?\s+(?:intends?|wants?|request|intent)\s+(?:to|is to|is)\s+)'
                    r'((?:open|launch|start|play|search|close|navigate|go to|browse|type|click|create|delete|run)\b.+?)(?:\.|,|\s+(?:it\'s|this|which|i\'|using|via|through|based))',
                    body_lower
                )
                if intent_match:
                    trigger_found = True
                    intent = intent_match.group(1).strip()
                    intent = re.split(r'[.,!;]', intent)[0].strip()
                    print(f"✅ Method 2 (user-intent phrase) matched. Intent: '{intent}'")
            
            if trigger_found and intent and len(intent) > 3:
                # Deduplication: don't trigger the same intent twice in a row
                if not hasattr(self, '_last_triggered_intent'):
                    self._last_triggered_intent = ""
                    
                if intent.lower() != self._last_triggered_intent.lower():
                    self._last_triggered_intent = intent
                    self._is_executing = True
                    print(f"🛠️ Tool Trigger Detected! Intent: '{intent}'")
                    call_id = f"text_trigger_{os.urandom(4).hex()}"
                    asyncio.create_task(self._execute_vision_loop(intent, call_id))
                else:
                    print(f"⏭️ Skipping duplicate trigger: '{intent}' (already executing)")
            elif trigger_found and not intent:
                print(f"⚠️ Trigger detected but no intent extracted from: '{text[:100]}...'")

    def _on_tts_audio(self, audio_chunk: bytes):
        try:
            self.speaker_stream.write(audio_chunk)
        except Exception as e:
            print(f"Speaker Output Error: {e}")

    def _on_state(self, state: str):
        self._current_state = state
        self.ui.update_state(state)

    def _on_tool_call(self, tool_name: str, args: dict, call_id: str):
        # Note: Tool calling via JSON is disabled in the Live Config currently, 
        # so this is a fallback in case Google enables it again.
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
        
        # Tool responses are disabled, so we speak it instead
        await self.live_service.speak_text(result)

    async def _run_research_agent(self, query: str, call_id: str):
        if not self.orchestrator or not self.live_service: return
        result = await self.orchestrator.perform_research(query)
        await self.live_service.speak_text(result)

    async def _run_describe_screen(self, call_id: str):
        if not self.computer_service or not self.live_service: return
        description = await self.computer_service.describe_screen()
        await self.live_service.speak_text(description)

    async def _execute_vision_loop(self, intent: str, call_id: str):
        if not self.computer_service: return
        
        try:
            self.ui.update_transcript("Planning task...")
            print(f"\n🎯 [VisionLoop] Starting with intent: '{intent}'")
            
            # Step 1: Plan the task — use gateway only if TRULY connected
            # Get environment context first so both gateway and local orchestrator can use it
            env_context = self.env_scanner.get_context_for_ai() if self.env_scanner else ""
            refined_intent = intent  # default fallback
            try:
                if self.gateway.is_connected:
                    print("  📡 Routing through Gateway...")
                    refined_intent = await self.gateway.query_orchestrator("plan", intent, env_context)
                    # If gateway returned an error, fall through to local orchestrator
                    if refined_intent.startswith("Error:"):
                        print(f"  ⚠️ Gateway failed: {refined_intent}. Falling back to local.")
                        refined_intent = intent
                elif self.orchestrator:
                    print("  🧠 Using local orchestrator...")
                    refined_intent = await self.orchestrator.plan_complex_task(intent, env_context)
                else:
                    print("  📝 Using raw intent (no orchestrator available).")
            except Exception as plan_err:
                print(f"  ⚠️ Planning failed: {plan_err}. Using raw intent.")
                refined_intent = intent
                
            # If we successfully planned it, gently wrap it so the execution agent
            # knows to blindly follow the steps, rather than just chat about it.
            if refined_intent != intent:
                refined_intent = f"Please blindly execute the following step-by-step plan to achieve this goal ('{intent}'). Do NOT describe the steps, just use tools to do them:\n\n{refined_intent}"
            
            # Step 2: Execute the computer use vision loop
            self.ui.update_state("executing")
            self.ui.update_transcript(f"Executing: {intent}")
            
            self.replay_worker.set_session(call_id)
            
            def on_screenshot(img_bytes):
                self.replay_worker.add_frame(img_bytes)

            print(f"  🚀 Calling ComputerUseService.execute_task()...")
            result = await self.computer_service.execute_task(
                intent=refined_intent,
                user_id=self.user_id,
                session_id=call_id,
                on_action=lambda d: self.ui.update_transcript(f"Action: {d}"),
                on_screenshot=on_screenshot
            )
            
            # Step 3: Log to memory (non-critical, don't let it break the flow)
            try:
                await self.memory.log_task_execution(
                    user_id=self.user_id,
                    session_id=call_id,
                    intent=intent,
                    actions=result.get("actions_taken", []),
                    status="success" if result.get("success") else "failed"
                )
            except Exception as mem_err:
                print(f"  ⚠️ Memory logging failed (non-critical): {mem_err}")
            
            # Step 4: Save replay (non-critical)
            try:
                if not self.replay_worker.isRunning():
                    self.replay_worker.start()
            except Exception as replay_err:
                print(f"  ⚠️ Replay save failed (non-critical): {replay_err}")
            
            # Step 5: Inform the user via speech
            success = result.get('success', False)
            reason = result.get('reason', '')
            actions_count = len(result.get('actions_taken', []))
            
            if success:
                status_msg = f"Done. Completed {actions_count} actions successfully."
            elif reason == "user_interrupted":
                status_msg = "Task stopped as you requested."
            else:
                status_msg = f"I couldn't finish the task. Reason: {reason}"
            
            print(f"  ✅ [VisionLoop] Finished: {status_msg}")
            self.ui.update_transcript(status_msg)
            self.ui.update_state("idle")
            self._is_executing = False
            self._last_triggered_intent = ""  # Allow same intent to be re-triggered
            
            # Only speak if the live service is still running
            if self.live_service and self.live_service._running:
                await self.live_service.speak_text(status_msg)
            
        except Exception as e:
            error_msg = f"Task execution error: {type(e).__name__}: {e}"
            print(f"  ❌ [VisionLoop] FATAL: {error_msg}")
            import traceback
            traceback.print_exc()
            self.ui.update_transcript(f"Error: {e}")
            self.ui.update_state("error")
            self._is_executing = False
            self._last_triggered_intent = ""

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

        # Setup system tray
        self._setup_system_tray()

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

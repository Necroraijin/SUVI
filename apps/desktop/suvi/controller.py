import sys
from PyQt6.QtCore import QObject
from apps.desktop.suvi.ui.action_ring.ring_window import RingWindow
from apps.desktop.suvi.ui.tray import SuviTray
from apps.desktop.suvi.ui.notifications import MicroToast, ResultCard, ConfirmDialog
from apps.desktop.suvi.workers import WakeWordWorker, VoiceWorker
from apps.desktop.suvi.services.live_session import LiveSession
from apps.desktop.suvi.services.gateway_client import GatewayClient
from apps.desktop.suvi.executor import ActionExecutor, KillSwitch
from apps.desktop.suvi.ui.action_ring.ring_state import RingState

class AppController(QObject):
    """Master controller that wires the UI, asyncio loop, and background services together."""
    
    def __init__(self, app, loop):
        super().__init__()
        self.app = app
        self.loop = loop
        
        # 1. Initialize UI Components
        self.ring_window = RingWindow()
        self.toast = MicroToast(parent_ring=self.ring_window)
        self.result_card = ResultCard(parent_ring=self.ring_window)
        self.confirm_dialog = ConfirmDialog()
        self.tray = SuviTray(ring_window=self.ring_window, app_controller=self)
        
        # 2. Initialize Services & Gateway
        self.gateway = GatewayClient()
        self.live_session = LiveSession(self.gateway)
        
        # 3. Initialize Background Workers
        self.wake_word_worker = WakeWordWorker()
        self.voice_worker = VoiceWorker()
        
        # 4. Initialize Action Executor
        self.action_executor = ActionExecutor()

        # 5. --- THE GRAND WIRING ---
        
        # Wake Word -> Start Listening
        self.wake_word_worker.wake_word_detected.connect(self._start_listening)
        
        # Mic -> AI Session
        self.voice_worker.audio_chunk_ready.connect(
            lambda chunk: asyncio.run_coroutine_threadsafe(
                self.live_session.send_audio_chunk(chunk), self.loop
            )
        )
        
        # Mic Amplitude -> UI Pulse
        self.voice_worker.amplitude_changed.connect(
            lambda amp: setattr(self.ring_window.vs, 'orb_glow', amp) or self.ring_window.update()
        )
        
        # AI Session -> UI States
        self.live_session.state_changed.connect(self.ring_window.set_state)
        self.live_session.error_occurred.connect(
            lambda msg: self.toast.show_status(f"AI Error: {msg}", duration_ms=5000)
        )
        
        # AI Session -> Executor (Tool Calls)
        self.live_session.tool_call_received.connect(
            lambda call: asyncio.run_coroutine_threadsafe(
                self.action_executor.execute_tool_call(call), self.loop
            )
        )
        
        # Executor -> UI (Permissions)
        self.action_executor.permission_required.connect(
            lambda tool, desc: self.confirm_dialog.prompt_user(desc)
        )
        self.confirm_dialog.decision_made.connect(self.action_executor.handle_user_decision)
        
        # Executor -> UI Notifications
        self.action_executor.action_started.connect(
            lambda msg: self.toast.show_status(msg, duration_ms=2000)
        )
        self.action_executor.action_completed.connect(self.result_card.show_result)
        self.action_executor.action_failed.connect(
            lambda msg: self.toast.show_status(f"Action Failed: {msg}", duration_ms=4000)
        )

        # Start Workers
        self.wake_word_worker.start()

    def start(self):
        """Brings the application online."""
        self.ring_window.show()
        self.tray.show()
        print("[System] SUVI Controller initialized. Async Event Loop running.")
        self.toast.show_status("SUVI Online. System Ready.", duration_ms=4000)

    def _start_listening(self):
        """Triggered by wake word or hotkey."""
        if self.ring_window.state == RingState.IDLE:
            print("[Controller] Wake word detected. Initializing Live Session...")
            self.ring_window.set_state(RingState.LISTENING)
            self.voice_worker.start()
            asyncio.run_coroutine_threadsafe(self.live_session.connect(), self.loop)
        else:
            self._stop_listening()

    def _stop_listening(self):
        """Collapses the ring and stops the stream."""
        self.ring_window.set_state(RingState.IDLE)
        self.voice_worker.stop()
        asyncio.run_coroutine_threadsafe(self.live_session.disconnect(), self.loop)

    # --- System Tray Callbacks ---

    def open_dashboard(self):
        print("[Controller] Launching Next.js Cloud Run Dashboard...")
        
    def open_preferences(self):
        print("[Controller] Opening Preferences Panel...")

    def emergency_halt(self):
        print("[CRITICAL] 🛑 KILL SWITCH ACTIVATED 🛑")
        KillSwitch.activate()
        self.ring_window._on_ring_clicked() # Visually collapse the ring for feedback
        self.toast.show_status("Emergency Halt Activated", duration_ms=3000)
        
    def quit(self):
        print("[System] Shutting down SUVI safely...")
        if self.wake_word_worker:
            self.wake_word_worker.stop()
        self.loop.stop()
        self.app.quit()
        sys.exit(0)
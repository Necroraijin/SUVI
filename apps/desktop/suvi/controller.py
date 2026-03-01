import sys
from PyQt6.QtCore import QObject
from apps.desktop.suvi.ui.action_ring.ring_window import RingWindow
from apps.desktop.suvi.ui.tray import SuviTray
from apps.desktop.suvi.ui.notifications import MicroToast, ResultCard
from apps.desktop.suvi.workers import WakeWordWorker
from apps.desktop.suvi.executor import ActionExecutor, KillSwitch

class AppController(QObject):
    """Master controller that wires the UI, asyncio loop, and background services together."""
    
    def __init__(self, app, loop):
        super().__init__()
        self.app = app
        self.loop = loop
        
        # 1. Initialize UI Components FIRST
        self.ring_window = RingWindow()
        self.toast = MicroToast(parent_ring=self.ring_window)
        self.result_card = ResultCard(parent_ring=self.ring_window)
        self.tray = SuviTray(ring_window=self.ring_window, app_controller=self)
        
        # 2. Placeholders for Services
        self.live_session = None
        
        # 3. Initialize Background Workers
        self.wake_word_worker = WakeWordWorker()
        self.wake_word_worker.wake_word_detected.connect(self.ring_window._on_ring_clicked)
        self.wake_word_worker.start()

        # 4. Initialize Action Executor LAST (so it can use the UI components)
        self.action_executor = ActionExecutor()
        self.action_executor.action_started.connect(
            lambda msg: self.toast.show_status(msg, duration_ms=2000)
        )
        self.action_executor.action_completed.connect(self.result_card.show_result)
        self.action_executor.action_failed.connect(
            lambda msg: self.toast.show_status(f"Action Failed: {msg}", duration_ms=4000)
        )

    def start(self):
        """Brings the application online."""
        self.ring_window.show()
        self.tray.show()
        print("[System] SUVI Controller initialized. Async Event Loop running.")
        self.toast.show_status("SUVI Online. System Ready.", duration_ms=4000)

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
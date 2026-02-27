import sys
from PyQt6.QtCore import QObject
from apps.desktop.suvi.ui.action_ring.ring_window import RingWindow
from apps.desktop.suvi.ui.tray import SuviTray
from apps.desktop.suvi.ui.notifications import MicroToast, ResultCard

class AppController(QObject):
    """Master controller that wires the UI, asyncio loop, and background services together."""
    
    def __init__(self, app, loop):
        super().__init__()
        self.app = app
        self.loop = loop
        
        # 1. Initialize UI Components (Order matters!)
        self.ring_window = RingWindow()
        
        # Now that ring_window exists, we can pass it to the notifications and tray
        self.toast = MicroToast(parent_ring=self.ring_window)
        self.result_card = ResultCard(parent_ring=self.ring_window)
        self.tray = SuviTray(ring_window=self.ring_window, app_controller=self)
        
        # 2. Placeholders for Workers & Services
        self.live_session = None
        self.wake_word_worker = None
        self.action_executor = None

    def start(self):
        """Brings the application online."""
        self.ring_window.show()
        self.tray.show()
        
        print("[System] SUVI Controller initialized. Async Event Loop running.")
        
        # Test the toast!
        self.toast.show_status("SUVI Online. System Ready.", duration_ms=4000)

    # --- System Tray Callbacks ---

    def open_dashboard(self):
        print("[Controller] Launching Next.js Cloud Run Dashboard...")
        
    def open_preferences(self):
        print("[Controller] Opening Preferences Panel...")

    def emergency_halt(self):
        print("[CRITICAL] 🛑 KILL SWITCH ACTIVATED 🛑")
        self.ring_window._on_ring_clicked() # Visually collapse the ring for feedback
        self.toast.show_status("Emergency Halt Activated", duration_ms=3000)
        
    def quit(self):
        print("[System] Shutting down SUVI safely...")
        self.loop.stop()
        self.app.quit()
        sys.exit(0)
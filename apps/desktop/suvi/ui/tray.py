from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QObject

class SuviTray(QSystemTrayIcon):
    def __init__(self, ring_window, app_controller=None):
        # Use a standard OS computer icon temporarily so the app doesn't crash 
        # looking for a custom PNG we haven't created yet!
        default_icon = QApplication.style().standardIcon(
            QApplication.style().StandardPixmap.SP_ComputerIcon
        )
        super().__init__(default_icon)
        
        self.ring_window = ring_window
        self.app_controller = app_controller
        
        self.setToolTip('SUVI — Multi-Agent Desktop OS')
        
        # Create the right-click context menu
        self.menu = QMenu()
        
        # Action: Open Dashboard
        self.action_dashboard = QAction("Open Dashboard")
        self.action_dashboard.triggered.connect(self._open_dashboard)
        self.menu.addAction(self.action_dashboard)
        
        # Action: Action History
        self.action_history = QAction("Action History")
        self.action_history.triggered.connect(self._show_history)
        self.menu.addAction(self.action_history)
        
        self.menu.addSeparator()
        
        # Action: Kill Switch (Emergency Halt)
        self.action_kill = QAction("Kill Switch (Halt All Agents)")
        self.action_kill.triggered.connect(self._emergency_halt)
        self.menu.addAction(self.action_kill)
        
        self.menu.addSeparator()
        
        # Action: Quit SUVI
        self.action_quit = QAction("Quit SUVI")
        self.action_quit.triggered.connect(self._quit_app)
        self.menu.addAction(self.action_quit)
        
        self.setContextMenu(self.menu)

        # Handle left-clicks directly on the tray icon
        self.activated.connect(self._on_activate)

    def _open_dashboard(self):
        print("[System] Opening Next.js Dashboard...")
        # TODO: Wire to app_controller.open_dashboard()
        
    def _show_history(self):
        print("[System] Opening Action Log Panel...")
        # TODO: Wire to ring_window.show_action_log()

    def _emergency_halt(self):
        print("[CRITICAL] Kill Switch Activated. Halting all agent actions!")
        # TODO: Wire to app_controller.emergency_halt()
        
    def _quit_app(self):
        print("[System] Shutting down SUVI safely...")
        QApplication.quit()
        
    def _on_activate(self, reason):
        # If the user double-clicks the tray icon, trigger the ring animation!
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.ring_window._on_ring_clicked()
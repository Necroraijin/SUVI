import sys
import os
from PyQt6.QtWidgets import QApplication

# Ensure the root suvi directory is in the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from apps.desktop.suvi.ui.action_ring.ring_window import RingWindow

def main():
    app = QApplication(sys.argv)
    
    # Keep the app running even if we close the main window (for the system tray later)
    app.setQuitOnLastWindowClosed(False)
    
    ring = RingWindow()
    ring.show()
    
    print("SUVI Action Ring is live! Check the bottom right corner of your screen.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
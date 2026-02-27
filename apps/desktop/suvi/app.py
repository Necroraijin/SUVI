import sys
import asyncio
import qasync
from PyQt6.QtWidgets import QApplication
from apps.desktop.suvi.controller import AppController

def run_app():
    # 1. Create the Qt Application
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False) # Keep alive for System Tray
    
    # 2. Merge asyncio with the PyQt6 Event Loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # 3. Initialize and Start the Master Controller
    controller = AppController(app, loop)
    controller.start()
    
    # 4. Run the combined event loop forever
    with loop:
        loop.run_forever()
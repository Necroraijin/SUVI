import sys
import asyncio
import qasync
from PyQt6.QtWidgets import QApplication
from suvi.app import SUVIApplication

def main():
    # 1. Create the PyQt Application
    app = QApplication(sys.argv)
    
    # 2. Bridge asyncio and PyQt using qasync
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # 3. Initialize SUVI App
    suvi_app = SUVIApplication()
    
    # 4. Run the asyncio event loop
    with loop:
        loop.run_until_complete(suvi_app.start())

if __name__ == "__main__":
    main()

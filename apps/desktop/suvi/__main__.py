import sys
import os
import asyncio
import qasync
from PyQt6.QtWidgets import QApplication
from dotenv import load_dotenv


root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from apps.desktop.suvi.app import SUVIApplication

def main():
    
    load_dotenv(os.path.join(root_dir, '.env'))
    os.getenv("GEMINI_API_KEY")
    
    
    app = QApplication(sys.argv)
    
    
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    
    suvi_app = SUVIApplication()
    
    
    with loop:
        try:
            
            asyncio.ensure_future(suvi_app.start())
            loop.run_forever()
        except KeyboardInterrupt:
            print("\nShutting down SUVI...")

if __name__ == "__main__":
    main()

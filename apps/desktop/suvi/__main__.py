import sys
import os
import asyncio
import qasync
from PyQt6.QtWidgets import QApplication
from dotenv import load_dotenv

# Ensure the root directory is accessible for imports
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from apps.desktop.suvi.app import SUVIApplication

def main():
    # Load environment variables
    load_dotenv(os.path.join(root_dir, '.env'))
    api_key = os.getenv("GEMINI_API_KEY")
    
    # 1. Create the PyQt Application
    app = QApplication(sys.argv)
    
    # 2. Bridge asyncio and PyQt using qasync
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # 3. Initialize SUVI App
    suvi_app = SUVIApplication()
    
    # 4. Run the asyncio event loop
    with loop:
        try:
            # We use ensure_future so the Qt UI renders while the async loop runs
            asyncio.ensure_future(suvi_app.start())
            loop.run_forever()
        except KeyboardInterrupt:
            print("\nShutting down SUVI...")

if __name__ == "__main__":
    main()

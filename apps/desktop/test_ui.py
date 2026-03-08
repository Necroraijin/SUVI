import sys
import os
import asyncio
import qasync
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtWidgets import QApplication

# Ensure project root is in path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from apps.desktop.suvi.ui.widget.chat_widget import ChatWidget

async def run_ui_demo(widget: ChatWidget):
    """Cycle through the UI states to demonstrate the widget's capabilities."""
    states = [
        ("idle", "Waiting for command..."),
        ("listening", "Can you open Notepad for me?"),
        ("thinking", "Analyzing intent and planning actions..."),
        ("speaking", "Sure, I'm opening Notepad for you right now."),
        ("executing", "Clicking Start -> Typing 'Notepad' -> Opening app"),
        ("idle", "Task completed.")
    ]
    
    print("Starting UI Demo Loop...")
    for state, transcript in states:
        print(f"State: {state} | Text: {transcript}")
        widget.update_state(state)
        widget.update_transcript(transcript)
        await asyncio.sleep(2.5) # Wait a bit before next state
        
    print("Demo loop finished. You can drag the widget around. Click Stop to exit.")

def main():
    # 1. Create the PyQt Application
    app = QApplication(sys.argv)
    
    # 2. Bridge asyncio and PyQt using qasync
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # 3. Create the Floating Widget
    widget = ChatWidget()
    
    # 4. Connect the physical 'Stop' button to close the app for this test
    widget.interrupt_requested.connect(app.quit)
    
    # Show it
    widget.show()
    
    # 5. Run the asyncio event loop with the demo sequence
    with loop:
        # We use ensure_future to run the demo without blocking the UI rendering
        asyncio.ensure_future(run_ui_demo(widget))
        loop.run_forever()

if __name__ == "__main__":
    main()

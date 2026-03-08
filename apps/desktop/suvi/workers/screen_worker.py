from PyQt6.QtCore import QThread, pyqtSignal
import mss
import io
import time
from PIL import Image

class ScreenWorker(QThread):
    # Emits raw JPEG bytes to the main thread
    frame_captured = pyqtSignal(bytes)

    def __init__(self):
        super().__init__()
        self._running = False
        self._sct = mss.mss()

    def run(self):
        self._running = True
        while self._running:
            # Capture the primary monitor
            frame = self._sct.grab(self._sct.monitors[1])
            img = Image.frombytes("RGB", frame.size, frame.bgra, "raw", "BGRX")
            
            # Resize for optimal token usage
            w, h = img.size
            if w > 1366:
                img = img.resize((1366, int(1366 * h / w)), Image.LANCZOS)
                
            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=85)
            
            # Safely emit to the Qt Event Loop
            self.frame_captured.emit(buf.getvalue())
            
            # Capture at ~2 FPS for efficiency to not overwhelm the system
            time.sleep(0.5)

    def stop(self):
        """Cleanly stop the worker thread"""
        self._running = False
        self.wait()

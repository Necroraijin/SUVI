import mss
import io
from PIL import Image
from PyQt6.QtCore import QThread, pyqtSignal

class ScreenWorker(QThread):
    frame_ready = pyqtSignal(bytes)

    def __init__(self):
        super().__init__()

    def capture_now(self):
        """Called on-demand to grab a single frame of the current screen context."""
        try:
            with mss.mss() as sct:
                # monitor 1 is usually the primary display
                monitor = sct.monitors[1]
                frame = sct.grab(monitor)
                
                # Convert to PIL Image
                img = Image.frombytes('RGB', frame.size, frame.bgra, 'raw', 'BGRX')
                
                # Resize to 768px wide to minimize Vertex AI token usage and latency
                target_width = 768
                target_height = int(target_width * frame.height / frame.width)
                img = img.resize((target_width, target_height))
                
                # Compress to JPEG bytes
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=75)
                
                print("[ScreenWorker] Screen frame captured and compressed.")
                self.frame_ready.emit(buf.getvalue())
        except Exception as e:
            print(f"[ScreenWorker] Failed to capture screen: {e}")
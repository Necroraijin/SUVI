import io
from PyQt6.QtCore import QThread, pyqtSignal
from PIL import Image

class ReplayWorker(QThread):
    """
    Accumulates screenshots during a task and saves them as an animated GIF.
    This serves as visual proof of the AI's actions for the hackathon submission.
    """
    replay_saved = pyqtSignal(str)   # Emits the local file path (or Cloud Storage URL)

    def __init__(self):
        super().__init__()
        self._frames = []
        self._running = False
        self._session_id = "default"

    def set_session(self, session_id: str):
        self._session_id = session_id
        self._frames = []

    def add_frame(self, image_bytes: bytes):
        """Called whenever a new screenshot is captured during the Vision loop."""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            # Optional: Resize even further to keep GIF size reasonable
            img.thumbnail((800, 600), Image.Resampling.LANCZOS)
            self._frames.append(img)
        except Exception as e:
            print(f"Error adding frame to replay: {e}")

    def save_replay(self):
        if not self._frames:
            print("No frames to save for replay.")
            return

        print(f"🎬 Compiling {len(self._frames)} frames into SUVI Replay...")
        
        # Save to a temporary local file
        import tempfile
        import os
        
        temp_dir = tempfile.gettempdir()
        gif_path = os.path.join(temp_dir, f"suvi_replay_{self._session_id}.gif")
        
        try:
            self._frames[0].save(
                gif_path,
                save_all=True,
                append_images=self._frames[1:],
                duration=600,   # 600ms per frame
                loop=0,
                optimize=True,
            )
            print(f"✅ Replay saved to: {gif_path}")
            self.replay_saved.emit(gif_path)
            
            # FUTURE: Upload to Google Cloud Storage here
            
        except Exception as e:
            print(f"❌ Failed to save replay GIF: {e}")

    def run(self):
        # The actual heavy lifting is done in save_replay, which can block if large.
        # Running it in this thread prevents the UI from freezing.
        self.save_replay()

import io
from PyQt6.QtCore import QThread, pyqtSignal
from PIL import Image

class ReplayWorker(QThread):
    """
    Accumulates screenshots during a task and saves them as an animated GIF.
    This serves as visual proof of the AI's actions for the hackathon submission.
    """
    replay_saved = pyqtSignal(str)   

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
           
            img.thumbnail((800, 600), Image.Resampling.LANCZOS)
            self._frames.append(img)
        except Exception as e:
            print(f"Error adding frame to replay: {e}")

    def save_replay(self):
        if not self._frames:
            print("No frames to save for replay.")
            return

        print(f"🎬 Compiling {len(self._frames)} frames into SUVI Replay...")
        
        
        import tempfile
        import os
        
        temp_dir = tempfile.gettempdir()
        gif_path = os.path.join(temp_dir, f"suvi_replay_{self._session_id}.gif")
        
        try:
            self._frames[0].save(
                gif_path,
                save_all=True,
                append_images=self._frames[1:],
                duration=600,   
                loop=0,
                optimize=True,
            )
            print(f"✅ Replay saved to: {gif_path}")
            
            
            try:
                from google.cloud import storage
                import os
                
                project_id = os.getenv("GCP_PROJECT_ID")
                if project_id:
                    bucket_name = f"{project_id}-suvi-replays"
                    storage_client = storage.Client(project=project_id)
                    
                    # Ensure bucket exists
                    bucket = storage_client.bucket(bucket_name)
                    if not bucket.exists():
                        bucket = storage_client.create_bucket(bucket_name, location="us-central1")
                    
                    blob_name = f"replays/suvi_replay_{self._session_id}.gif"
                    blob = bucket.blob(blob_name)
                    blob.upload_from_filename(gif_path)
                    
                    try:
                        
                        url = blob.generate_signed_url(expiration=3600)
                    except Exception as sign_err:
                        
                        url = f"https://storage.googleapis.com/{bucket_name}/{blob_name}"
                        print(f"⚠️ Could not sign URL (likely using ADC). Returning standard link.")
                        
                    print(f"🚀 Replay uploaded to GCS: {url}")
                    self.replay_saved.emit(url)
                else:
                    self.replay_saved.emit(gif_path)
            except Exception as upload_err:
                print(f"⚠️ GCS Upload failed, using local path: {upload_err}")
                self.replay_saved.emit(gif_path)
                
        except Exception as e:
            print(f"❌ Failed to save replay GIF: {e}")

    def run(self):
        
        self.save_replay()

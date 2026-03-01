import numpy as np
import sounddevice as sd
from PyQt6.QtCore import QThread, pyqtSignal

class VoiceWorker(QThread):
    audio_chunk_ready = pyqtSignal(bytes)
    amplitude_changed = pyqtSignal(float)

    def __init__(self, sample_rate=16000, chunk_size=1600): 
        # 16000Hz is the standard for Gemini Live API. 
        # 1600 chunk size = 100ms chunks
        super().__init__()
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self._is_running = False

    def run(self):
        self._is_running = True
        try:
            with sd.InputStream(samplerate=self.sample_rate, channels=1, 
                                dtype='int16', blocksize=self.chunk_size) as stream:
                print("[VoiceWorker] Microphone stream opened.")
                while self._is_running:
                    audio_data, overflowed = stream.read(self.chunk_size)
                    if not self._is_running:
                        break
                    
                    # 1. Emit raw bytes for Vertex AI
                    self.audio_chunk_ready.emit(audio_data.tobytes())
                    
                    # 2. Calculate volume amplitude for the UI orb pulse (0.0 to 1.0)
                    peak = np.max(np.abs(audio_data))
                    amplitude = min(1.0, peak / 32768.0) # int16 max is 32768
                    self.amplitude_changed.emit(amplitude)
        except Exception as e:
            print(f"[VoiceWorker] Error accessing microphone: {e}")

    def stop(self):
        self._is_running = False
        self.wait()
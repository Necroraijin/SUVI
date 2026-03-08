import sounddevice as sd
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

class VoiceWorker(QThread):
    """
    Background thread to continuously capture microphone audio.
    Emits raw audio chunks to be sent to Gemini Live and amplitude for UI visuals.
    """
    # Emits raw PCM 16-bit audio bytes
    audio_chunk_captured = pyqtSignal(bytes)
    # Emits a float 0.0 - 1.0 representing microphone volume
    amplitude_updated = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self._running = False
        self.sample_rate = 16000 # Required by Gemini Live API
        self.chunk_ms = 100      # Send 100ms chunks
        self.chunk_samples = int(self.sample_rate * self.chunk_ms / 1000)

    def run(self):
        self._running = True
        
        # Log available devices for debugging
        print("🎤 Initializing Microphone...")
        
        def audio_callback(indata, frames, time, status):
            if not self._running:
                raise sd.CallbackStop()
            
            if status:
                print(f"⚠️ VoiceWorker Status: {status}")

            # Calculate amplitude for UI (0.0 to 1.0)
            amplitude = float(np.abs(indata).mean())
            self.amplitude_updated.emit(min(amplitude * 10, 1.0))

            # Debugging: Print a dot if we hear significant noise
            if amplitude > 0.05:
                print("🔊 [Mic picked up sound]")

            # Convert float32 to PCM 16-bit, which Gemini Live expects
            pcm_chunk = (indata[:, 0] * 32767).astype(np.int16).tobytes()
            self.audio_chunk_captured.emit(pcm_chunk)

        try:
            # We explicitly ask for the default input device to bypass Sound Mapper issues
            device_info = sd.query_devices(kind='input')
            print(f"🎤 Using Audio Device: {device_info['name']}")
            
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32,
                blocksize=self.chunk_samples,
                callback=audio_callback
            ):
                # Keep thread alive while input stream runs
                while self._running:
                    self.msleep(100)
        except Exception as e:
            print(f"❌ Microphone error: {e}")

    def stop(self):
        self._running = False
        self.wait()

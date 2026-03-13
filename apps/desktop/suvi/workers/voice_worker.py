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
        print("🎤 [VoiceWorker] Waiting for mic hand-off...")
        self.msleep(300) # Brief wait for WakeWordWorker to release the mic
        
        def audio_callback(indata, frames, time, status):
            if not self._running:
                raise sd.CallbackStop()
            
            if status:
                print(f"⚠️ VoiceWorker Status: {status}")

            # Calculate amplitude for UI (0.0 to 1.0)
            amplitude = float(np.abs(indata).mean())
            self.amplitude_updated.emit(min(amplitude * 10, 1.0))

            # Convert float32 to PCM 16-bit, which Gemini Live expects
            pcm_chunk = (indata[:, 0] * 32767).astype(np.int16).tobytes()
            self.audio_chunk_captured.emit(pcm_chunk)

        retry_count = 0
        while self._running and retry_count < 3:
            try:
                device_info = sd.query_devices(kind='input')
                print(f"🎤 [VoiceWorker] Opening Device: {device_info['name']}")
                
                with sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype=np.float32,
                    blocksize=self.chunk_samples,
                    callback=audio_callback
                ):
                    while self._running:
                        self.msleep(100)
                break # Exit loop if closed normally
            except Exception as e:
                retry_count += 1
                print(f"⚠️ [VoiceWorker] Mic Access Attempt {retry_count} failed: {e}")
                self.msleep(1000) # Wait and try again

    def stop(self):
        self._running = False
        self.wait()

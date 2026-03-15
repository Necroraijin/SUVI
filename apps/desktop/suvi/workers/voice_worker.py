import sounddevice as sd
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

class VoiceWorker(QThread):
    """
    Captures microphone audio continuously and streams
    PCM chunks to Gemini Live.

    Also emits amplitude for UI visualization.
    """

    audio_chunk_captured = pyqtSignal(bytes)
    amplitude_updated = pyqtSignal(float)

    def __init__(self):
        super().__init__()

        self._running = False

        # Gemini Live requirements
        self.sample_rate = 16000
        self.chunk_ms = 100
        self.chunk_samples = int(self.sample_rate * self.chunk_ms / 1000)

    # -----------------------------------------------------
    def run(self):
        self._running = True

        print("🎤 [VoiceWorker] Waiting for mic hand-off...")
        self.msleep(300)

        retry_count = 0

        while self._running and retry_count < 3:
            try:
                device_info = sd.query_devices(kind="input")
                print(f"🎤 [VoiceWorker] Opening Device: {device_info['name']}")

                with sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype=np.float32,
                    blocksize=self.chunk_samples,
                    callback=self._audio_callback,
                ):
                    while self._running:
                        self.msleep(100)
                break
            except Exception as e:
                retry_count += 1
                print(f"⚠️ [VoiceWorker] Mic attempt {retry_count} failed: {e}")
                self.msleep(1000)

        if retry_count >= 3:
            print("❌ [VoiceWorker] Failed to open microphone.")

    # -----------------------------------------------------
    def _audio_callback(self, indata, frames, time, status):
        if not self._running:
            raise sd.CallbackStop()

        if status:
            print(f"⚠️ VoiceWorker Status: {status}")

        amplitude = float(np.abs(indata).mean())
        self.amplitude_updated.emit(min(amplitude * 10, 1.0))

        pcm_chunk = (indata[:, 0] * 32767).astype(np.int16).tobytes()
        self.audio_chunk_captured.emit(pcm_chunk)

    # -----------------------------------------------------
    def stop(self):
        self._running = False

        try:
            self.wait(1000)
        except Exception:
            pass
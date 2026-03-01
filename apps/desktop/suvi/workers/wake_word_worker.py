from PyQt6.QtCore import QThread, pyqtSignal
from pynput import keyboard

class WakeWordWorker(QThread):
    wake_word_detected = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._listener = None

    def run(self):
        # Trigger SUVI with Ctrl+Shift+S
        def on_activate():
            print("[WakeWordWorker] Global hotkey pressed!")
            self.wake_word_detected.emit()

        hotkey = keyboard.GlobalHotKeys({
            '<ctrl>+<shift>+s': on_activate
        })
        
        self._listener = hotkey
        print("[WakeWordWorker] Listening for Ctrl+Shift+S...")
        self._listener.start()
        self._listener.join()

    def stop(self):
        if self._listener:
            self._listener.stop()
        self.wait()
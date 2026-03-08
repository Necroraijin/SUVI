import time
from PyQt6.QtCore import QThread, pyqtSignal
import speech_recognition as sr

class WakeWordWorker(QThread):
    """
    Background thread that listens for the 'Hey SUVI' wake word using Google's free Speech-to-Text.
    Emits a signal when detected, to activate the main SUVI Live loop.
    Requires NO API keys.
    """
    wake_word_detected = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._running = False
        self.recognizer = sr.Recognizer()
        
        # Adjust these for ambient noise sensitivity
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.5
        
        # Phonetic matches for "SUVI" since STT might misspell it
        self.wake_words = ["suvi", "sue vee", "suzie", "sooby", "subi", "hey cv", "hey siri", "ruby", "snoopy", "hey suvi"]

    def run(self):
        self._running = True
        print("🎧 Listening for wake word 'Hey SUVI'...")

        with sr.Microphone() as source:
            # Calibrate to background noise
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            while self._running:
                try:
                    # Listen in short chunks to be responsive
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                    
                    if not self._running:
                        break
                        
                    # Use Google's free Web Speech API
                    text = self.recognizer.recognize_google(audio).lower()
                    print(f"  [Heard]: {text}")
                    
                    # Check if any phonetic variation of the wake word is in the text
                    if any(wake_word in text for wake_word in self.wake_words):
                        print("🚨 WAKE WORD DETECTED: 'SUVI'!")
                        self.wake_word_detected.emit()
                        break # Stop listening once detected, handing over to the main session
                        
                except sr.WaitTimeoutError:
                    # Normal timeout if no one is speaking, just loop again
                    pass
                except sr.UnknownValueError:
                    # Speech was detected but couldn't be understood
                    pass
                except Exception as e:
                    print(f"❌ Wake word error: {e}")
                    time.sleep(1)

    def stop(self):
        self._running = False
        self.wait()

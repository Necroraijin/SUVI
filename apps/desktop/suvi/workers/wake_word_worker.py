import time
import traceback
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
        
        # High sensitivity settings - FIXED threshold so you don't have to shout
        self.recognizer.energy_threshold = 150 
        self.recognizer.dynamic_energy_threshold = False # Disable dynamic so it doesn't auto-mute you
        self.recognizer.pause_threshold = 0.5
        
        # Aggressive phonetic matches for "Hey SUVI"
        self.wake_words = [
            "suvi", "sue vee", "suzie", "sooby", "subi", "cv", "siri", "ruby", 
            "hey suvi", "hey sue vee", "hello suvi", "hey ruby", "hey subi",
            "heysuvi", "heysuevee", "hey cv", "hey siri", "hi suvi"
        ]

    def run(self):
        self._running = True
        print("🎧 Listening for wake word 'Hey SUVI' (High Sensitivity)...")

        while self._running:
            try:
                # Open microphone only inside the loop so we can release it quickly
                with sr.Microphone() as source:
                    # We don't need adjust_for_ambient_noise anymore since we hardcoded the threshold
                    
                    while self._running:
                        try:
                            # Listen with short timeout
                            audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                            
                            if not self._running:
                                break
                                
                            text = self.recognizer.recognize_google(audio).lower()
                            print(f"  [Heard]: {text}")
                            
                            if any(wake_word in text for wake_word in self.wake_words):
                                print("🚨 WAKE WORD DETECTED: 'SUVI'!")
                                # RELEASE MICROPHONE IMMEDIATELY by breaking the 'with' block
                                self.wake_word_detected.emit()
                                return 
                                
                        except sr.WaitTimeoutError:
                            pass
                        except sr.UnknownValueError:
                            pass
                            
            except Exception as e:
                if self._running:
                    print(f"❌ Microphone Access Error in WakeWord: {type(e).__name__} - {e}")
                    traceback.print_exc()
                    # If access is denied, wait a bit before retrying
                    time.sleep(2)
                else:
                    break

    def stop(self):
        self._running = False
        self.wait()

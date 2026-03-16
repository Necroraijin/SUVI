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
        
        
        self.recognizer.energy_threshold = 150 
        self.recognizer.dynamic_energy_threshold = False 
        self.recognizer.pause_threshold = 0.5
        
        
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
                
                with sr.Microphone() as source:
                    
                    
                    while self._running:
                        try:
                            
                            audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                            
                            if not self._running:
                                break
                                
                            text = self.recognizer.recognize_google(audio).lower()
                            print(f"  [Heard]: {text}")
                            
                            if any(wake_word in text for wake_word in self.wake_words):
                                print("🚨 WAKE WORD DETECTED: 'SUVI'!")
                                
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
                    
                    time.sleep(2)
                else:
                    break

    def stop(self):
        self._running = False
        self.wait()

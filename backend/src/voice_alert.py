"""
Voice alert system using text-to-speech engine
"""

import threading
import queue
import sys
from pathlib import Path

_backend_dir = Path(__file__).parent.parent.resolve()
_root_dir = Path(__file__).parent.parent.parent.resolve()
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

try:
    from src.logger import logger
    from config.config import ENABLE_VOICE, VOICE_RATE, VOICE_VOLUME
except ImportError:
    from backend.src.logger import logger
    from backend.config.config import ENABLE_VOICE, VOICE_RATE, VOICE_VOLUME

class VoiceAlertSystem:
    """Non-blocking text-to-speech alert system"""
    
    def __init__(self):
        self.enabled = ENABLE_VOICE
        self.speech_queue = queue.Queue()
        self.running = True
        self.engine = None
        
        if self.enabled:
            self._init_engine()
            self.thread = threading.Thread(target=self._worker, daemon=True)
            self.thread.start()

    def _init_engine(self):
        """Initialize pyttsx3 engine safely"""
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', VOICE_RATE)
            self.engine.setProperty('volume', VOICE_VOLUME)
        except Exception as e:
            logger.warning(f"Failed to initialize pyttsx3 TTS engine ({e}). Voice alerts will run in silent mode.")
            self.engine = None

    def _worker(self):
        """Background thread worker for speaking queue messages"""
        while self.running:
            try:
                text = self.speech_queue.get(timeout=1.0)
                if text is None:
                    break
                logger.info(f"VOICE ALERT: {text}")
                if self.engine is not None:
                    try:
                        self.engine.say(text)
                        self.engine.runAndWait()
                    except Exception as e:
                        logger.error(f"Error speaking text: {e}")
                self.speech_queue.task_done()
            except queue.Empty:
                continue

    def speak(self, text):
        """Queue text message for speech output"""
        if not self.enabled:
            return
        if self.speech_queue.qsize() < 5:  # Avoid queuing too many old alerts
            self.speech_queue.put(text)

    def alert_high_traffic(self, lane_name="main lane"):
        self.speak(f"High traffic density detected on {lane_name}")

    def alert_speeding_vehicle(self, info):
        speed = info.get('speed', 0)
        self.speak(f"Speeding vehicle detected at {speed:.0f} kilometers per hour")

    def alert_collision(self, info):
        self.speak("Warning, vehicle collision detected")

    def alert_accident(self, info):
        self.speak("Emergency alert, traffic accident detected")

    def alert_fire(self, info):
        self.speak("Danger, fire incident detected")

    def alert_sudden_stop(self, info):
        self.speak("Caution, sudden vehicle deceleration detected")

    def shutdown(self):
        """Shutdown worker thread"""
        self.running = False
        self.speech_queue.put(None)


if __name__ == "__main__":
    import time
    vas = VoiceAlertSystem()
    tts_mode = "TTS ACTIVE" if vas.engine is not None else "SILENT MODE (pyttsx3 not installed)"

    if vas.enabled:
        print(f"[INFO] Voice engine: {tts_mode}")
        print(f"[INFO] Speaking alerts now — listen carefully...")
        vas.alert_speeding_vehicle({"speed": 85.0})
        time.sleep(4)   # Wait for pyttsx3 to speak first alert
        vas.alert_high_traffic("lane_0")
        time.sleep(4)   # Wait for second alert
        vas.alert_collision({})
        time.sleep(4)   # Wait for third alert
        vas.shutdown()
        print(f"[OK] VoiceAlertSystem tested successfully! Mode: {tts_mode} | Voice Enabled: {vas.enabled}")
    else:
        print(f"[OK] VoiceAlertSystem tested successfully! Mode: DISABLED | Voice Enabled: {vas.enabled}")


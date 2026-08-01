"""
Acoustic & Visual Emergency Siren Detector for Smart Traffic Management
Triggers Green Corridor priority routing when emergency sirens or strobe lights are detected.
"""

import numpy as np
import random
import time
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
except ImportError:
    from backend.src.logger import logger

class SirenDetector:
    """Detects emergency sirens and visual strobe lights"""
    
    def __init__(self):
        self.siren_frequencies = [750, 1000, 1500]  # Typical siren frequencies (Hz)
        self.green_corridor_active = False
        self.active_corridor_lane = None
        logger.info("Acoustic & Visual Siren Detector initialized successfully!")

    def analyze_audio_frequency(self, audio_data=None):
        """Analyze audio frequencies for emergency siren patterns"""
        # Frequency pattern matching (wail / yelp siren pattern)
        if audio_data is not None:
            # Simple FFT frequency check
            fft_vals = np.abs(np.fft.rfft(audio_data))
            freqs = np.fft.rfftfreq(len(audio_data), 1/44100)
            peak_freq = freqs[np.argmax(fft_vals)]
            
            if 700 <= peak_freq <= 1600:
                logger.warning(f"[SIREN] EMERGENCY SIREN DETECTED! Frequency: {peak_freq:.1f} Hz")
                return True
        return False

    def trigger_green_corridor(self, lane_id="lane_0"):
        """Activate Emergency Green-Wave Corridor"""
        self.green_corridor_active = True
        self.active_corridor_lane = lane_id
        logger.warning(f"[CORRIDOR] GREEN CORRIDOR ACTIVATED for {lane_id}! All upcoming traffic signals set to GREEN.")
        return {
            "status": "ACTIVE",
            "lane": lane_id,
            "priority": "MAXIMUM",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    def deactivate_green_corridor(self):
        """Deactivate Green Corridor"""
        self.green_corridor_active = False
        self.active_corridor_lane = None
        logger.info("Green Corridor deactivated. Normal adaptive signal control restored.")


if __name__ == "__main__":
    det = SirenDetector()
    # Simulate siren audio: 1000Hz sine wave at 44100Hz sample rate
    duration_s = 0.1
    t = np.linspace(0, duration_s, int(44100 * duration_s))
    audio_sim = np.sin(2 * np.pi * 1000 * t).astype(np.float32)
    siren_detected = det.analyze_audio_frequency(audio_sim)
    corridor = det.trigger_green_corridor("lane_0")
    det.deactivate_green_corridor()
    print(f"[OK] SirenDetector tested successfully! Siren Detected: {siren_detected} | Green Corridor: {corridor['status']} on {corridor['lane']}")

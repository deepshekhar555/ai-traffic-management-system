"""
ByteTrack Advanced Speed Tracking Module
"""

import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent.parent.resolve()
backend_dir = Path(__file__).parent.parent.resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

try:
    from src.speed_tracker import SpeedTracker
except ImportError:
    from backend.src.speed_tracker import SpeedTracker

class ByteTrackSpeedTracker(SpeedTracker):
    """ByteTrack-based tracker extending SpeedTracker"""
    
    def __init__(self, fps=30, pixels_per_meter=20, max_age=30, **kwargs):
        super().__init__(fps=fps, pixels_per_meter=pixels_per_meter)
        self.max_age = max_age


if __name__ == "__main__":
    tracker = ByteTrackSpeedTracker()
    print(f"[OK] ByteTrackSpeedTracker initialized successfully! FPS: {tracker.fps}, Max Age: {tracker.max_age}")

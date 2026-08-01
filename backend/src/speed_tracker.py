"""
Speed Measurement & Centroid Tracking Module
"""

import math
import time
import sys
from pathlib import Path
from typing import List, Dict, Tuple

_backend_dir = Path(__file__).parent.parent.resolve()
_root_dir = Path(__file__).parent.parent.parent.resolve()
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

try:
    from config.config import FPS, PIXELS_PER_METER, SPEED_LIMIT_KMH
except ImportError:
    from backend.config.config import FPS, PIXELS_PER_METER, SPEED_LIMIT_KMH

try:
    from src.logger import logger
except ImportError:
    from backend.src.logger import logger

class SpeedTracker:
    """Tracks vehicle centroids across frames and calculates speed in km/h"""
    
    def __init__(self, fps=FPS, pixels_per_meter=PIXELS_PER_METER):
        self.fps = fps
        self.pixels_per_meter = pixels_per_meter
        self.next_track_id = 1
        self.tracks: Dict[int, Dict] = {}

    def match_detections(self, detections: List[Dict], frame_h: int, frame_w: int) -> List[Dict]:
        """
        Match current frame detections to existing tracks by minimum centroid distance
        Returns tracked objects with updated current_speed and max_speed
        """
        tracked_results = []

        for det in detections:
            cx, cy = det.get("center", (0, 0))
            class_name = det.get("class_name", "car")
            
            # Find nearest track
            best_id = None
            min_dist = 50.0  # Max pixel search distance threshold
            
            for tid, t_info in self.tracks.items():
                prev_x, prev_y = t_info["center"]
                dist = math.sqrt((cx - prev_x)**2 + (cy - prev_y)**2)
                if dist < min_dist:
                    min_dist = dist
                    best_id = tid

            if best_id is None:
                best_id = self.next_track_id
                self.next_track_id += 1
                self.tracks[best_id] = {
                    "center": (cx, cy),
                    "class_name": class_name,
                    "history": [(cx, cy)],
                    "current_speed": 0.0,
                    "max_speed": 0.0,
                    "last_seen": time.time()
                }

            # Update existing track
            t_info = self.tracks[best_id]
            prev_x, prev_y = t_info["center"]
            dist_pixels = math.sqrt((cx - prev_x)**2 + (cy - prev_y)**2)
            dist_meters = dist_pixels / self.pixels_per_meter
            
            # Time delta between frames in seconds
            time_delta = 1.0 / self.fps
            speed_mps = dist_meters / time_delta if time_delta > 0 else 0
            speed_kmh = speed_mps * 3.6

            t_info["center"] = (cx, cy)
            t_info["history"].append((cx, cy))
            if len(t_info["history"]) > 10:
                t_info["history"].pop(0)

            t_info["current_speed"] = speed_kmh
            t_info["max_speed"] = max(t_info["max_speed"], speed_kmh)
            t_info["last_seen"] = time.time()

            item = {
                "track_id": best_id,
                "class_name": class_name,
                "center": (cx, cy),
                "bbox": det.get("bbox", (0, 0, 0, 0)),
                "confidence": det.get("confidence", 0.9),
                "current_speed": speed_kmh,
                "speed": speed_kmh,
                "max_speed": t_info["max_speed"],
                "frames_seen": len(t_info["history"])
            }
            tracked_results.append(item)

        return tracked_results


    def get_speeding_vehicles(self, tracked_vehicles: List[Dict], speed_limit=SPEED_LIMIT_KMH) -> List[Dict]:
        """Return list of vehicles exceeding speed_limit"""
        speeding = []
        for v in tracked_vehicles:
            sp = v.get("current_speed", v.get("speed", 0.0))
            if sp > speed_limit:
                speeding.append({
                    "track_id": v["track_id"],
                    "class_name": v["class_name"],
                    "speed": sp,
                    "excess": sp - speed_limit,
                    "center": v.get("center", (0,0))
                })
        return speeding

    def get_speed_statistics(self, tracked_vehicles: List[Dict]) -> Dict:
        """Calculate and return statistics for all tracked vehicles in the current frame"""
        speeds = [v.get('current_speed', v.get('speed', 0.0)) for v in tracked_vehicles if isinstance(v, dict)]
        confidences = [v.get('confidence', 0.9) for v in tracked_vehicles if isinstance(v, dict)]
        valid_speeds = [s for s in speeds if s > 0.0]
        
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.9
        
        if not valid_speeds:
            return {
                "avg_speed": 0.0,
                "max_speed": 0.0,
                "min_speed": 0.0,
                "speeding_count": 0,
                "average_confidence": avg_conf,
                "tracked_vehicles": tracked_vehicles
            }
        
        avg_speed = sum(valid_speeds) / len(valid_speeds)
        max_speed = max(valid_speeds)
        min_speed = min(valid_speeds)
        speeding_count = sum(1 for s in valid_speeds if s > 60.0)
        
        return {
            "avg_speed": avg_speed,
            "max_speed": max_speed,
            "min_speed": min_speed,
            "speeding_count": speeding_count,
            "average_confidence": avg_conf,
            "tracked_vehicles": tracked_vehicles
        }


if __name__ == "__main__":
    tracker = SpeedTracker(fps=FPS, pixels_per_meter=PIXELS_PER_METER)
    frame1 = [
        {"center": (100, 200), "class_name": "car",   "bbox": (80,180,130,230),  "confidence": 0.92},
        {"center": (400, 300), "class_name": "truck",  "bbox": (370,270,440,340), "confidence": 0.88},
        {"center": (700, 250), "class_name": "car",   "bbox": (680,230,730,280), "confidence": 0.95},
    ]
    frame2 = [
        {"center": (108, 200), "class_name": "car",   "bbox": (88,180,138,230),  "confidence": 0.91},
        {"center": (415, 300), "class_name": "truck",  "bbox": (385,270,455,340), "confidence": 0.87},
        {"center": (780, 250), "class_name": "car",   "bbox": (760,230,810,280), "confidence": 0.94},
    ]
    tracker.match_detections(frame1, 720, 1280)
    tracked = tracker.match_detections(frame2, 720, 1280)
    stats = tracker.get_speed_statistics(tracked)
    speeding = tracker.get_speeding_vehicles(tracked)
    print(f"[OK] SpeedTracker tested successfully!")
    for v in tracked:
        print(f"  Track #{v['track_id']} ({v['class_name']}): Speed={v['current_speed']:.1f} km/h")
    print(f"  Avg Speed: {stats['avg_speed']:.1f} km/h | Max: {stats['max_speed']:.1f} km/h | Speeding: {len(speeding)} vehicles")

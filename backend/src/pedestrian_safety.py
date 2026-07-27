"""
Pedestrian Crosswalk Safety & Collision Avoidance System
Calculates Time-to-Collision (TTC) between approaching speeding vehicles and pedestrians on crosswalks.
"""

import math
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

class PedestrianSafetySystem:
    """Predicts pedestrian-vehicle collision risk on crosswalk zones"""
    
    def __init__(self, ttc_threshold_seconds=2.5):
        self.ttc_threshold = ttc_threshold_seconds  # Time To Collision threshold in seconds
        self.warnings = []
        logger.info("Pedestrian Crosswalk Safety & Collision Avoidance Engine initialized!")

    def calculate_ttc(self, ped_center, vehicle_center, vehicle_speed_kmh):
        """
        Calculate Time-to-Collision (TTC) in seconds
        TTC = Distance / Speed
        """
        px, py = ped_center
        vx, vy = vehicle_center
        distance_pixels = math.sqrt((px - vx)**2 + (py - vy)**2)
        
        # Convert speed km/h to pixels per second (~20 pixels = 1 meter, 1 km/h = 0.278 m/s)
        speed_mps = vehicle_speed_kmh * 0.278
        speed_pps = speed_mps * 20.0  # pixels per second
        
        if speed_pps <= 0:
            return 999.0
            
        ttc_seconds = distance_pixels / speed_pps
        return round(ttc_seconds, 2)

    def analyze_crosswalk_safety(self, pedestrians, vehicles):
        """
        Analyze safety interaction between all detected pedestrians and approaching vehicles
        Returns active hazard warnings list
        """
        hazards = []
        for ped in pedestrians:
            ped_center = ped["center"]
            for v in vehicles:
                vehicle_center = v["center"]
                speed = v.get("current_speed", 40.0)
                
                ttc = self.calculate_ttc(ped_center, vehicle_center, speed)
                if ttc <= self.ttc_threshold:
                    hazard = {
                        "pedestrian_center": ped_center,
                        "vehicle_track_id": v.get("track_id", 0),
                        "vehicle_speed": speed,
                        "ttc_seconds": ttc,
                        "severity": "CRITICAL_HAZARD",
                        "action": "TRIGGER_PEDESTRIAN_RED_LIGHT"
                    }
                    hazards.append(hazard)
                    logger.warning(f"PEDESTRIAN COLLISION HAZARD! Vehicle #{v.get('track_id')} approaching pedestrian. TTC = {ttc:.2f}s!")
                    
        return hazards


if __name__ == "__main__":
    pss = PedestrianSafetySystem(ttc_threshold_seconds=2.5)
    # Simulate 1 pedestrian and 1 fast approaching vehicle
    pedestrians = [{"center": (640, 400), "track_id": 99}]
    vehicles = [{"center": (640, 200), "track_id": 7, "current_speed": 80.0}]
    # TTC = distance(200px) / speed(80 km/h -> 444.8 pps) = ~0.45s -> CRITICAL
    hazards = pss.analyze_crosswalk_safety(pedestrians, vehicles)
    ttc_val = pss.calculate_ttc((640, 400), (640, 200), 80.0)
    print(f"[OK] PedestrianSafetySystem tested successfully! TTC: {ttc_val}s | Hazards detected: {len(hazards)} (Severity: {hazards[0]['severity'] if hazards else 'NONE'})")

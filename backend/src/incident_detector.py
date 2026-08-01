"""
Incident & Collision Detection Module
"""

from typing import Tuple, List, Dict

class IncidentDetector:
    """Detects collisions, sudden stops, and fire/smoke incidents"""
    
    def __init__(self):
        pass

    def check_collision(self, bbox1: Tuple[int, int, int, int], bbox2: Tuple[int, int, int, int]) -> Tuple[bool, float]:
        """
        Calculate Intersection over Union (IoU) between two bounding boxes
        Returns (is_collision, iou_value)
        """
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2

        # Intersection coordinates
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)

        intersection_area = max(0, x2_i - x1_i) * max(0, y2_i - y1_i)
        if intersection_area == 0:
            return False, 0.0

        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union_area = area1 + area2 - intersection_area

        iou = intersection_area / float(union_area) if union_area > 0 else 0.0
        is_collision = iou > 0.3
        return is_collision, iou

    def detect_sudden_stop(self, vehicle: Dict, prev_speed: float) -> Dict:
        """Detect sudden deceleration or stop"""
        curr_speed = vehicle.get("current_speed", vehicle.get("speed", 0.0))
        speed_drop = prev_speed - curr_speed

        if prev_speed > 25.0 and speed_drop > 20.0:
            return {
                "track_id": vehicle["track_id"],
                "prev_speed": prev_speed,
                "current_speed": curr_speed,
                "speed_drop": speed_drop
            }
        return None

    def detect_fire(self, detections: List[Dict]) -> List[Dict]:
        """Check detections for fire or smoke classes"""
        fires = []
        for det in detections:
            c_name = str(det.get("class_name", "")).lower()
            if "fire" in c_name or "smoke" in c_name or "flame" in c_name:
                fires.append(det)
        return fires

    def analyze_incidents(self, tracked_vehicles: List[Dict], detections: List[Dict]) -> Dict:
        """Run all incident detection rules on current frame"""
        collisions = []
        # Check pairwise collisions
        n = len(tracked_vehicles)
        for i in range(n):
            for j in range(i + 1, n):
                v1, v2 = tracked_vehicles[i], tracked_vehicles[j]
                is_col, iou = self.check_collision(v1["bbox"], v2["bbox"])
                if is_col:
                    collisions.append({
                        "vehicle1_id": v1["track_id"],
                        "vehicle2_id": v2["track_id"],
                        "iou": iou
                    })

        fires = self.detect_fire(detections)
        return {
            "collisions": collisions,
            "fires": fires
        }


if __name__ == "__main__":
    detector = IncidentDetector()
    # Test collision IoU detection
    bbox1 = (100, 100, 300, 300)
    bbox2 = (200, 200, 400, 400)  # Overlapping box
    is_col, iou = detector.check_collision(bbox1, bbox2)
    # Test sudden stop
    vehicle = {"track_id": 7, "current_speed": 5.0}
    stop = detector.detect_sudden_stop(vehicle, prev_speed=60.0)
    # Test full analysis
    vehicles = [{"track_id": 1, "bbox": (100,100,300,300)}, {"track_id": 2, "bbox": (200,200,400,400)}]
    result = detector.analyze_incidents(vehicles, [])
    print(f"[OK] IncidentDetector tested successfully! Collision IoU: {iou:.2f} | Sudden Stop: {stop is not None} | Incidents: {result}")


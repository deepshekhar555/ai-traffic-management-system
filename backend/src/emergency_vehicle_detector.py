"""
Emergency Vehicle Detection Module
"""

class EmergencyVehicleDetector:
    """Detects emergency vehicles (ambulance, fire truck, police car)"""
    
    def __init__(self):
        self.active_detection = None

    def detect_emergency_vehicles(self, detections, frame):
        """Analyze detections for emergency vehicle classes or patterns"""
        for det in detections:
            c_name = str(det.get("class_name", "")).lower()
            if "ambulance" in c_name or "police" in c_name or "fire" in c_name:
                self.active_detection = {
                    "type": c_name.capitalize(),
                    "center": det.get("center", (frame.shape[1] // 2, frame.shape[0] // 2)),
                    "bbox": det.get("bbox", (0, 0, 100, 100))
                }
                return self.active_detection
        return None

    def get_emergency_type_emoji(self, type_str: str) -> str:
        """Return emoji for emergency type"""
        t = str(type_str).lower()
        if "ambulance" in t:
            return "🚑"
        elif "fire" in t:
            return "🚒"
        elif "police" in t:
            return "🚓"
        return "🚨"

    def clear_detection(self):
        """Clear active detection"""
        self.active_detection = None


if __name__ == "__main__":
    import numpy as np
    detector = EmergencyVehicleDetector()
    dummy_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    sample_dets = [{"class_name": "ambulance", "center": (500, 400), "bbox": (450, 350, 550, 450)}]
    res = detector.detect_emergency_vehicles(sample_dets, dummy_frame)
    print(f"[OK] EmergencyVehicleDetector tested successfully! Detected Type: {res['type']}")



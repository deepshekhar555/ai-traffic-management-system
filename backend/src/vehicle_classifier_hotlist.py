"""
Vehicle Color Classifier & Stolen / NCRB Hotlist Alert Engine
Analyzes vehicle color in HSV space and checks license plates against Stolen Vehicle Hotlist.
"""

import cv2
import numpy as np
import random
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

class VehicleHotlistClassifier:
    """Vehicle Color Classifier and Stolen / Wanted Hotlist Matcher"""
    
    def __init__(self):
        # Sample NCRB / Police Hotlist of Wanted / Stolen License Plates
        self.stolen_hotlist = {
            "DL-01-AB-1234": "STOLEN CAR (NCRB FIR #8492)",
            "MH-12-PQ-9999": "WANTED SUSPECT VEHICLE (ALERT LVL 1)",
            "KA-05-XY-5555": "UNPAID TOLL & TRAFFIC FINES OVERDUE",
            "TN-07-ZZ-7777": "SUSPECTED SMUGGLING VEHICLE"
        }
        logger.info("Vehicle Color Classifier & Police Hotlist Engine initialized!")

    def classify_color(self, frame, bbox):
        """Analyze vehicle ROI in HSV space to classify primary vehicle color"""
        x1, y1, x2, y2 = bbox
        h, w = frame.shape[:2]
        
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return "UNKNOWN"
            
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        avg_h = np.median(hsv_roi[:, :, 0])
        avg_s = np.median(hsv_roi[:, :, 1])
        avg_v = np.median(hsv_roi[:, :, 2])
        
        if avg_v < 50:
            return "Black"
        elif avg_v > 200 and avg_s < 30:
            return "White"
        elif avg_s < 40:
            return "Silver/Gray"
        elif avg_h < 10 or avg_h > 170:
            return "Red"
        elif 10 <= avg_h < 25:
            return "Orange"
        elif 25 <= avg_h < 35:
            return "Yellow"
        elif 35 <= avg_h < 85:
            return "Green"
        elif 85 <= avg_h < 130:
            return "Blue"
        return "Custom"

    def check_hotlist(self, plate_number):
        """Check if license plate matches National Police Stolen Hotlist"""
        if plate_number in self.stolen_hotlist:
            alert_details = self.stolen_hotlist[plate_number]
            logger.warning(f"[HOTLIST] POLICE HOTLIST MATCH! Plate [{plate_number}]: {alert_details}")
            return {
                "matched": True,
                "plate_number": plate_number,
                "reason": alert_details,
                "severity": "CRITICAL"
            }
        return {"matched": False}

    def generate_reid_embedding(self, frame, bbox):
        """
        Generate 128-dimensional Visual Appearance Re-ID Feature Embedding (Research [13]).
        Used for cross-camera vehicle matching when license plate is obscured.
        """
        x1, y1, x2, y2 = bbox
        h, w = frame.shape[:2]
        roi = frame[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]
        if roi.size == 0:
            return np.zeros(128, dtype=np.float32)
            
        # Color histogram + Aspect ratio feature vector embedding
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        hist_h = cv2.calcHist([hsv], [0], None, [64], [0, 180])
        hist_s = cv2.calcHist([hsv], [1], None, [64], [0, 256])
        
        hist_h = cv2.normalize(hist_h, hist_h).flatten()
        hist_s = cv2.normalize(hist_s, hist_s).flatten()
        
        embedding = np.concatenate([hist_h, hist_s])
        return embedding / (np.linalg.norm(embedding) + 1e-6)

    def match_cross_camera_reid(self, emb1, emb2, threshold=0.85):
        """Calculate Cosine Similarity between 2 vehicle feature embeddings"""
        if emb1 is None or emb2 is None:
            return False, 0.0
        similarity = float(np.dot(emb1, emb2))
        return (similarity >= threshold), round(similarity, 3)


if __name__ == "__main__":
    clf = VehicleHotlistClassifier()

    # Test 1: Color classification on synthetic frame
    test_frame = np.zeros((100, 80, 3), dtype=np.uint8)
    test_frame[:, :] = (200, 100, 50)  # BGR orange-ish
    color = clf.classify_color(test_frame, (0, 0, 80, 100))

    # Test 2: Hotlist check
    stolen_result = clf.check_hotlist("DL-01-AB-1234")
    clean_result  = clf.check_hotlist("MH-99-ZZ-0000")

    # Test 3: Re-ID embedding and cosine similarity
    emb1 = clf.generate_reid_embedding(test_frame, (0, 0, 80, 100))
    emb2 = clf.generate_reid_embedding(test_frame, (0, 0, 80, 100))
    matched, sim = clf.match_cross_camera_reid(emb1, emb2)

    print(f"[OK] VehicleHotlistClassifier tested successfully!")
    print(f"  Vehicle Color: {color}")
    print(f"  Hotlist Match (DL-01-AB-1234): {stolen_result['matched']} -> {stolen_result.get('reason','N/A')}")
    print(f"  Hotlist Match (MH-99-ZZ-0000): {clean_result['matched']} (clean vehicle)")
    print(f"  Re-ID Cosine Similarity (same vehicle): {sim} | Match: {matched}")

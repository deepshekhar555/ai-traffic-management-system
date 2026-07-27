"""
UI Overlay and Dashboard Renderer
"""

import cv2
import numpy as np

class TrafficDashboard:
    """Renders stats and status panels on video frame overlay"""
    
    def __init__(self):
        pass

    def add_traffic_stats(self, frame, stats):
        """Draw traffic statistics panel on frame"""
        frame_copy = frame.copy()
        if not stats:
            return frame_copy
        
        cv2.rectangle(frame_copy, (10, 10), (300, 120), (40, 40, 40), -1)
        cv2.rectangle(frame_copy, (10, 10), (300, 120), (0, 255, 255), 2)
        
        vehicles = stats.get("vehicles", 0)
        level = stats.get("level", "LOW")
        density = stats.get("density", 0.0) * 100
        
        cv2.putText(frame_copy, f"Vehicles: {vehicles}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame_copy, f"Density: {density:.1f}%", (20, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame_copy, f"Level: {level}", (20, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        return frame_copy


if __name__ == "__main__":
    dash = TrafficDashboard()
    dummy_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    rendered = dash.add_traffic_stats(dummy_frame, {"vehicles": 12, "density": 0.45, "level": "MODERATE"})
    print(f"[OK] TrafficDashboard HUD Renderer tested successfully! Rendered Frame Shape: {rendered.shape}")
    print("  Note: To open the Web Dashboard in browser, run 'python backend/dashboard_app.py' or 'python start_all.py'!")


"""
Lane Analysis and Partitioning Module
"""

import cv2
import numpy as np

class LaneDetector:
    """Divides video stream into virtual lanes and computes per-lane traffic levels"""
    
    def __init__(self, num_lanes=2):
        self.num_lanes = num_lanes
        self.lane_width = None
        self.history = {f"lane_{i}": [] for i in range(num_lanes)}

    def divide_frame_into_lanes(self, frame_w, frame_h, vehicle_detections):
        """Divide frame horizontally into lanes and group vehicles by lane"""
        self.lane_width = frame_w / self.num_lanes
        lane_data = {}

        for i in range(self.num_lanes):
            lane_key = f"lane_{i}"
            min_x = i * self.lane_width
            max_x = (i + 1) * self.lane_width

            lane_vehicles = []
            for det in vehicle_detections:
                cx, cy = det.get("center", (0, 0))
                if min_x <= cx < max_x:
                    lane_vehicles.append(det)

            count = len(lane_vehicles)
            if count >= 6:
                level = "CRITICAL"
            elif count >= 4:
                level = "HIGH"
            elif count >= 2:
                level = "MODERATE"
            else:
                level = "LOW"

            lane_data[lane_key] = {
                "vehicles": lane_vehicles,
                "count": count,
                "level": level
            }

        return lane_data

    def update_lane_history(self, lane_data):
        """Update history metrics for each lane"""
        for lane_key, data in lane_data.items():
            if lane_key in self.history:
                self.history[lane_key].append(data["count"])

    def draw_lanes_on_frame(self, frame, lane_data, signal_state):
        """Draw lane boundary lines and traffic signal colors on frame"""
        h, w = frame.shape[:2]
        if self.lane_width is None:
            self.lane_width = w / self.num_lanes

        for i in range(1, self.num_lanes):
            x = int(i * self.lane_width)
            cv2.line(frame, (x, 50), (x, h - 90), (255, 255, 255), 2)

        # Draw signals for each lane
        for i in range(self.num_lanes):
            lane_key = f"lane_{i}"
            lane_x = int(i * self.lane_width)
            color = signal_state.get(lane_key, (0, 255, 0)) if signal_state else (0, 255, 0)

            # Signal box
            cv2.rectangle(frame, (lane_x + 15, 60), (lane_x + 55, 100), (0, 0, 0), -1)
            cv2.circle(frame, (lane_x + 35, 80), 12, color, -1)

        return frame

    def highlight_lane(self, frame, lane_id, color=(255, 0, 255), alpha=0.15):
        """Highlight a specific lane with semi-transparent color overlay"""
        try:
            lane_idx = int(lane_id.split("_")[-1])
        except (ValueError, IndexError):
            lane_idx = 0

        h, w = frame.shape[:2]
        if self.lane_width is None:
            self.lane_width = w / self.num_lanes

        x1 = int(lane_idx * self.lane_width)
        x2 = int((lane_idx + 1) * self.lane_width)

        overlay = frame.copy()
        cv2.rectangle(overlay, (x1, 50), (x2, h - 90), color, -1)
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        return frame

    def detect_red_light_running(self, vehicle_detections, signal_state, frame_h):
        """
        Detect Red-Light Running (RLR) Violations (Research [10, 12]).
        Triggers when a vehicle crosses the virtual stop-line (Y_stop) during RED signal state.
        """
        violations = []
        stop_line_y = int(frame_h * 0.70)  # Virtual stop line at 70% height

        for det in vehicle_detections:
            cx, cy = det.get("center", (0, 0))
            lane_idx = min(int(cx / (self.lane_width or 640)), self.num_lanes - 1)
            lane_key = f"lane_{lane_idx}"
            lane_color = signal_state.get(lane_key, "RED")

            # Check if vehicle has crossed the stop line while signal is RED
            if cy >= stop_line_y and lane_color == "RED":
                violations.append({
                    "vehicle": det,
                    "lane": lane_key,
                    "stop_line_y": stop_line_y,
                    "violation_type": "RED_LIGHT_RUNNING",
                    "fine_amount_inr": 5000
                })
        return violations


if __name__ == "__main__":
    lane_det = LaneDetector(num_lanes=2)
    vehicles = [
        {"center": (300, 400), "track_id": 1, "class_name": "car"},
        {"center": (320, 350), "track_id": 2, "class_name": "car"},
        {"center": (900, 400), "track_id": 3, "class_name": "truck"},
    ]
    lane_data = lane_det.divide_frame_into_lanes(1280, 720, vehicles)
    print(f"[OK] LaneDetector tested successfully!")
    for lane, data in lane_data.items():
        print(f"  {lane}: {data['count']} vehicles -> Level: {data['level']}")



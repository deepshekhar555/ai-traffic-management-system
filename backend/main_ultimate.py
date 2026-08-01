"""
AI Traffic Management System - Ultimate Version
Combines single-threaded, multi-threaded, performance, accuracy, and balanced operating modes.
Supports multiple display styles and feature toggles.
"""

import sys
import time
import argparse
import cv2
from pathlib import Path
from datetime import datetime

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent))

from main import TrafficManagementApp
from config.config import MODEL_NAME, FRAME_WIDTH, FRAME_HEIGHT, FPS_UPDATE_INTERVAL
from src.logger import logger

class UltimateTrafficApp(TrafficManagementApp):
    """
    Ultimate AI Traffic Management System with configurable modes, 
    display styles, and feature toggles.
    """
    def __init__(self, camera_source=0, mode="balanced", display="detailed", 
                 enable_speed=True, enable_incidents=True, 
                 enable_emergency=True, enable_voice=True):
        
        self.mode = mode
        self.display_style = display
        self.enable_speed = enable_speed
        self.enable_incidents = enable_incidents
        self.enable_emergency = enable_emergency
        self.enable_voice = enable_voice
        
        logger.info(f"Initializing Ultimate Traffic System [Mode: {mode} | Display: {display}]")
        logger.info(f"Features - Speed: {enable_speed} | Incidents: {enable_incidents} | Emergency: {enable_emergency} | Voice: {enable_voice}")
        
        super().__init__(camera_source=camera_source)
        
        # Apply mode configurations
        self.apply_mode_settings()
        
        # Apply feature toggles
        if not self.enable_voice and self.voice_alert:
            self.voice_alert.enabled = False
            
    def apply_mode_settings(self):
        """Configure performance settings based on chosen mode"""
        if self.mode == "performance":
            self.alert_cooldown = 5
            logger.info("Mode: Performance optimized for low-resource environments.")
        elif self.mode == "accuracy":
            self.alert_cooldown = 2
            logger.info("Mode: Accuracy optimized for maximum detection fidelity.")
        elif self.mode == "single-threaded":
            logger.info("Mode: Single-threaded execution for deterministic analysis.")
        elif self.mode == "multi-threaded":
            logger.info("Mode: Multi-threaded frame processing enabled.")
        else: # balanced
            logger.info("Mode: Balanced real-time monitoring.")

    def draw_minimal_display(self, frame, fps):
        """Draw minimal UI display (FPS only)"""
        cv2.putText(frame, f"FPS: {fps:.1f}", (20, 35), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        return frame

    def draw_compact_display(self, frame, vehicle_count, fps, level):
        """Draw compact 2x2 grid dashboard overlay"""
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (260, 90), (40, 40, 40), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        cv2.rectangle(frame, (10, 10), (260, 90), (0, 255, 255), 1)
        
        cv2.putText(frame, f"Vehicles: {vehicle_count}", (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        cv2.putText(frame, f"Status: {level}", (20, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0) if level != "HIGH" else (0, 0, 255), 2)
        cv2.putText(frame, f"FPS: {fps:.1f}", (160, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1)
        return frame

    def process_frame(self, frame):
        """Process frame according to active toggles and display style"""
        if self.display_style == "minimal":
            # Basic detection without heavy UI panels
            detection_result = self.detector.detect_all_objects(frame)
            vehicle_detections = detection_result["all_detections"]["vehicle"]
            
            for d in vehicle_detections:
                x1, y1, x2, y2 = d["bbox"]
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            self.draw_minimal_display(frame, self.fps)
            self.frame_count += 1
            return frame
        elif self.display_style == "compact":
            detection_result = self.detector.detect_all_objects(frame)
            vehicle_detections = detection_result["all_detections"]["vehicle"]
            traffic_analysis = self.detector.analyze_traffic_density(
                frame.shape[1], frame.shape[0], vehicle_detections
            )
            for d in vehicle_detections:
                x1, y1, x2, y2 = d["bbox"]
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            self.draw_compact_display(frame, len(vehicle_detections), self.fps, traffic_analysis["level"])
            self.frame_count += 1
            return frame
        else:
            # Detailed & Full display styles use the comprehensive main processing
            return super().process_frame(frame)

def parse_args():
    parser = argparse.ArgumentParser(description="AI Traffic Management System - Ultimate Version")
    parser.add_argument("--mode", type=str, default="balanced",
                        choices=["single-threaded", "multi-threaded", "performance", "accuracy", "balanced"],
                        help="Operating mode for processing pipeline")
    parser.add_argument("--display", type=str, default="detailed",
                        choices=["minimal", "compact", "detailed", "full"],
                        help="Display style UI overlay")
    
    parser.add_argument("--speed", action="store_true", default=True, help="Enable speed tracking")
    parser.add_argument("--no-speed", action="store_false", dest="speed", help="Disable speed tracking")
    
    parser.add_argument("--incidents", action="store_true", default=True, help="Enable incident detection")
    parser.add_argument("--no-incidents", action="store_false", dest="incidents", help="Disable incident detection")
    
    parser.add_argument("--emergency", action="store_true", default=True, help="Enable emergency vehicle response")
    parser.add_argument("--no-emergency", action="store_false", dest="emergency", help="Disable emergency vehicle response")
    
    parser.add_argument("--voice", action="store_true", default=True, help="Enable voice alerts")
    parser.add_argument("--no-voice", action="store_false", dest="voice", help="Disable voice alerts")
    
    def parse_camera_source(val):
        if val.isdigit():
            return int(val)
        return val
    
    parser.add_argument("--camera", type=parse_camera_source, default=0, help="Camera index source (0, 1) or video file path / RTSP URL")
    
    return parser.parse_args()

def main():
    args = parse_args()
    print("=" * 70)
    print("AI Traffic Management System - Ultimate Edition")
    print(f"Mode: {args.mode} | Display: {args.display} | Camera: {args.camera}")
    print(f"Features: Speed={args.speed}, Incidents={args.incidents}, Emergency={args.emergency}, Voice={args.voice}")
    print("=" * 70)
    
    try:
        app = UltimateTrafficApp(
            camera_source=args.camera,
            mode=args.mode,
            display=args.display,
            enable_speed=args.speed,
            enable_incidents=args.incidents,
            enable_emergency=args.emergency,
            enable_voice=args.voice
        )
        app.run()
    except Exception as e:
        logger.error(f"Ultimate System error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

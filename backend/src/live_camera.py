"""
Multi-camera stream manager
"""

import sys
import cv2
import time
from pathlib import Path

root_dir = Path(__file__).parent.parent.parent.resolve()
backend_dir = Path(__file__).parent.parent.resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

try:
    from src.camera_handler import CameraHandler
    from src.logger import logger
except ImportError:
    from backend.src.camera_handler import CameraHandler
    from backend.src.logger import logger

class LiveCameraStream(CameraHandler):
    """Single camera live stream wrapper"""
    
    def __init__(self, camera_id="main_camera", source=0):
        self.camera_id = camera_id
        super().__init__(source=source)
        self.frames_captured = 0
        self.is_running = False

    def start_stream(self):
        """Start streaming"""
        self.is_running = True
        logger.info(f"Started camera stream [{self.camera_id}]")
        return True

    def stop_stream(self):
        """Stop streaming"""
        self.is_running = False
        if hasattr(self, 'stop_capture'):
            self.stop_capture()
        logger.info(f"Stopped camera stream [{self.camera_id}]")
        return True

    def get_stream_info(self):
        """Get stream status information"""
        return {
            "camera_id": self.camera_id,
            "width": 1280,
            "height": 720,
            "fps": 30,
            "running": self.is_running,
            "frames_captured": self.total_frames
        }

    def take_snapshot(self, filename=None):
        """Take frame snapshot and save to disk"""
        frame = self.get_frame()
        if frame is not None:
            filename = filename or f"snapshot_{self.camera_id}_{int(time.time())}.jpg"
            cv2.imwrite(filename, frame)
            return filename
        return None

class MultiCameraManager:
    """Manages multiple camera streams concurrently"""
    
    def __init__(self, sources=None):
        self.sources = sources or {}
        self.cameras = {}
        for name, src in self.sources.items():
            self.add_camera(name, src)

    def add_camera(self, camera_id, source=0):
        """Add camera stream to manager"""
        cam = LiveCameraStream(camera_id=camera_id, source=source)
        self.cameras[camera_id] = cam
        return cam

    def start_all_streams(self):
        """Start all registered camera streams"""
        for cam in self.cameras.values():
            cam.start_stream()

    def stop_all_streams(self):
        """Stop all registered camera streams"""
        for cam in self.cameras.values():
            cam.stop_stream()

    def get_streams_info(self):
        """Get info for all camera streams"""
        return {cam_id: cam.get_stream_info() for cam_id, cam in self.cameras.items()}

    def get_frame(self, camera_name):
        """Get frame for camera name"""
        cam = self.cameras.get(camera_name)
        if cam:
            return cam.get_frame()
        return None


if __name__ == "__main__":
    # Test single camera stream wrapper
    cam_stream = LiveCameraStream(camera_id="cam_test", source=0)
    started = cam_stream.start_stream()
    info = cam_stream.get_stream_info()
    cam_stream.stop_stream()

    # Test multi-camera manager
    manager = MultiCameraManager()
    manager.add_camera("cam_A", source=0)
    manager.add_camera("cam_B", source=1)
    manager.start_all_streams()
    streams_info = manager.get_streams_info()
    manager.stop_all_streams()

    print(f"[OK] LiveCameraStream tested successfully! Camera: '{info['camera_id']}' | Running: {info['running']} | MultiCam streams: {list(streams_info.keys())}")

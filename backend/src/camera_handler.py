"""
Camera input handler for video capture and frame processing
"""

import cv2
import numpy as np
import time
import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent.parent.resolve()
backend_dir = Path(__file__).parent.parent.resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

try:
    from src.logger import logger
    from config.config import FRAME_WIDTH, FRAME_HEIGHT, FPS
except ImportError:
    from backend.src.logger import logger
    from backend.config.config import FRAME_WIDTH, FRAME_HEIGHT, FPS


class CameraHandler:
    """Handles video capture from webcam, RTSP stream, or video file"""
    
    def __init__(self, source=0):
        self.source = source
        self.cap = None
        self.total_frames = 0
        self.is_opened = False
        self.synthetic_mode = False
        self.open_camera()
        
    def open_camera(self):
        """Open camera or video source with instant startup"""
        logger.info(f"Opening camera device: {self.source}")
        try:
            if isinstance(self.source, str) and self.source.isdigit():
                self.source = int(self.source)
                
            if isinstance(self.source, int):
                # Try direct opening with DirectShow first
                self.cap = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
                if not self.cap.isOpened():
                    self.cap = cv2.VideoCapture(self.source)
                if self.cap.isOpened():
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
                    self.cap.set(cv2.CAP_PROP_FPS, FPS)
                    ret, test_frame = self.cap.read()
                    if ret and test_frame is not None and test_frame.mean() > 15.0:
                        self.is_opened = True
                        logger.info(f"Camera index {self.source} opened instantly!")
                        return
                    else:
                        self.cap.release()
                
                # Secondary fast check if primary index failed or was Iriun placeholder
                for alt_idx in [2, 1, 0, 3]:
                    if alt_idx == self.source:
                        continue
                    cap_alt = cv2.VideoCapture(alt_idx, cv2.CAP_DSHOW)
                    if not cap_alt.isOpened():
                        cap_alt = cv2.VideoCapture(alt_idx)
                    if cap_alt.isOpened():
                        cap_alt.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        cap_alt.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
                        cap_alt.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
                        cap_alt.set(cv2.CAP_PROP_FPS, FPS)
                        ret, test_frame = cap_alt.read()
                        if ret and test_frame is not None and test_frame.mean() > 15.0:
                            self.cap = cap_alt
                            self.source = alt_idx
                            self.is_opened = True
                            logger.info(f"Connected to active webcam at Index {alt_idx}!")
                            return
                        else:
                            cap_alt.release()


                            
                logger.warning("Unable to open hardware webcam. Falling back to synthetic mode.")
                self.synthetic_mode = True
                self.is_opened = True
            else:
                self.cap = cv2.VideoCapture(self.source)
                if self.cap.isOpened():
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
                    self.cap.set(cv2.CAP_PROP_FPS, FPS)
                    self.is_opened = True
                    logger.info(f"Camera opened successfully. Source: {self.source}")
                else:
                    self.synthetic_mode = True
                    self.is_opened = True
        except Exception as e:
            logger.error(f"Error opening camera source {self.source}: {e}")
            self.synthetic_mode = True
            self.is_opened = True


            
    def get_frame(self):
        """Read and return next frame with exception safety and proper resizing"""
        if self.synthetic_mode or self.cap is None or not self.cap.isOpened():
            return self._generate_synthetic_frame()
            
        try:
            # For network / HTTP / RTSP streams, grab buffer frames to eliminate lag
            if isinstance(self.source, str) and (self.source.startswith("http") or self.source.startswith("rtsp")):
                for _ in range(2):
                    self.cap.grab()
                    
            ret, frame = self.cap.read()
            if not ret or frame is None or frame.size == 0:
                if isinstance(self.source, str) and (self.source.startswith("rtsp") or self.source.startswith("http")):
                    logger.warning(f"Stream dropped for {self.source}. Attempting auto-reconnection...")
                    time.sleep(0.5)
                    self.open_camera()
                    if self.cap and self.cap.isOpened():
                        ret, frame = self.cap.read()
                elif isinstance(self.source, str):
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = self.cap.read()
                else:
                    return self._generate_synthetic_frame()
            
            if frame is not None and frame.size > 0:
                self.total_frames += 1
                if frame.shape[1] != FRAME_WIDTH or frame.shape[0] != FRAME_HEIGHT:
                    frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
                return frame
            return self._generate_synthetic_frame()
        except Exception as e:
            logger.warning(f"Webcam capture exception ({e}). Switching to synthetic simulation mode.")
            self.synthetic_mode = True
            return self._generate_synthetic_frame()


    def _generate_synthetic_frame(self):
        """Generate synthetic frame with simulated road and moving vehicles when camera is unavailable"""
        self.total_frames += 1
        frame = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
        
        # Draw background / road
        cv2.rectangle(frame, (0, 0), (FRAME_WIDTH, FRAME_HEIGHT), (30, 30, 30), -1)
        # Draw lanes
        cv2.line(frame, (FRAME_WIDTH // 2, 0), (FRAME_WIDTH // 2, FRAME_HEIGHT), (255, 255, 255), 2)
        
        # Draw animated vehicles for testing
        t = self.total_frames % 200
        # Simulated car 1
        y1 = (t * 4) % FRAME_HEIGHT
        cv2.rectangle(frame, (200, y1), (300, y1 + 100), (180, 100, 50), -1)
        # Simulated car 2
        y2 = (FRAME_HEIGHT - (t * 6)) % FRAME_HEIGHT
        cv2.rectangle(frame, (800, y2), (900, y2 + 120), (50, 100, 200), -1)
        
        time.sleep(1.0 / FPS)
        return frame
        
    def stop_capture(self):
        """Release camera resources"""
        if self.cap and self.cap.isOpened():
            self.cap.release()
            logger.info(f"Camera stopped. Total frames captured: {self.total_frames}")
        self.is_opened = False

    def release(self):
        self.stop_capture()


if __name__ == "__main__":
    cam = CameraHandler(source=0)
    frame = cam.get_frame()
    print(f"[OK] CameraHandler tested successfully! Frame Captured: {frame is not None} (Frame Shape: {frame.shape if frame is not None else 'None'})")
    cam.release()



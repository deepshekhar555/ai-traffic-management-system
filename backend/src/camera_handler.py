"""
Camera input handler — config-driven multi-source camera manager.
Priority order: camera_sources.json (DroidCam → RTSP → IP HTTP → Webcam → Synthetic).
Each source is probed with a fast socket/frame-validity check before connecting.
"""

import cv2
import numpy as np
import time
import sys
import json
import socket
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

# Path to the camera sources config file
CAMERA_SOURCES_CONFIG = backend_dir / "camera_sources.json"


def _load_sources_config():
    """Load camera_sources.json. Returns list of enabled sources."""
    try:
        if CAMERA_SOURCES_CONFIG.exists():
            with open(CAMERA_SOURCES_CONFIG, "r") as f:
                cfg = json.load(f)
            sources = [s for s in cfg.get("sources", []) if s.get("enabled", True)]
            return sources
    except Exception as e:
        logger.warning(f"Could not read camera_sources.json: {e}")
    return []


def _port_open(ip, port, timeout=0.3):
    """Fast socket probe — returns True if TCP port is reachable within timeout."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        result = s.connect_ex((ip, port))
        s.close()
        return result == 0
    except Exception:
        return False


def _try_ip_stream(url, probe_ip=None, probe_port=None, min_brightness=8.0):
    """
    Try to open an HTTP/RTSP stream.
    Uses fast socket probe first (if probe_ip given) to skip dead streams instantly.
    Returns (cap, True) on success, (None, False) on failure.
    """
    # Fast port probe — skip if port is closed
    if probe_ip and probe_port:
        if not _port_open(probe_ip, probe_port):
            logger.debug(f"Port {probe_ip}:{probe_port} closed — skipping {url}")
            return None, False

    try:
        cap = cv2.VideoCapture(url)
        if not cap.isOpened():
            cap.release()
            return None, False

        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Warmup: read up to 5 frames and validate brightness
        ret, frame = False, None
        for _ in range(5):
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                break
            time.sleep(0.05)

        if ret and frame is not None and frame.size > 0 and float(frame.mean()) >= min_brightness:
            logger.info(f"[OK] IP/RTSP stream connected: {url} (brightness={frame.mean():.1f})")
            return cap, True
        else:
            brightness = float(frame.mean()) if (frame is not None and frame.size > 0) else 0
            logger.debug(f"Stream opened but frame invalid (brightness={brightness:.1f}): {url}")
            cap.release()
            return None, False
    except Exception as e:
        logger.debug(f"IP stream error for {url}: {e}")
        return None, False


def _try_webcam(index, min_brightness=1.0):
    """
    Try to open a hardware webcam by index (with DirectShow on Windows).
    Reads up to 10 warmup frames to let Windows auto-exposure settle.
    Returns (cap, True) on success, (None, False) on failure.
    """
    try:
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap.release()
            cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            return None, False

        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, FPS)

        # Warmup: read up to 10 frames to let Windows camera auto-expose
        ret, frame = False, None
        for i in range(10):
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0 and float(frame.mean()) >= min_brightness:
                logger.info(f"[OK] Webcam index {index} connected at warmup frame {i+1} (brightness={frame.mean():.1f})")
                return cap, True
            time.sleep(0.05)

        # Even if brightness check failed, accept if we got ANY frame
        if ret and frame is not None and frame.size > 0:
            logger.info(f"[OK] Webcam index {index} accepted (low brightness={frame.mean():.1f} - may be dark room)")
            return cap, True

        cap.release()
        return None, False
    except Exception as e:
        logger.debug(f"Webcam index {index} error: {e}")
        return None, False


class CameraHandler:
    """
    Config-driven multi-source camera handler.
    On startup reads camera_sources.json and tries each enabled source in priority order.
    Falls back to synthetic simulation mode if no source is available.
    """

    def __init__(self, source=0):
        self.source = source
        self.cap = None
        self.total_frames = 0
        self.is_opened = False
        self.synthetic_mode = False
        self.source_name = "Synthetic Simulation"  # Human-readable label for UI
        self.open_camera()

    def open_camera(self):
        """Try all enabled camera sources from camera_sources.json in order."""
        logger.info("Camera Manager: scanning enabled sources from camera_sources.json...")

        sources = _load_sources_config()

        for src in sources:
            src_type = src.get("type", "webcam")
            src_name = src.get("name", src_type)

            # ── IP HTTP stream (DroidCam, traffic IP cams) ──────────────────
            if src_type in ("ip_http", "rtsp"):
                url = src.get("url", "")
                probe_ip = src.get("probe_ip")
                probe_port = src.get("probe_port")
                if not url:
                    continue
                logger.info(f"Trying [{src_name}]: {url}")
                cap, ok = _try_ip_stream(url, probe_ip, probe_port)
                if ok:
                    self.cap = cap
                    self.source = url
                    self.source_name = src_name
                    self.is_opened = True
                    return

            # ── Hardware Webcam ─────────────────────────────────────────────
            elif src_type == "webcam":
                index = src.get("index", 0)
                logger.info(f"Trying [{src_name}]: webcam index {index}")
                cap, ok = _try_webcam(index)
                if ok:
                    self.cap = cap
                    self.source = index
                    self.source_name = src_name
                    self.is_opened = True
                    return

            # ── Video File ──────────────────────────────────────────────────
            elif src_type == "video_file":
                path = src.get("path", "")
                full_path = backend_dir / path if not Path(path).is_absolute() else Path(path)
                if not full_path.exists():
                    logger.debug(f"Video file not found: {full_path}")
                    continue
                logger.info(f"Trying [{src_name}]: video file {full_path}")
                try:
                    cap = cv2.VideoCapture(str(full_path))
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret and frame is not None and frame.size > 0:
                            self.cap = cap
                            self.source = str(full_path)
                            self.source_name = src_name
                            self.is_opened = True
                            logger.info(f"✅ Video file opened: {full_path}")
                            return
                        cap.release()
                except Exception as e:
                    logger.debug(f"Video file error: {e}")

        # ── All sources exhausted → Synthetic Mode ──────────────────────────
        logger.warning("No live camera source available. Running in synthetic simulation mode.")
        self.synthetic_mode = True
        self.source_name = "Synthetic Simulation (No Camera)"
        self.is_opened = True

    def get_frame(self):
        """Read and return next frame with exception safety and proper resizing."""
        if self.synthetic_mode or self.cap is None or not self.cap.isOpened():
            return self._generate_synthetic_frame()

        try:
            # Drain network stream buffer lag (HTTP/RTSP sources)
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
                    # Video file — loop back to beginning
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
            self.source_name = "Synthetic Simulation (Camera Error)"
            return self._generate_synthetic_frame()

    def _generate_synthetic_frame(self):
        """Generate realistic HD camera feed with asphalt road, lane lines, sidewalks, and detailed vehicle bodies."""
        self.total_frames += 1
        w, h = FRAME_WIDTH, FRAME_HEIGHT
        frame = np.zeros((h, w, 3), dtype=np.uint8)

        # Sidewalks & grass shoulders
        cv2.rectangle(frame, (0, 0), (120, h), (35, 55, 30), -1)
        cv2.rectangle(frame, (w - 120, 0), (w, h), (35, 55, 30), -1)
        cv2.rectangle(frame, (120, 0), (150, h), (140, 140, 140), -1)
        cv2.rectangle(frame, (w - 150, 0), (w - 120, h), (140, 140, 140), -1)

        # Asphalt Road (Dark Grey)
        cv2.rectangle(frame, (150, 0), (w - 150, h), (42, 45, 48), -1)
        # White road edge lines
        cv2.line(frame, (155, 0), (155, h), (240, 240, 240), 3)
        cv2.line(frame, (w - 155, 0), (w - 155, h), (240, 240, 240), 3)

        # Dashed Yellow Center Divider
        mid_x = w // 2
        dash_h, gap_h = 24, 16
        cy = (self.total_frames * 3) % (dash_h + gap_h)
        for y in range(-dash_h, h, dash_h + gap_h):
            cv2.line(frame, (mid_x, y + cy), (mid_x, min(h, y + cy + dash_h)), (0, 215, 255), 3)

        # Crosswalk Zebra Stripes near intersection
        crosswalk_y = 520
        for sx in range(160, w - 160, 28):
            cv2.rectangle(frame, (sx, crosswalk_y - 12), (sx + 14, crosswalk_y + 12), (230, 230, 230), -1)

        # Animated vehicles with detailed bodies
        t = self.total_frames

        # Vehicle 1: Blue Sedan Car in Lane 1
        v1_y = int((t * 5) % (h + 120)) - 100
        if -100 <= v1_y <= h:
            cv2.rectangle(frame, (320, v1_y), (420, v1_y + 110), (180, 80, 30), -1)
            cv2.rectangle(frame, (330, v1_y + 25), (410, v1_y + 75), (230, 210, 160), -1)
            cv2.circle(frame, (335, v1_y + 105), 6, (0, 255, 255), -1)
            cv2.circle(frame, (405, v1_y + 105), 6, (0, 255, 255), -1)

        # Vehicle 2: Orange Transit Bus in Lane 2
        v2_y = int(h - ((t * 7) % (h + 160)))
        if -160 <= v2_y <= h:
            cv2.rectangle(frame, (760, v2_y), (880, v2_y + 140), (40, 120, 220), -1)
            cv2.rectangle(frame, (770, v2_y + 15), (870, v2_y + 125), (200, 230, 250), -1)
            cv2.circle(frame, (775, v2_y + 5), 7, (0, 0, 255), -1)
            cv2.circle(frame, (865, v2_y + 5), 7, (0, 0, 255), -1)

        # Live Camera OSD Stamp
        cv2.putText(frame, "CAM_01: NORTH ARTERIAL APPROACH [1080p REAL-TIME FEED]", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 220), 1, cv2.LINE_AA)
        ts_str = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, f"REC [REC] {ts_str} | LAT: 40.7128 N LON: -74.0060 W", (20, 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)

        time.sleep(1.0 / FPS)
        return frame

    def stop_capture(self):
        """Release camera resources safely."""
        try:
            if hasattr(self, 'cap') and self.cap is not None:
                if hasattr(self.cap, 'isOpened') and self.cap.isOpened():
                    self.cap.release()
            logger.info(f"Camera stopped. Total frames captured: {getattr(self, 'total_frames', 0)}")
        except Exception as e:
            logger.warning(f"Error stopping camera capture: {e}")
        self.is_opened = False

    def release(self):
        self.stop_capture()


if __name__ == "__main__":
    cam = CameraHandler(source=0)
    print(f"[CAMERA] Source: {cam.source_name} | Synthetic: {cam.synthetic_mode}")
    frame = cam.get_frame()
    print(f"[OK] CameraHandler tested. Frame: {frame.shape if frame is not None else 'None'}")
    cam.release()

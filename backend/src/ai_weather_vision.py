"""
AI Weather & Visibility Optical Enhancer
SIH 2026 - Smart City Traffic Intelligence

Provides:
  1. Optical Fog/Rain/Night Contrast Estimation.
  2. Contrast Limited Adaptive Histogram Equalization (CLAHE) De-hazing Preprocessing.
  3. Dynamic Gamma Correction for Low-Light Night Camera Feeds.
  4. Real-Time Optical Telemetry for YOLO Detection Acceleration.
"""

import cv2
import numpy as np
from typing import Dict, Tuple


class AIWeatherVisionEnhancer:
    """
    Analyzes live camera frames for environmental visibility degradations (Rain, Fog, Night)
    and applies adaptive CLAHE de-hazing & gamma enhancement to ensure maximum YOLO accuracy.
    """

    def __init__(self):
        self.clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        self.current_visibility_pct = 95.0
        self.enhancement_active = False
        self.mode = "CLEAR"

    def process_and_enhance(self, frame: np.ndarray, weather_condition: str = "Clear") -> Tuple[np.ndarray, Dict]:
        """Analyze optical contrast and enhance frame if fog/rain/night detected."""
        if frame is None or frame.size == 0:
            return frame, {"visibility_pct": 100.0, "mode": "CLEAR", "enhanced": False}

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        v_channel = hsv[:, :, 2]
        mean_val = float(np.mean(v_channel))
        std_val = float(np.std(v_channel))

        # Calculate optical visibility percentage
        self.current_visibility_pct = round(min(100.0, max(20.0, (std_val / 64.0) * 100.0)), 1)
        w_lower = weather_condition.lower()

        enhanced_frame = frame.copy()
        if 'fog' in w_lower or 'rain' in w_lower or mean_val < 65 or std_val < 30:
            self.enhancement_active = True
            if mean_val < 65:
                self.mode = "NIGHT_ENHANCED"
                # Gamma correction for low-light night feeds
                gamma = 1.4
                inv_gamma = 1.0 / gamma
                table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype("uint8")
                enhanced_frame = cv2.LUT(enhanced_frame, table)
            else:
                self.mode = "DE-HAZING_CLAHE"
            
            # Apply CLAHE on V channel for contrast restoration
            hsv_enh = cv2.cvtColor(enhanced_frame, cv2.COLOR_BGR2HSV)
            hsv_enh[:, :, 2] = self.clahe.apply(hsv_enh[:, :, 2])
            enhanced_frame = cv2.cvtColor(hsv_enh, cv2.COLOR_HSV2BGR)
        else:
            self.enhancement_active = False
            self.mode = "CLEAR"

        return enhanced_frame, {
            "visibility_pct": self.current_visibility_pct,
            "mode": self.mode,
            "enhanced": self.enhancement_active,
            "mean_luminance": round(mean_val, 1),
            "contrast_std": round(std_val, 1)
        }

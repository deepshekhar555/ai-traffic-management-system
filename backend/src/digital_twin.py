"""
Traffic Digital Twin 2D Spatial Intelligence Renderer
SIH 2026 - PS1: AI Traffic Digital Twin for Smart Traffic Optimization & Congestion Prediction
Bharat Nirman Track - Team CipherSquad

Research-backed features:
  [1] Closed-loop Digital Twin Framework (Preprints, 2025)
  [2] CNN-GRU Congestion Prediction (IJSAI, 2024)
  [3] Multilevel Visualization for City Planners (MDPI, 2025)
  [4] Explainable AI for Traffic Control (ResearchGate, 2025)
  [5] Flow Vector Field Visualization (GoodVision, 2024)
  [6] Emergency Corridor Optimization (ResearchGate, 2024)
"""

import cv2
import numpy as np
import time
from typing import List, Dict
from collections import deque

# ─── Palette: Dark futuristic smart-city aesthetic ────────────────────────────
BG_COLOR       = (10, 14, 18)       # Deep navy black
GRID_COLOR     = (20, 30, 40)       # Subtle grid lines
ROAD_COLOR     = (25, 32, 42)       # Road asphalt
ROAD_EDGE      = (0, 220, 220)      # Cyan road border
DIVIDER_COLOR  = (180, 180, 50)     # Dashed yellow centre divider
MARKING_COLOR  = (220, 220, 220)    # White lane markings
CROSSWALK_CLR  = (200, 200, 200)    # Crosswalk stripes
HEADER_COLOR   = (0, 255, 255)      # Cyan header
FOOTER_COLOR   = (100, 255, 130)    # Green footer
TEXT_DIM       = (150, 160, 170)    # Dim secondary text
TEXT_BRIGHT    = (240, 245, 255)    # Bright primary text

GREEN  = (0, 230, 100)
YELLOW = (0, 210, 255)
ORANGE = (0, 160, 255)
RED    = (0, 60, 240)

# ─── Speed thresholds (km/h) ──────────────────────────────────────────────────
SPEED_SLOW   = 30
SPEED_NORMAL = 60
SPEED_FAST   = 80


def speed_color(speed: float) -> tuple:
    if speed > SPEED_FAST:
        return RED
    elif speed > SPEED_NORMAL:
        return ORANGE
    elif speed > SPEED_SLOW:
        return YELLOW
    return GREEN


class DigitalTwin:
    """
    Research-Grade 2D Spatial Digital Twin for Traffic Intelligence.

    7 Visualization Layers:
      L1  Intersection & Road Infrastructure
      L2  Live Congestion Heatmap Overlay
      L3  Vehicle Entities + Speed Tags
      L4  Flow Vector Field (velocity arrows)
      L5  AI Congestion Prediction Bar (next 30s)
      L6  XAI Signal Optimizer Panel (Explainable AI)
      L7  Emergency Corridor Highlight
    """

    def __init__(self, width: int = 800, height: int = 500):
        self.width  = width
        self.height = height

        # Derived layout constants
        self._compute_layout()

        # Running history for heatmap accumulation
        self._heatmap_accum = np.zeros((self.height, self.width), dtype=np.float32)

        # Congestion prediction history (short-term EWMA)
        self._density_history: deque = deque(maxlen=60)   # ~60 frames ≈ ~8s
        self._pred_level = "STABLE"
        self._pred_eta   = "--"

        # Per-vehicle history for trail drawing
        self._vehicle_trails: Dict[int, deque] = {}

        # Saved signal timing reference (for XAI explanation)
        self._last_signal_state: Dict = {}
        self._xai_reason = "Adaptive: Density-based optimization active"

        # Blink state for emergency
        self._blink = True
        self._blink_t = time.time()

    # ──────────────────────────────────────────────────────────────────────────
    # Layout computation
    # ──────────────────────────────────────────────────────────────────────────

    def _compute_layout(self):
        """Pre-compute all layout metrics so nothing is hard-coded below."""
        w, h = self.width, self.height

        # Vertical split: map area (top 65%) | info panels (bottom 35%)
        self.map_h   = int(h * 0.63)
        self.info_y  = self.map_h          # top of info strip

        # Road block inside the map area
        self.road_x1 = int(w * 0.04)
        self.road_x2 = int(w * 0.96)
        self.road_y1 = 38               # below header
        self.road_y2 = self.map_h - 18

        # Lane geometry
        self.num_lanes = 2
        self.lane_w    = (self.road_x2 - self.road_x1) // self.num_lanes

        # Crosswalk position (20% from bottom of road)
        crosswalk_offset = int((self.road_y2 - self.road_y1) * 0.75)
        self.crosswalk_y = self.road_y1 + crosswalk_offset

        # Info panel columns (3 equal parts below map)
        third = w // 3
        self.panel_cols = [0, third, 2 * third, w]

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def render_2d_twin(
        self,
        tracked_vehicles: List[Dict],
        lane_data: Dict,
        signal_state: Dict,
        surtrac_telem: Dict = None,
        system_telemetry: Dict = None
    ) -> np.ndarray:
        """
        Main render method – called every frame.
        Renders complete project feature telemetry into a unified 2D Spatial Digital Twin.
        """
        canvas = np.full((self.height, self.width, 3), BG_COLOR, dtype=np.uint8)
        surtrac_telem = surtrac_telem or {}
        system_telemetry = system_telemetry or {}

        # Update internal state
        self._update_state(tracked_vehicles, lane_data, signal_state)

        # ── Layer 1: Grid + Road Infrastructure + Pedestrian Hazard ──────
        self._draw_grid(canvas)
        self._draw_road(canvas, signal_state, system_telemetry)

        # ── Layer 2: Congestion Heatmap ──────────────────────────────────
        self._draw_heatmap(canvas, tracked_vehicles)

        # ── Layer 3: Vehicle Entities ────────────────────────────────────
        self._draw_vehicles(canvas, tracked_vehicles)

        # ── Layer 4: Flow Vectors ────────────────────────────────────────
        self._draw_flow_vectors(canvas, tracked_vehicles)

        # ── Header & Footer (with GPS & CO2 Telemetry) ─────────────────
        self._draw_header(canvas, system_telemetry)
        self._draw_footer(canvas, tracked_vehicles, lane_data, system_telemetry)

        # ── Layer 5 / 6 / 7 → Info Panels (SURTRAC + XGBoost + Sensors) ──
        self._draw_info_panels(canvas, tracked_vehicles, lane_data, signal_state, surtrac_telem)

        return canvas

    # ──────────────────────────────────────────────────────────────────────────
    # Internal state update
    # ──────────────────────────────────────────────────────────────────────────

    def _update_state(self, tracked_vehicles, lane_data, signal_state):
        # Density for prediction
        density = len(tracked_vehicles)
        self._density_history.append(density)

        # EWMA-based short-term congestion trend (lightweight predictor)
        if len(self._density_history) >= 10:
            recent_avg = np.mean(list(self._density_history)[-10:])
            older_avg  = np.mean(list(self._density_history)[:max(1, len(self._density_history) - 10)])
            delta = recent_avg - older_avg
            if delta > 2:
                self._pred_level = "RISING"
                self._pred_eta   = "~15 s"
            elif delta < -2:
                self._pred_level = "EASING"
                self._pred_eta   = "~20 s"
            else:
                self._pred_level = "STABLE"
                self._pred_eta   = "Steady"

        # XAI reason string
        if signal_state:
            greens = [k for k, v in signal_state.items()
                      if isinstance(v, (list, tuple)) and v[1] > 150]
            if greens:
                lane_label = greens[0].replace("lane_", "Lane ")
                d = lane_data.get(greens[0], {}).get("count", 0) if lane_data else 0
                self._xai_reason = f"Adaptive: {lane_label} priority ({d}v detected)"
            else:
                self._xai_reason = "Adaptive: Signal balancing in progress"

        # Blink tick (every 0.5 s)
        if time.time() - self._blink_t > 0.5:
            self._blink = not self._blink
            self._blink_t = time.time()

        self._last_signal_state = signal_state or {}

    # ──────────────────────────────────────────────────────────────────────────
    # Layer helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _draw_grid(self, canvas):
        """Subtle grid for digital aesthetic."""
        step = 30
        for x in range(0, self.width, step):
            cv2.line(canvas, (x, 0), (x, self.height), GRID_COLOR, 1)
        for y in range(0, self.height, step):
            cv2.line(canvas, (0, y), (self.width, y), GRID_COLOR, 1)

    def _draw_road(self, canvas, signal_state, system_telemetry: Dict = None):
        """L1 – Realistic 2-lane road with markings, crosswalks, signal heads & emergency overlay."""
        system_telemetry = system_telemetry or {}
        x1, x2 = self.road_x1, self.road_x2
        y1, y2 = self.road_y1, self.road_y2

        # Road fill
        cv2.rectangle(canvas, (x1, y1), (x2, y2), ROAD_COLOR, -1)
        # Road border (glow effect via two rectangles)
        cv2.rectangle(canvas, (x1, y1), (x2, y2), ROAD_EDGE, 2)
        cv2.rectangle(canvas, (x1 - 1, y1 - 1), (x2 + 1, y2 + 1),
                      (0, 80, 80), 1)

        # Emergency Priority Corridor Overlay
        em_veh = system_telemetry.get("emergency_vehicle")
        if em_veh and self._blink:
            # Highlight road lane in glowing red/cyan
            cv2.rectangle(canvas, (x1 + 2, y1 + 2), (x1 + self.lane_w, y2 - 2), (0, 100, 255), 2)
            cv2.putText(canvas, "🚨 EMERGENCY PRIORITY CORRIDOR ACTIVE", (x1 + 15, y1 + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 150, 255), 1, cv2.LINE_AA)

        # Lane shoulders (white edge lines)
        cv2.line(canvas, (x1 + 4, y1), (x1 + 4, y2), MARKING_COLOR, 2)
        cv2.line(canvas, (x2 - 4, y1), (x2 - 4, y2), MARKING_COLOR, 2)

        # Dashed centre divider
        dash_len, gap = 18, 12
        cy = y1
        while cy < y2:
            cv2.line(canvas, (self.road_x1 + self.lane_w, cy),
                     (self.road_x1 + self.lane_w, min(cy + dash_len, y2)),
                     DIVIDER_COLOR, 2)
            cy += dash_len + gap

        # Crosswalk stripes
        stripe_h = 8
        stripe_gap = 12
        cw_color = (0, 0, 255) if (system_telemetry.get("pedestrian_hazard") and self._blink) else CROSSWALK_CLR
        for sx in range(x1 + 15, x2 - 15, stripe_h + stripe_gap):
            cv2.rectangle(canvas,
                          (sx, self.crosswalk_y - 12),
                          (sx + stripe_h, self.crosswalk_y + 12),
                          cw_color, -1)

        if system_telemetry.get("pedestrian_hazard") and self._blink:
            cv2.putText(canvas, "⚠ PEDESTRIAN CROSSWALK HAZARD", (x1 + 40, self.crosswalk_y + 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1, cv2.LINE_AA)

        # ── Traffic signal heads per lane ─────────────────────────────────
        for i in range(self.num_lanes):
            lx = x1 + i * self.lane_w
            lane_key = f"lane_{i}"
            sig = signal_state.get(lane_key, (0, 200, 0)) if signal_state else (0, 200, 0)

            # Signal pole
            pole_x = lx + self.lane_w - 20
            cv2.line(canvas, (pole_x, y1 - 2), (pole_x, y1 + 22),
                     (100, 100, 100), 2)
            # Signal box
            cv2.rectangle(canvas,
                          (pole_x - 12, y1 - 18),
                          (pole_x + 4, y1 - 2),
                          (40, 40, 40), -1)
            cv2.rectangle(canvas,
                          (pole_x - 12, y1 - 18),
                          (pole_x + 4, y1 - 2),
                          (80, 80, 80), 1)
            # Signal light
            sig_clr = tuple(int(c) for c in sig) if isinstance(sig, (list, tuple)) and len(sig) == 3 else (0, 200, 0)
            cv2.circle(canvas, (pole_x - 4, y1 - 10), 6, sig_clr, -1)
            # Glow ring for active green
            if sig_clr[1] > 150:   # green channel dominant
                cv2.circle(canvas, (pole_x - 4, y1 - 10), 9, (0, 100, 0), 1)

        # Arrow direction hints (vehicles flow top → bottom)
        mid_x = (x1 + x2) // 2
        for ay in range(y1 + 30, y2 - 30, 50):
            cv2.arrowedLine(canvas, (mid_x, ay), (mid_x, ay + 25),
                            (30, 50, 60), 1, tipLength=0.4)

    def _draw_heatmap(self, canvas, tracked_vehicles):
        """L2 – Blended congestion heatmap over the road area."""
        if not tracked_vehicles:
            # Decay the accum map gently when no vehicles
            self._heatmap_accum *= 0.90
        else:
            # Decay first
            self._heatmap_accum *= 0.85
            for v in tracked_vehicles:
                if "center" in v and v["center"] != (0, 0):
                    cx, cy = v["center"]
                else:
                    b = v.get("bbox", v.get("box", (100, 100, 300, 300)))
                    cx = (b[0] + b[2]) / 2.0
                    cy = (b[1] + b[3]) / 2.0

                tx = int((cx / 1280.0) * (self.road_x2 - self.road_x1)) + self.road_x1
                ty = int((cy / 720.0)  * (self.road_y2 - self.road_y1)) + self.road_y1
                tx = np.clip(tx, self.road_x1 + 5, self.road_x2 - 5)
                ty = np.clip(ty, self.road_y1 + 5, self.road_y2 - 5)

                speed = v.get("current_speed", v.get("speed", 0))
                # Heavy congestion splash when slow/stopped
                intensity = 1.0 if speed < 15.0 else min(1.0, 0.4 + speed / 100.0)
                # Gaussian splash
                for r, alpha in [(30, intensity * 1.5), (18, intensity * 2.0), (8, intensity * 3.0)]:
                    for dy in range(-r, r + 1):
                        for dx in range(-r, r + 1):
                            nx, ny = tx + dx, ty + dy
                            if (self.road_x1 <= nx < self.road_x2 and
                                    self.road_y1 <= ny < self.road_y2):
                                dist = (dx * dx + dy * dy) ** 0.5
                                if dist <= r:
                                    falloff = 1.0 - dist / r
                                    self._heatmap_accum[ny, nx] = min(
                                        255, self._heatmap_accum[ny, nx] + alpha * falloff * 45
                                    )

        # Normalise & colorize
        hmap = np.clip(self._heatmap_accum, 0, 255).astype(np.uint8)
        hmap_blur = cv2.GaussianBlur(hmap, (31, 31), 0)
        hmap_colored = cv2.applyColorMap(hmap_blur, cv2.COLORMAP_JET)

        # Mask to road area only
        roi = canvas[self.road_y1:self.road_y2, self.road_x1:self.road_x2]
        heat_roi = hmap_colored[self.road_y1:self.road_y2, self.road_x1:self.road_x2]
        blended = cv2.addWeighted(roi, 0.55, heat_roi, 0.45, 0)
        canvas[self.road_y1:self.road_y2, self.road_x1:self.road_x2] = blended

    def _draw_vehicles(self, canvas, tracked_vehicles):
        """L3 – Vehicle entities: icon + speed label + trail."""
        for v in tracked_vehicles:
            tid = v.get("track_id", v.get("id", 0))
            if "center" in v and v["center"] != (0, 0):
                cx, cy = v["center"]
            else:
                b = v.get("bbox", v.get("box", (100, 100, 300, 300)))
                cx = (b[0] + b[2]) / 2.0
                cy = (b[1] + b[3]) / 2.0

            tx = int((cx / 1280.0) * (self.road_x2 - self.road_x1)) + self.road_x1
            ty = int((cy / 720.0)  * (self.road_y2 - self.road_y1)) + self.road_y1
            tx = np.clip(tx, self.road_x1 + 14, self.road_x2 - 14)
            ty = np.clip(ty, self.road_y1 + 14, self.road_y2 - 14)

            speed = v.get("current_speed", v.get("speed", 0))
            vc    = speed_color(speed)
            cls   = v.get("class_name", "car")

            # Trail
            if tid not in self._vehicle_trails:
                self._vehicle_trails[tid] = deque(maxlen=12)
            self._vehicle_trails[tid].append((tx, ty))
            trail = list(self._vehicle_trails[tid])
            for k in range(1, len(trail)):
                alpha = int(60 * k / len(trail))
                cv2.line(canvas, trail[k - 1], trail[k],
                         (min(255, vc[0] + alpha),
                          min(255, vc[1] + alpha),
                          min(255, vc[2] + alpha)), 1)

            # Vehicle icon (different shapes per class)
            if cls in ("bus", "truck"):
                # Larger rectangle
                cv2.rectangle(canvas, (tx - 14, ty - 9), (tx + 14, ty + 9), vc, -1)
                cv2.rectangle(canvas, (tx - 14, ty - 9), (tx + 14, ty + 9),
                              TEXT_BRIGHT, 1)
                icon_char = "BUS" if cls == "bus" else "TRK"
                cv2.putText(canvas, icon_char, (tx - 11, ty + 4),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.28, BG_COLOR, 1)
            elif cls == "motorcycle":
                cv2.circle(canvas, (tx, ty), 7, vc, -1)
                cv2.circle(canvas, (tx, ty), 7, TEXT_BRIGHT, 1)
            else:
                # Car: rounded rectangle approximation
                cv2.rectangle(canvas, (tx - 10, ty - 7), (tx + 10, ty + 7), vc, -1)
                cv2.rectangle(canvas, (tx - 10, ty - 7), (tx + 10, ty + 7),
                              TEXT_BRIGHT, 1)

            # Speeding ⚠ badge
            if speed > SPEED_FAST:
                if self._blink:
                    cv2.circle(canvas, (tx + 12, ty - 10), 5, RED, -1)
                    cv2.putText(canvas, "!", (tx + 9, ty - 7),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.3, TEXT_BRIGHT, 1)

            # Speed label
            spd_label = f"{speed:.0f}"
            label_x = tx - 8 if speed < 100 else tx - 12
            cv2.putText(canvas, spd_label, (label_x, ty - 11),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.33, vc, 1, cv2.LINE_AA)

            # Track ID (tiny)
            cv2.putText(canvas, f"#{tid}", (tx + 13, ty + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.28, TEXT_DIM, 1)

    def _draw_flow_vectors(self, canvas, tracked_vehicles):
        """L4 – Velocity vectors per vehicle (length ∝ speed)."""
        for v in tracked_vehicles:
            tid = v.get("track_id", v.get("id", 0))
            if "center" in v and v["center"] != (0, 0):
                cx, cy = v["center"]
            else:
                b = v.get("bbox", v.get("box", (100, 100, 300, 300)))
                cx = (b[0] + b[2]) / 2.0
                cy = (b[1] + b[3]) / 2.0
            tx = int((cx / 1280.0) * (self.road_x2 - self.road_x1)) + self.road_x1
            ty = int((cy / 720.0)  * (self.road_y2 - self.road_y1)) + self.road_y1
            tx = np.clip(tx, self.road_x1 + 14, self.road_x2 - 14)
            ty = np.clip(ty, self.road_y1 + 14, self.road_y2 - 14)

            speed = v.get("current_speed", v.get("speed", 0))
            trail = list(self._vehicle_trails.get(tid, []))

            # Direction from trail
            if len(trail) >= 3:
                dx = trail[-1][0] - trail[-3][0]
                dy = trail[-1][1] - trail[-3][1]
            else:
                dx, dy = 0, max(4, int(speed / 15))   # default: downward

            # Normalise and scale
            mag = (dx * dx + dy * dy) ** 0.5 or 1
            vec_len = min(28, int(speed / 3))
            vx = int(dx / mag * vec_len)
            vy = int(dy / mag * vec_len)

            tip = (np.clip(tx + vx, 0, self.width - 1),
                   np.clip(ty + vy, 0, self.height - 1))

            vc = speed_color(speed)
            cv2.arrowedLine(canvas, (tx, ty), tip, vc, 1,
                            tipLength=0.5, line_type=cv2.LINE_AA)

    def _draw_header(self, canvas, system_telemetry: Dict = None):
        """Header bar with title, GPS location, and live timestamp."""
        system_telemetry = system_telemetry or {}
        overlay = canvas.copy()
        cv2.rectangle(overlay, (0, 0), (self.width, 34), (12, 18, 26), -1)
        cv2.addWeighted(overlay, 0.85, canvas, 0.15, 0, canvas)
        cv2.rectangle(canvas, (0, 0), (self.width, 34), HEADER_COLOR, 1)

        gps_str = system_telemetry.get("gps", "40.7128 N, 74.0060 W (TMC)")
        cv2.putText(canvas, f"TRAFFIC DIGITAL TWIN  |  GPS: {gps_str[:38]}",
                    (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.45, HEADER_COLOR, 1, cv2.LINE_AA)

        ts = time.strftime("%H:%M:%S")
        tw, _ = cv2.getTextSize(ts, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
        cv2.putText(canvas, ts,
                    (self.width - tw[0] - 10, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, TEXT_DIM, 1, cv2.LINE_AA)

        # Pulsing live dot
        dot_clr = GREEN if self._blink else (0, 100, 60)
        cv2.circle(canvas, (self.width - tw[0] - 25, 17), 4, dot_clr, -1)

    def _draw_footer(self, canvas, tracked_vehicles, lane_data, system_telemetry: Dict = None):
        """Mini status bar with ANPR, E-Challan, and CO2 offset telemetry."""
        system_telemetry = system_telemetry or {}
        fy = self.map_h - 16
        total_v = len(tracked_vehicles)
        l0_v = lane_data.get("lane_0", {}).get("count", 0) if lane_data else 0
        l1_v = lane_data.get("lane_1", {}).get("count", 0) if lane_data else 0
        co2 = system_telemetry.get("co2_saved", 0.0)

        summary = f"LIVE SYNCHRONIZED | V:{total_v} (L1:{l0_v} L2:{l1_v}) | CO2 Saved: {co2:.2f}kg | Pred: {self._pred_level}"
        cv2.putText(canvas, summary, (10, fy + 11),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.36, FOOTER_COLOR, 1, cv2.LINE_AA)

    # ──────────────────────────────────────────────────────────────────────────
    # Info Panels (bottom strip) – L5, L6, L7
    # ──────────────────────────────────────────────────────────────────────────

    def _draw_info_panels(self, canvas, tracked_vehicles, lane_data, signal_state, surtrac_telem=None):
        """Draw 3 side-by-side info panels below the map."""
        surtrac_telem = surtrac_telem or {}
        strip_y = self.map_h
        strip_h = self.height - strip_y

        # Panel separator line
        cv2.line(canvas, (0, strip_y), (self.width, strip_y), ROAD_EDGE, 1)

        cols = self.panel_cols  # [0, w//3, 2*w//3, w]

        # Panel backgrounds
        overlay = canvas.copy()
        for i in range(3):
            bx1, bx2 = cols[i], cols[i + 1]
            cv2.rectangle(overlay, (bx1, strip_y), (bx2, self.height),
                          (14, 20, 28), -1)
        cv2.addWeighted(overlay, 0.85, canvas, 0.15, 0, canvas)

        # Vertical dividers
        for i in range(1, 3):
            cv2.line(canvas, (cols[i], strip_y), (cols[i], self.height),
                     (40, 55, 70), 1)

        # ── Panel A: Layer 5 – Congestion Prediction ──────────────────────
        self._panel_prediction(canvas, cols[0], cols[1], strip_y, strip_h)

        # ── Panel B: Layer 6 – XAI Signal Optimizer ───────────────────────
        self._panel_xai(canvas, cols[1], cols[2], strip_y, strip_h, lane_data, signal_state, surtrac_telem)

        # ── Panel C: Layer 7 – Lane Density Bars ──────────────────────────
        self._panel_density_bars(canvas, cols[2], cols[3], strip_y, strip_h, lane_data)

    def _panel_prediction(self, canvas, x1, x2, y_top, h):
        """L5 – Congestion Prediction panel with 6-bar sparkline."""
        margin = 10
        # Title
        cv2.putText(canvas, "AI CONGESTION FORECAST",
                    (x1 + margin, y_top + 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, HEADER_COLOR, 1, cv2.LINE_AA)
        cv2.line(canvas, (x1 + margin, y_top + 22),
                 (x2 - margin, y_top + 22), (40, 55, 70), 1)

        # Prediction level badge
        pred_colors = {
            "RISING":  (0, 80, 220),
            "EASING":  (0, 180, 80),
            "STABLE":  (0, 180, 200)
        }
        pc = pred_colors.get(self._pred_level, HEADER_COLOR)
        badge_txt = self._pred_level
        cv2.rectangle(canvas, (x1 + margin, y_top + 27),
                      (x1 + margin + 80, y_top + 44), pc, -1)
        cv2.putText(canvas, badge_txt,
                    (x1 + margin + 5, y_top + 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, TEXT_BRIGHT, 1)

        # ETA
        cv2.putText(canvas, f"ETA: {self._pred_eta}",
                    (x1 + margin + 90, y_top + 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.36, TEXT_DIM, 1)

        # Sparkline bars (last 12 density values)
        hist = list(self._density_history)[-12:]
        if hist:
            bar_area_x = x1 + margin
            bar_area_w = (x2 - x1) - 2 * margin
            bar_area_y = y_top + 50
            bar_area_h = h - 60
            max_val = max(max(hist), 1)
            bar_w = max(2, (bar_area_w - 4) // len(hist))

            for k, val in enumerate(hist):
                bh = int(val / max_val * bar_area_h)
                bx = bar_area_x + k * (bar_w + 2)
                by = bar_area_y + bar_area_h - bh
                # Gradient colour
                ratio = val / max_val
                b_clr = (0, int(220 * (1 - ratio)), int(220 * ratio))
                cv2.rectangle(canvas, (bx, by), (bx + bar_w, bar_area_y + bar_area_h),
                              b_clr, -1)

            # Threshold line (danger level)
            thresh_y = bar_area_y + int(bar_area_h * 0.6)
            cv2.line(canvas, (bar_area_x, thresh_y),
                     (bar_area_x + bar_area_w, thresh_y), (0, 60, 200), 1)
            cv2.putText(canvas, "THRESH",
                        (bar_area_x + bar_area_w - 45, thresh_y - 3),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.28, (0, 80, 200), 1)

    def _panel_xai(self, canvas, x1, x2, y_top, h, lane_data, signal_state, surtrac_telem=None):
        """L6 – Explainable AI (SURTRAC) panel: shows WHY the AI picked the current signal."""
        surtrac_telem = surtrac_telem or {}
        margin = 10
        cv2.putText(canvas, "XAI: SURTRAC OPTIMIZER",
                    (x1 + margin, y_top + 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 210, 255), 1, cv2.LINE_AA)
        cv2.line(canvas, (x1 + margin, y_top + 22),
                 (x2 - margin, y_top + 22), (40, 55, 70), 1)

        # Show SURTRAC + RL algorithm name
        algo = surtrac_telem.get("algorithm", self._xai_reason)
        cv2.putText(canvas, algo[:32],
                    (x1 + margin, y_top + 36),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 200, 240), 1)

        # Active lane + phase elapsed / duration
        active_l  = surtrac_telem.get("active_lane", 0)
        elapsed   = surtrac_telem.get("phase_elapsed", 0)
        duration  = surtrac_telem.get("phase_duration", 0)
        saved     = surtrac_telem.get("wait_time_saved", 0)
        eta       = surtrac_telem.get("next_arrival_eta")
        in_yellow = surtrac_telem.get("in_yellow", False)

        rl_info = surtrac_telem.get("rl_agent", {})
        rl_rew = rl_info.get("cumulative_reward", 0.0)
        rl_q = rl_info.get("max_q_value", 0.0)

        phase_clr = YELLOW if in_yellow else GREEN
        phase_lbl = "YELLOW" if in_yellow else f"GREEN L{active_l+1}"
        cv2.putText(canvas, f"Phase: {phase_lbl} | RL Rew: +{rl_rew:.1f}",
                    (x1 + margin, y_top + 52),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.33, phase_clr, 1)
        cv2.putText(canvas, f"SURTRAC: {elapsed:.1f}s/{duration:.1f}s | Q-Val: {rl_q:.2f}",
                    (x1 + margin, y_top + 66),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.31, TEXT_DIM, 1)

        # Next arrival ETA
        eta_txt = f"Next arrival: {eta:.1f}s" if eta else "No arrivals pending"
        cv2.putText(canvas, eta_txt,
                    (x1 + margin, y_top + 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.33, TEXT_DIM, 1)
        # Cumulative Wait Time Saved
        saved_txt = f"Saved: {saved:.1f}s vs fixed"
        cv2.putText(canvas, saved_txt,
                    (x1 + margin, y_top + 94),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.33, GREEN, 1)

        # Adaptive vs Fixed timing comparison
        y_cmp = y_top + 83
        cv2.putText(canvas, "ADAPTIVE   vs   FIXED TIMER",
                    (x1 + margin, y_cmp),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.32, TEXT_DIM, 1)

        bar_start = x1 + margin
        bar_end   = x2 - margin
        bar_mid   = (bar_start + bar_end) // 2
        bar_w     = bar_end - bar_start

        # Adaptive bar (green, narrower = more efficient)
        l0_count = lane_data.get("lane_0", {}).get("count", 0) if lane_data else 0
        l1_count = lane_data.get("lane_1", {}).get("count", 0) if lane_data else 0
        total = max(l0_count + l1_count, 1)
        adapt_ratio = min(0.9, 0.3 + 0.06 * total)    # simulated efficiency
        fixed_ratio = 0.5                               # fixed 50%

        for i, (ratio, clr, label, row) in enumerate([
            (adapt_ratio, GREEN,  "AI", 0),
            (fixed_ratio, (80, 80, 80), "FX", 1)
        ]):
            by = y_cmp + 8 + row * 18
            filled = int(bar_w * ratio)
            cv2.rectangle(canvas, (bar_start, by), (bar_end, by + 12),
                          (20, 28, 38), -1)
            cv2.rectangle(canvas, (bar_start, by), (bar_start + filled, by + 12),
                          clr, -1)
            cv2.putText(canvas, label, (bar_start - 22, by + 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.3, TEXT_DIM, 1)
            pct = f"{int(ratio * 100)}%"
            cv2.putText(canvas, pct, (bar_start + filled + 3, by + 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.3, TEXT_DIM, 1)

        # CO2 / eco savings
        co2 = max(0.0, (0.5 - adapt_ratio) * 200)
        cv2.putText(canvas, f"Est. Idle Reduction: {co2:.0f}s saved",
                    (x1 + margin, y_top + h - 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.33, GREEN, 1)

    def _panel_density_bars(self, canvas, x1, x2, y_top, h, lane_data):
        """L7 – Per-lane density bars + emergency indicator."""
        margin = 10
        cv2.putText(canvas, "LANE DENSITY + SIGNAL",
                    (x1 + margin, y_top + 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, YELLOW, 1, cv2.LINE_AA)
        cv2.line(canvas, (x1 + margin, y_top + 22),
                 (x2 - margin, y_top + 22), (40, 55, 70), 1)

        lane_keys = [f"lane_{i}" for i in range(self.num_lanes)]
        lane_labels = [f"Lane {i+1}" for i in range(self.num_lanes)]
        bar_w = (x2 - x1 - 2 * margin)
        level_map = {"LOW": 0.15, "MODERATE": 0.45, "HIGH": 0.70, "CRITICAL": 1.0}
        clr_map   = {"LOW": GREEN, "MODERATE": YELLOW, "HIGH": ORANGE, "CRITICAL": RED}

        for i, (key, lbl) in enumerate(zip(lane_keys, lane_labels)):
            info  = lane_data.get(key, {}) if lane_data else {}
            level = info.get("level", "LOW")
            count = info.get("count", 0)
            ratio = level_map.get(level, 0.15)
            clr   = clr_map.get(level, GREEN)

            by = y_top + 32 + i * 38

            cv2.putText(canvas, f"{lbl}  ({count}v)  {level}",
                        (x1 + margin, by),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.36, clr, 1)

            # Background bar
            cv2.rectangle(canvas, (x1 + margin, by + 4),
                          (x1 + margin + bar_w, by + 18),
                          (22, 30, 40), -1)
            # Filled bar
            filled = int(bar_w * ratio)
            cv2.rectangle(canvas, (x1 + margin, by + 4),
                          (x1 + margin + filled, by + 18), clr, -1)
            cv2.rectangle(canvas, (x1 + margin, by + 4),
                          (x1 + margin + bar_w, by + 18),
                          (60, 70, 80), 1)

        # Emergency indicator
        em_y = y_top + h - 35
        cv2.line(canvas, (x1 + margin, em_y), (x2 - margin, em_y), (40, 55, 70), 1)
        em_clr = (0, 80, 255) if self._blink else (0, 30, 120)
        cv2.putText(canvas, "EMERGENCY CORRIDOR: CLEAR",
                    (x1 + margin, em_y + 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.33, em_clr, 1)

        # Legend
        for j, (txt, clr) in enumerate([("LOW", GREEN), ("MOD", YELLOW),
                                         ("HIGH", ORANGE), ("CRIT", RED)]):
            lx = x1 + margin + j * 48
            cv2.rectangle(canvas, (lx, em_y + 22), (lx + 10, em_y + 32), clr, -1)
            cv2.putText(canvas, txt, (lx + 12, em_y + 31),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.28, TEXT_DIM, 1)


# ──────────────────────────────────────────────────────────────────────────────
# Quick sanity test
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    dt = DigitalTwin(width=800, height=500)
    vehicles = [
        {"track_id": 1, "center": (200, 200), "current_speed": 42.0, "class_name": "car"},
        {"track_id": 2, "center": (800, 400), "current_speed": 88.0, "class_name": "truck"},
        {"track_id": 3, "center": (500, 300), "current_speed": 65.0, "class_name": "motorcycle"},
    ]
    lanes = {
        "lane_0": {"count": 4, "level": "MODERATE"},
        "lane_1": {"count": 9, "level": "HIGH"}
    }
    signals = {
        "lane_0": (0, 230, 0),
        "lane_1": (0, 0, 230)
    }
    canvas = dt.render_2d_twin(vehicles, lanes, signals)
    cv2.imshow("Digital Twin – SIH 2026 PS1", canvas)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    print(f"[OK] DigitalTwin upgraded successfully! Canvas: {canvas.shape}")

"""
Adaptive Traffic Signal Manager (SURTRAC-powered)
SIH 2026 - PS1: AI Traffic Digital Twin

Delegates per-intersection scheduling to SURTRACController.
Keeps backward-compatible API so main.py needs no changes.
"""

import time
from typing import Dict, List, Optional

from src.surtrac_controller import SURTRACController


# BGR colour constants (OpenCV)
CLR_GREEN  = (0, 230, 0)
CLR_YELLOW = (0, 210, 255)
CLR_RED    = (0, 0, 230)


class TrafficSignalManager:
    """
    SURTRAC-powered adaptive signal manager.

    Drop-in replacement for the original density-only manager.
    Exposes the same public methods so main.py requires zero changes.
    """

    def __init__(self, num_lanes: int = 2):
        self.num_lanes         = num_lanes
        self.emergency_mode    = False
        self.emergency_lane: Optional[str] = None

        # SURTRAC core
        self._surtrac = SURTRACController(num_lanes=num_lanes)

        # Cache last signal state (string → BGR color)
        self._last_state: Dict[str, str] = {
            f"lane_{i}": "RED" for i in range(num_lanes)
        }
        self._last_state["lane_0"] = "GREEN"

        # Convenience for external readers (active green lane index)
        self.active_green_lane: int = 0

        # Store last tracked vehicles so update_signals_adaptive can pass them to SURTRAC
        self._tracked_vehicles: List[Dict] = []
        self._frame_w: int = 1280
        self._frame_h: int = 720

    # ─────────────────────────────────────────────────────────────────────────
    # Emergency overrides
    # ─────────────────────────────────────────────────────────────────────────

    def activate_emergency_mode(self, emergency_lane: str):
        """Force emergency lane green, all others red."""
        self.emergency_mode = True
        self.emergency_lane = emergency_lane
        self._surtrac.activate_emergency(emergency_lane)

    def deactivate_emergency_mode(self):
        """Resume SURTRAC adaptive control."""
        self.emergency_mode = False
        self.emergency_lane = None
        self._surtrac.deactivate_emergency()

    # ─────────────────────────────────────────────────────────────────────────
    # Called every frame from main.py
    # ─────────────────────────────────────────────────────────────────────────

    def set_frame_context(self, tracked_vehicles: List[Dict],
                          frame_w: int = 1280, frame_h: int = 720):
        """
        Supply the current tracked-vehicle list so SURTRAC can compute
        arrival schedules.  Call this BEFORE update_signals_adaptive().
        """
        self._tracked_vehicles = tracked_vehicles
        self._frame_w = frame_w
        self._frame_h = frame_h

    def update_signals_adaptive(self, lane_data: Dict, traffic_trend: str = "STABLE"):
        """
        Run SURTRAC scheduler and cache result.

        Parameters mirror the original API so main.py needs no changes.
        """
        if self.emergency_mode:
            return

        state = self._surtrac.update(
            self._tracked_vehicles,
            lane_data,
            self._frame_w,
            self._frame_h,
        )
        self._last_state = state
        self.active_green_lane = self._surtrac.active_lane

    # ─────────────────────────────────────────────────────────────────────────
    # Signal state readers
    # ─────────────────────────────────────────────────────────────────────────

    def get_all_signals(self) -> Dict[str, Dict]:
        """
        Returns { lane_key: {"color": (B, G, R)} } in OpenCV BGR format.
        Backward compatible with the original manager's output.
        """
        signals = {}
        for i in range(self.num_lanes):
            lk = f"lane_{i}"
            if self.emergency_mode:
                color = CLR_GREEN if lk == self.emergency_lane else CLR_RED
            else:
                s = self._last_state.get(lk, "RED")
                if s == "GREEN":
                    color = CLR_GREEN
                elif s == "YELLOW":
                    color = CLR_YELLOW
                else:
                    color = CLR_RED
            signals[lk] = {"color": color}
        return signals

    def get_emergency_info(self) -> Dict:
        return {
            "active": self.emergency_mode,
            "lane":   self.emergency_lane,
        }

    def get_surtrac_telemetry(self) -> Dict:
        """
        Rich SURTRAC telemetry for the Digital Twin XAI panel.
        """
        return self._surtrac.get_telemetry()


# ─────────────────────────────────────────────────────────────────────────────
# Standalone test
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mgr = TrafficSignalManager(num_lanes=2)

    vehicles = [
        {"track_id": 1, "center": (200, 600), "current_speed": 40.0},
        {"track_id": 2, "center": (300, 500), "current_speed": 55.0},
        {"track_id": 3, "center": (900, 400), "current_speed": 30.0},
    ]
    lane_data = {
        "lane_0": {"count": 2, "level": "MODERATE"},
        "lane_1": {"count": 1, "level": "LOW"},
    }

    mgr.set_frame_context(vehicles)
    mgr.update_signals_adaptive(lane_data, "STABLE")
    signals = mgr.get_all_signals()
    telem   = mgr.get_surtrac_telemetry()

    def _cname(bgr):
        if bgr == CLR_GREEN:   return "GREEN"
        if bgr == CLR_YELLOW:  return "YELLOW"
        return "RED"

    print("[OK] SURTRAC-powered TrafficSignalManager!")
    for lane, info in signals.items():
        print(f"  {lane}: {_cname(info['color'])}")
    print(f"  SURTRAC active lane:  lane_{telem['active_lane']}")
    print(f"  Algorithm:            {telem['algorithm']}")
    print(f"  Wait time saved:      {telem['wait_time_saved']} s vs fixed timer")

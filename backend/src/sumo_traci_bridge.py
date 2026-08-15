"""
SUMO (Simulation of Urban MObility) / TraCI Live Virtual Mirror & Closed-Loop Feedback

REAL implementation - replaces the previous mocked version that returned
hand-computed formulas. This module actually launches SUMO and drives it
via the TraCI Python API, so queue lengths, delay, and what-if signal
timing results come from SUMO's own car-following / traffic-light model,
not from arithmetic we invented.

Setup required (one-time):
    1. Install SUMO:  sudo apt install sumo sumo-tools   (Linux)
                       or download from https://sumo.dlr.de/docs/Downloads.php
    2. pip install traci sumolib
    3. Put intersection.net.xml, intersection.rou.xml, intersection.sumocfg
       (provided alongside this file) in a `sumo/` folder next to `backend/`.
    4. If you want this tied to a REAL intersection instead of the generic
       4-way template provided, export it from OpenStreetMap:
         netconvert --osm-files your_area.osm -o intersection.net.xml
       (grab the .osm export from https://www.openstreetmap.org/export
        or via the Overpass API for just your intersection's bounding box)

Usage:
    bridge = SUMOTraCIBridge(sumo_cfg_path="sumo/intersection.sumocfg")
    bridge.start()
    ... in your main detection loop, once per frame/interval ...
    bridge.sync_virtual_graph_state({"lane_id": "N_in_0", "vehicle_count": 7, ...})
    ...
    bridge.close()
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

_backend_dir = Path(__file__).parent.parent.resolve()
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

try:
    from src.logger import logger
except ImportError:
    try:
        from logger import logger
    except ImportError:
        import logging
        logger = logging.getLogger("traffic_ai")


class SUMOTraCIBridge:
    """
    Real SUMO / TraCI bridge. Launches a SUMO simulation process and steps
    it forward, injecting vehicles derived from live camera counts and
    reading back genuine queue lengths / delays computed by SUMO's engine.
    """

    def __init__(self, sumo_cfg_path: str = "sumo/intersection.sumocfg", gui: bool = False):
        self.sumo_cfg_path = sumo_cfg_path
        self.gui = gui
        self.traci_active = False
        self.traci = None
        self._injected_vehicle_counter = 0
        self._route_by_lane_prefix = {
            "N": "N_to_S",
            "S": "S_to_N",
            "E": "E_to_W",
            "W": "W_to_E",
        }
        self._init_sumo_traci()

    def _init_sumo_traci(self):
        """Import traci and launch (or connect to) a running SUMO instance."""
        try:
            import traci
            self.traci = traci
        except ImportError:
            logger.warning(
                "[SUMO/TraCI] `traci` package not installed. Run: pip install traci sumolib. "
                "Falling back to emulated mode (numbers will NOT reflect a real simulation)."
            )
            self.traci_active = False
            return

        if not Path(self.sumo_cfg_path).exists():
            logger.warning(
                f"[SUMO/TraCI] Config not found at {self.sumo_cfg_path}. "
                "Falling back to emulated mode. Copy the sumo/ folder into your project root."
            )
            self.traci_active = False
            return

        try:
            binary = "sumo-gui" if self.gui else "sumo"
            self.traci.start([binary, "-c", self.sumo_cfg_path, "--no-step-log", "--quit-on-end"])
            self.traci_active = True
            logger.info(f"[SUMO/TraCI] Connected to real SUMO simulation ({binary}).")
        except Exception as e:
            logger.error(f"[SUMO/TraCI] Failed to launch SUMO: {e}")
            self.traci_active = False

    def start(self):
        """Explicit start, in case you construct the bridge before SUMO should launch."""
        if not self.traci_active:
            self._init_sumo_traci()

    def sync_virtual_graph_state(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ingest live camera/MQTT telemetry: inject a vehicle into the SUMO
        simulation matching the observed approach, step the simulation,
        and read back REAL queue length / speed from SUMO's own state -
        not a formula.
        """
        lane_id = telemetry.get("lane_id", "N_in_0")
        v_count = telemetry.get("vehicle_count", 0)

        if not self.traci_active:
            return self._emulated_fallback(telemetry)

        approach = lane_id[0].upper() if lane_id and lane_id[0].upper() in self._route_by_lane_prefix else "N"
        route_id = self._route_by_lane_prefix[approach]
        in_edge = f"{approach}_in"

        # Inject vehicles proportional to observed count above what's already
        # running on that edge, so SUMO's density roughly mirrors the camera.
        try:
            already_on_edge = self.traci.edge.getLastStepVehicleNumber(in_edge)
            to_inject = max(0, v_count - already_on_edge)
            for _ in range(min(to_inject, 5)):  # cap per-call injection to avoid runaway spawns
                veh_id = f"cam_veh_{self._injected_vehicle_counter}"
                self._injected_vehicle_counter += 1
                try:
                    self.traci.vehicle.add(veh_id, route_id, typeID="car")
                except Exception:
                    pass  # route/type may momentarily be busy; skip this tick

            self.traci.simulationStep()

            queue_length = self.traci.edge.getLastStepHaltingNumber(in_edge)
            avg_speed_ms = self.traci.edge.getLastStepMeanSpeed(in_edge)
            avg_speed_kmh = round(avg_speed_ms * 3.6, 1) if avg_speed_ms >= 0 else 0.0
            sim_time = self.traci.simulation.getTime()

            return {
                "sumo_version": "Eclipse SUMO (live TraCI)",
                "sim_step": int(sim_time),
                "virtual_node": "center",
                "active_edge": in_edge,
                "virtual_queue_length_m": round(queue_length * 6.0, 1),  # ~6m per halted vehicle incl. gap
                "simulated_avg_speed_kmh": avg_speed_kmh,
                "traci_status": "ACTIVE_SYNC",
            }
        except Exception as e:
            logger.error(f"[SUMO/TraCI] Step failed, falling back to emulated values: {e}")
            return self._emulated_fallback(telemetry)

    def simulate_what_if_signal_override(self, proposed_green_sec: int, tls_id: str = "center") -> Dict[str, Any]:
        """
        REAL what-if test: measure current average waiting time on the
        signalized edges, change the traffic light's green phase duration
        via TraCI, step the simulation forward, and measure again. The
        delay reduction reported is what SUMO actually computed, not a
        formula.
        """
        if not self.traci_active:
            return self._emulated_what_if_fallback(proposed_green_sec)

        try:
            monitored_edges = ["N_in", "S_in", "E_in", "W_in"]

            def avg_wait():
                waits = [self.traci.edge.getWaitingTime(e) for e in monitored_edges]
                return sum(waits) / max(1, len(waits))

            baseline_delay = avg_wait()

            # Extend every "green" phase in the current program to proposed_green_sec.
            logic = self.traci.trafficlight.getAllProgramLogics(tls_id)[0]
            for phase in logic.phases:
                if "G" in phase.state:
                    phase.duration = proposed_green_sec
            self.traci.trafficlight.setProgramLogic(tls_id, logic)

            for _ in range(60):  # step forward 60s to let the new timing take effect
                self.traci.simulationStep()

            optimized_delay = avg_wait()
            delay_reduction_pct = round(
                ((baseline_delay - optimized_delay) / baseline_delay) * 100.0, 1
            ) if baseline_delay > 0 else 0.0

            return {
                "scenario": "What-If Signal Timing Adjustment (live SUMO)",
                "proposed_green_duration_sec": proposed_green_sec,
                "baseline_delay_sec": round(baseline_delay, 1),
                "simulated_delay_sec": round(optimized_delay, 1),
                "predicted_delay_reduction_pct": delay_reduction_pct,
                "recommendation": "APPROVED FOR REAL-WORLD DEPLOYMENT" if delay_reduction_pct > 15.0 else "REJECTED",
            }
        except Exception as e:
            logger.error(f"[SUMO/TraCI] What-if simulation failed: {e}")
            return self._emulated_what_if_fallback(proposed_green_sec)

    def _emulated_fallback(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """Used only when SUMO/traci isn't available - clearly labeled as emulated."""
        lane_id = telemetry.get("lane_id", "lane_0")
        v_count = telemetry.get("vehicle_count", 0)
        signal_phase = telemetry.get("signal_phase", "GREEN")
        simulated_queue = max(0.0, (v_count * 4.5) - (12.0 if signal_phase == "GREEN" else 0.0))
        return {
            "sumo_version": "NOT CONNECTED - emulated placeholder",
            "sim_step": int(time.time()) % 1000,
            "virtual_node": "INT_001_JUNCTION",
            "active_edge": f"EDGE_{lane_id.upper()}",
            "virtual_queue_length_m": round(simulated_queue, 1),
            "simulated_avg_speed_kmh": telemetry.get("avg_speed_kmh", 45.0),
            "traci_status": "EMULATED_TRACI_GRAPH",
        }

    def _emulated_what_if_fallback(self, proposed_green_sec: int) -> Dict[str, Any]:
        current_delay = 34.5
        optimized_delay = max(12.0, current_delay - (proposed_green_sec * 0.4))
        delay_reduction_pct = round(((current_delay - optimized_delay) / current_delay) * 100.0, 1)
        return {
            "scenario": "What-If Signal Timing Adjustment (NOT CONNECTED - emulated)",
            "proposed_green_duration_sec": proposed_green_sec,
            "baseline_delay_sec": current_delay,
            "simulated_delay_sec": round(optimized_delay, 1),
            "predicted_delay_reduction_pct": delay_reduction_pct,
            "recommendation": "APPROVED FOR REAL-WORLD DEPLOYMENT" if delay_reduction_pct > 15.0 else "REJECTED",
        }

    def close(self):
        if self.traci_active:
            try:
                self.traci.close()
            except Exception:
                pass
            self.traci_active = False


if __name__ == "__main__":
    bridge = SUMOTraCIBridge(sumo_cfg_path="../../sumo/intersection.sumocfg")
    sync_res = bridge.sync_virtual_graph_state({"lane_id": "N_in_0", "vehicle_count": 6, "avg_speed_kmh": 38.0, "signal_phase": "GREEN"})
    sim_res = bridge.simulate_what_if_signal_override(proposed_green_sec=45)
    print(f"[OK] SUMOTraCIBridge tested. traci_active={bridge.traci_active}")
    print(f"  Graph Sync: {sync_res}")
    print(f"  What-If: {sim_res}")
    bridge.close()

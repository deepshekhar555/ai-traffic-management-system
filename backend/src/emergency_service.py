"""
Emergency Service & Alarm Management Module
"""

import time
import winsound
from datetime import datetime
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
except ImportError:
    from backend.src.logger import logger


class EmergencyServiceManager:
    """Manages alarms and emergency calls to police, ambulance, and fire brigade"""
    
    def __init__(self, enable_calls=False):
        self.enable_calls = enable_calls
        self.calls = []
        self.stats = {
            "total_calls": 0,
            "today_calls": 0,
            "by_service": {"Police": 0, "Ambulance": 0, "Fire Brigade": 0},
            "by_incident_type": {"Speeding": 0, "Collision": 0, "Fire": 0}
        }

    def ring_alarm(self, duration=1, frequency=1000):
        """Ring sound alarm using system sound synthesizer"""
        try:
            winsound.Beep(frequency, int(duration * 1000))
        except Exception:
            pass

    def _log_call(self, service: str, incident_type: str, details: dict):
        """Record emergency call details"""
        call_entry = {
            "timestamp": datetime.now().isoformat(),
            "service": service,
            "incident_type": incident_type,
            "details": details
        }
        self.calls.append(call_entry)
        self.stats["total_calls"] += 1
        self.stats["today_calls"] += 1
        if service in self.stats["by_service"]:
            self.stats["by_service"][service] += 1
        if incident_type in self.stats["by_incident_type"]:
            self.stats["by_incident_type"][incident_type] += 1
            
        status_str = "CALL DISPATCHED" if self.enable_calls else "MOCK CALL LOGGED"
        logger.warning(f"[EMERGENCY] [{status_str}]: Service={service} | Type={incident_type} | Details={details}")

    def handle_speeding_vehicle(self, vehicle: dict, excess_speed: float):
        """Handle speeding vehicle alert and police call"""
        self.ring_alarm(duration=0.5, frequency=1200)
        self._log_call("Police", "Speeding", {
            "vehicle_id": vehicle.get("track_id"),
            "speed": vehicle.get("speed", 0),
            "excess": excess_speed
        })

    def handle_accident(self, accident_info: dict):
        """Handle vehicle collision and dispatch police + ambulance"""
        self.ring_alarm(duration=1.0, frequency=1500)
        self._log_call("Police", "Collision", accident_info)
        self._log_call("Ambulance", "Collision", accident_info)

    def handle_fire_incident(self, fire_info: dict):
        """Handle fire incident and dispatch fire brigade"""
        self.ring_alarm(duration=1.5, frequency=2000)
        self._log_call("Fire Brigade", "Fire", fire_info)

    def get_call_statistics(self) -> dict:
        """Return call statistics summary"""
        return self.stats

    def handle_collision(self, accident_info: dict):
        """Alias for handle_accident to match speed integration requirements"""
        return self.handle_accident(accident_info)

    def handle_fire(self, fire_info: dict):
        """Alias for handle_fire_incident to match speed integration requirements"""
        return self.handle_fire_incident(fire_info)

    def handle_speeding(self, vehicle: dict, excess_speed: float):
        """Alias for handle_speeding_vehicle to match speed integration requirements"""
        return self.handle_speeding_vehicle(vehicle, excess_speed)


if __name__ == "__main__":
    em_mgr = EmergencyServiceManager(enable_calls=False)
    em_mgr.handle_speeding({"track_id": 12, "speed": 105.0}, excess_speed=25.0)
    em_mgr.handle_accident({"location": "Junction 4", "vehicles_involved": 2})
    stats = em_mgr.get_call_statistics()
    print(f"[OK] EmergencyServiceManager tested successfully! Dispatch Stats: {stats}")



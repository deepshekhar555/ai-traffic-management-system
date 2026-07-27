"""
Traffic Alert Manager for logging and managing system notifications
"""

import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent.parent.resolve()
backend_dir = Path(__file__).parent.parent.resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from datetime import datetime
try:
    from src.logger import logger
except ImportError:
    from backend.src.logger import logger


class AlertManager:
    """Manages active traffic alerts, severities, and stats"""
    
    def __init__(self):
        self.active_alerts = []
        self.total_alerts = 0

    def high_traffic_alert(self, lane_name, vehicle_count, density):
        """Create high traffic alert"""
        alert = {
            "id": self.total_alerts + 1,
            "type": "high_traffic",
            "severity": "HIGH",
            "message": f"High traffic on {lane_name}: {vehicle_count} vehicles ({density*100:.1f}%)",
            "timestamp": datetime.now().isoformat()
        }
        self.total_alerts += 1
        self.active_alerts.append(alert)
        logger.warning(alert["message"])
        return alert

    def normal_traffic_alert(self, lane_name):
        """Create normal traffic alert and clear high traffic alerts"""
        self.active_alerts = [a for a in self.active_alerts if a["type"] != "high_traffic"]
        alert = {
            "id": self.total_alerts + 1,
            "type": "normal_traffic",
            "severity": "INFO",
            "message": f"Normal traffic flow restored on {lane_name}",
            "timestamp": datetime.now().isoformat()
        }
        self.total_alerts += 1
        logger.info(alert["message"])
        return alert

    def hsr_status_alert(self, status, time_remaining=0.0):
        """Create HSR hard shoulder status alert"""
        alert = {
            "id": self.total_alerts + 1,
            "type": "hsr_status",
            "severity": "WARNING" if status == "CLOSING" else "INFO",
            "message": f"HSR Hard Shoulder Status: {status}",
            "timestamp": datetime.now().isoformat()
        }
        self.total_alerts += 1
        self.active_alerts.append(alert)
        logger.info(alert["message"])
        return alert

    def accident_alert(self, location, severity="CRITICAL"):
        """Create accident alert"""
        alert = {
            "id": self.total_alerts + 1,
            "type": "accident",
            "severity": severity,
            "message": f"Accident Alert at {location} [{severity}]",
            "timestamp": datetime.now().isoformat()
        }
        self.total_alerts += 1
        self.active_alerts.append(alert)
        logger.warning(alert["message"])
        return alert

    def resolve_alert(self, alert_id):
        """Resolve alert by ID"""
        self.active_alerts = [a for a in self.active_alerts if a.get("id") != alert_id]
        return True

    def get_active_alerts(self):
        """Get list of active unresolved alerts"""
        return self.active_alerts

    def get_alert_stats(self):
        """Get statistics summary"""
        by_type = {}
        by_severity = {}
        for a in self.active_alerts:
            t = a.get("type", "other")
            s = a.get("severity", "INFO")
            by_type[t] = by_type.get(t, 0) + 1
            by_severity[s] = by_severity.get(s, 0) + 1
        return {
            "total_alerts": self.total_alerts,
            "active_alerts": len(self.active_alerts),
            "by_type": by_type,
            "by_severity": by_severity
        }


if __name__ == "__main__":
    mgr = AlertManager()
    mgr.high_traffic_alert("Main Junction", 15, 0.85)
    mgr.accident_alert("Lane 1 Crosswalk")
    print(f"[OK] AlertManager tested successfully! Stats: {mgr.get_alert_stats()}")



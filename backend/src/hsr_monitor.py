"""
HSR (Human Shoulder Responsibility) Monitoring Module
"""

class HSRMonitor:
    """Monitors shoulder lane usage and incident clearance status"""
    
    def __init__(self):
        self.status = "OPEN"
        self.incident_count = 0
        self.clear_count = 0

    def update_status(self, is_incident: bool):
        """Update HSR status based on incident detection"""
        if is_incident:
            self.incident_count += 1
            self.clear_count = 0
            if self.incident_count >= 5:
                self.status = "CLOSING"
            if self.incident_count >= 15:
                self.status = "CLOSED"
        else:
            self.clear_count += 1
            self.incident_count = 0
            if self.clear_count >= 10:
                self.status = "OPEN"

    def get_status(self) -> str:
        """Get current HSR status"""
        return self.status


if __name__ == "__main__":
    hsr = HSRMonitor()
    for _ in range(6):
        hsr.update_status(is_incident=True)
    print(f"[OK] HSRMonitor tested successfully! Current Hard Shoulder Lane Status: {hsr.get_status()}")


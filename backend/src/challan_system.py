"""
Automated E-Challan Fine Ticket & Notification Engine
Calculates Motor Vehicle Act fine amounts and generates instant e-Challan digital receipts.
"""

import json
import random
import time
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


class EChallanSystem:
    """Automated E-Challan Ticket & Fine Generation System"""
    
    def __init__(self):
        self.issued_challans = []
        logger.info("Automated E-Challan Digital Ticket Engine initialized!")

    def calculate_fine(self, speed_kmh, violation_type="Speeding"):
        """Calculate fine amount based on Motor Vehicle Act standards (INR ₹)"""
        if violation_type == "Emergency Obstruction":
            return 10000  # ₹10,000 fine for blocking ambulance/fire engine
        elif violation_type == "Red Light Jump":
            return 5000   # ₹5,000 fine for red light violation
        else:
            excess = speed_kmh - 80
            if excess > 40:
                return 5000  # Extreme speeding (>120 km/h)
            elif excess > 20:
                return 2000  # Heavy speeding (100 - 120 km/h)
            else:
                return 1000  # Moderate speeding (80 - 100 km/h)

    def issue_challan(self, plate_number, speed_kmh, vehicle_type="car", violation_type="Speeding", location="Main Junction"):
        """Generate and issue digital e-Challan ticket"""
        fine_amount = self.calculate_fine(speed_kmh, violation_type)
        challan_id = f"CHALLAN-{random.randint(100000, 999999)}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        challan = {
            "challan_id": challan_id,
            "plate_number": plate_number,
            "vehicle_type": vehicle_type,
            "speed_kmh": round(speed_kmh, 1),
            "speed_limit": 80,
            "violation_type": violation_type,
            "fine_amount_inr": fine_amount,
            "location": location,
            "status": "ISSUED",
            "timestamp": timestamp,
            "notification_sent": True
        }
        
        self.issued_challans.append(challan)
        logger.info(f"[CHALLAN ISSUED] Ticket #{challan_id} | Plate: {plate_number} | Fine: INR {fine_amount} ({violation_type} @ {speed_kmh:.1f} km/h)")
        return challan

    def get_issued_challans(self):
        """Return list of all issued e-Challans"""
        return self.issued_challans


if __name__ == "__main__":
    challan_sys = EChallanSystem()
    ticket = challan_sys.issue_challan("KA-33-JI-6538", speed_kmh=115.4, vehicle_type="car")
    print(f"[OK] EChallanSystem tested successfully! Issued Ticket ID: {ticket['challan_id']} (Fine: INR {ticket['fine_amount_inr']})")


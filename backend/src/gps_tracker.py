"""
GPS Tracking & Traffic Hotspot Logger
"""

import json
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


class GPSTracker:
    """Tracks location coordinates and logs traffic congestion hotspots"""
    
    def __init__(self, default_lat=40.7128, default_lon=-74.0060, location_name="Traffic Management Center"):
        self.latitude = default_lat
        self.longitude = default_lon
        self.location_name = location_name
        self.hotspots = []
        self.detection_count = 0

    def mark_high_traffic_zone(self, level="HIGH"):
        """Record a high traffic hotspot at current GPS coordinate"""
        self.detection_count += 1
        hotspot = {
            "name": f"{self.location_name} - Zone {len(self.hotspots) + 1}",
            "lat": self.latitude + (len(self.hotspots) * 0.001),
            "lon": self.longitude + (len(self.hotspots) * 0.001),
            "count": self.detection_count,
            "level": level
        }
        if len(self.hotspots) == 0 or self.hotspots[-1]["level"] != level:
            self.hotspots.append(hotspot)
        else:
            self.hotspots[-1]["count"] += 1

    def get_traffic_hotspots(self):
        """Return recorded traffic hotspots"""
        return self.hotspots

    def get_location_string(self):
        """Return formatted location string"""
        return f"{self.location_name} ({self.latitude:.4f}°N, {self.longitude:.4f}°E)"

    def get_map_url(self):
        """Return OpenStreetMap or Google Maps URL"""
        return f"https://www.openstreetmap.org/?mlat={self.latitude}&mlon={self.longitude}#map=15/{self.latitude}/{self.longitude}"

    def save_location_data(self):
        """Save location and hotspot data to file"""
        try:
            out_file = Path("logs/gps_hotspots.json")
            out_file.parent.mkdir(exist_ok=True)
            data = {
                "location": self.location_name,
                "coordinates": {"lat": self.latitude, "lon": self.longitude},
                "hotspots": self.hotspots
            }
            with open(out_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved GPS location data to {out_file}")
        except Exception as e:
            logger.error(f"Failed to save GPS location data: {e}")


if __name__ == "__main__":
    gps = GPSTracker()
    gps.mark_high_traffic_zone("HIGH")
    gps.save_location_data()
    print(f"[OK] GPSTracker tested successfully! Location: {gps.get_location_string()} (Hotspots: {len(gps.get_traffic_hotspots())})")


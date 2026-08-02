"""
TraffixAI — Push Alert System
Uses ntfy.sh (completely FREE, no API key, instant phone push notification).

Setup (one-time, 30 seconds):
  1. Install 'ntfy' app on your phone from Play Store / App Store
  2. Subscribe to topic: traffixai-ciphersquad
  3. Done — you'll instantly get alerts when accidents/fire/speeding happen!
"""

import urllib.request
import urllib.parse
import threading
import time
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent.resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    from src.logger import logger
except ImportError:
    from backend.src.logger import logger

# ── Configuration ─────────────────────────────────────────────────────────────
NTFY_SERVER  = "https://ntfy.sh"
NTFY_TOPIC   = "traffixai-ciphersquad-ke5vnd"   # Unique to your team
ALERT_COOLDOWN_SECONDS = 30                       # Don't spam — min gap between same alert type

_last_alert_time: dict = {}   # track_type → last_sent_timestamp
_lock = threading.Lock()


def _send_ntfy(title: str, message: str, priority: str = "high", tags: str = "rotating_light"):
    """Send push notification via ntfy.sh (fire-and-forget in background thread)."""
    def _do_send():
        try:
            url = f"{NTFY_SERVER}/{urllib.parse.quote(NTFY_TOPIC)}"
            data = message.encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "Title":    title,
                    "Priority": priority,
                    "Tags":     tags,
                    "Content-Type": "text/plain; charset=utf-8",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                logger.info(f"[PUSH ALERT] Sent: {title} | Status: {resp.status}")
        except Exception as e:
            logger.debug(f"[PUSH ALERT] Could not send (offline?): {e}")

    t = threading.Thread(target=_do_send, daemon=True)
    t.start()


def _can_send(alert_type: str) -> bool:
    """Rate limit: same alert type can only fire every ALERT_COOLDOWN_SECONDS."""
    with _lock:
        now = time.time()
        last = _last_alert_time.get(alert_type, 0)
        if now - last >= ALERT_COOLDOWN_SECONDS:
            _last_alert_time[alert_type] = now
            return True
        return False


# ── Public API ────────────────────────────────────────────────────────────────

def alert_accident(location: str = "Junction", vehicles: int = 2):
    """Send push alert for vehicle collision/accident."""
    if not _can_send("accident"):
        return
    _send_ntfy(
        title="🚨 ACCIDENT DETECTED — TraffixAI",
        message=f"Vehicle collision at {location}.\n"
                f"Vehicles involved: {vehicles}\n"
                f"⚡ Police + Ambulance auto-dispatched!\n"
                f"📍 Open dashboard: http://localhost:5000",
        priority="urgent",
        tags="rotating_light,ambulance",
    )

def alert_fire(location: str = "Junction"):
    """Send push alert for fire incident."""
    if not _can_send("fire"):
        return
    _send_ntfy(
        title="🔥 FIRE DETECTED — TraffixAI",
        message=f"Fire incident detected at {location}.\n"
                f"🚒 Fire Brigade auto-dispatched!\n"
                f"📍 Open dashboard: http://localhost:5000",
        priority="urgent",
        tags="fire,rotating_light",
    )

def alert_speeding(vehicle_id, speed: float, limit: float = 60.0):
    """Send push alert for speeding vehicle."""
    if not _can_send("speeding"):
        return
    excess = speed - limit
    _send_ntfy(
        title=f"🚔 SPEEDING VEHICLE — TraffixAI",
        message=f"Vehicle #{vehicle_id} detected at {speed:.1f} km/h\n"
                f"Speed limit: {limit:.0f} km/h | Excess: +{excess:.1f} km/h\n"
                f"📋 E-Challan auto-generated!\n"
                f"📍 Dashboard: http://localhost:5000",
        priority="high",
        tags="police_car,warning",
    )

def alert_emergency_vehicle(ev_type: str = "Ambulance", location: str = "Junction"):
    """Send push alert for detected emergency vehicle."""
    if not _can_send("emergency_vehicle"):
        return
    _send_ntfy(
        title=f"🚑 EMERGENCY VEHICLE — TraffixAI",
        message=f"{ev_type} detected approaching {location}.\n"
                f"🟢 Green Corridor ACTIVATED — all signals cleared!\n"
                f"📍 Dashboard: http://localhost:5000",
        priority="high",
        tags="ambulance,green_heart",
    )

def alert_congestion(level: str = "HIGH", location: str = "Junction"):
    """Send push alert for high congestion."""
    if not _can_send("congestion"):
        return
    _send_ntfy(
        title=f"🚦 CONGESTION {level} — TraffixAI",
        message=f"Traffic congestion level {level} at {location}.\n"
                f"AI signal optimization activated.\n"
                f"📍 Dashboard: http://localhost:5000",
        priority="default",
        tags="traffic_light,warning",
    )

def send_test_alert():
    """Test push notification setup."""
    _send_ntfy(
        title="✅ TraffixAI Connected!",
        message="Push alerts are working!\n"
                "You will now receive instant alerts for:\n"
                "• Accidents & Collisions\n"
                "• Fire Incidents\n"
                "• Speeding Violations\n"
                "• Emergency Vehicle Detection\n"
                "• High Congestion Events\n\n"
                f"Topic: {NTFY_TOPIC}",
        priority="default",
        tags="white_check_mark",
    )
    print(f"[PUSH ALERT] Test sent! Subscribe to topic '{NTFY_TOPIC}' in ntfy app.")


if __name__ == "__main__":
    print("Testing TraffixAI Push Alert System...")
    print(f"Subscribe to ntfy topic: {NTFY_TOPIC}")
    send_test_alert()
    time.sleep(2)
    alert_speeding(vehicle_id=42, speed=95.0, limit=60.0)
    time.sleep(2)
    print("[OK] Push Alert System tested!")

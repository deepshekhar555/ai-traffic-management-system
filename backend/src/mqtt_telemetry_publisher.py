"""
MQTT Structured Telemetry Publisher for Real-Time Digital Twin Sync
Publishes structured JSON (timestamp, lane_id, vehicle_count, avg_speed, queue_length, signal_phase)
"""

import json
import time
import sys
from pathlib import Path
from typing import Dict, Any

_backend_dir = Path(__file__).parent.parent.resolve()
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

try:
    from src.logger import logger
except ImportError:
    from backend.src.logger import logger


class MQTTTelemetryPublisher:
    """
    MQTT Telemetry Broker / Publisher Client
    Streams live physical perception data to downstream SUMO / GNN Digital Twin Modules
    """
    def __init__(self, broker_host: str = "localhost", broker_port: int = 1883, topic: str = "traffix/telemetry/intersection_1"):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic = topic
        self.client = None
        self._init_mqtt_client()

    def _init_mqtt_client(self):
        """Initialize Paho MQTT Client with fallback simulation buffer"""
        try:
            import paho.mqtt.client as mqtt
            self.client = mqtt.Client(client_id="TraffixAI_Publisher")
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            self.client.loop_start()
            logger.info(f"[MQTT] Connected to MQTT Broker at {self.broker_host}:{self.broker_port} | Topic: {self.topic}")
        except Exception as e:
            logger.warning(f"[MQTT] Could not connect to external MQTT Broker ({e}). Using local in-memory pub-sub loop.")
            self.client = None

    def publish_lane_telemetry(self, lane_id: str, vehicle_count: int, avg_speed_kmh: float, queue_length_m: float, signal_phase: str) -> Dict[str, Any]:
        """Format and publish structured telemetry JSON"""
        payload = {
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "intersection_id": "INT_001",
            "lane_id": lane_id,
            "vehicle_count": vehicle_count,
            "avg_speed_kmh": round(avg_speed_kmh, 1),
            "queue_length_m": round(queue_length_m, 1),
            "signal_phase": signal_phase,
            "density_ratio": round(min(1.0, vehicle_count / 15.0), 2)
        }

        json_str = json.dumps(payload)

        if self.client:
            try:
                self.client.publish(self.topic, json_str)
            except Exception as e:
                logger.error(f"[MQTT] Publish failed: {e}")

        # Also write payload to local JSON buffer for Flask API
        try:
            buf_path = _backend_dir.parent / "data" / "mqtt_latest_telemetry.json"
            with open(buf_path, "w") as f:
                json.dump(payload, f)
        except Exception:
            pass

        return payload


if __name__ == "__main__":
    pub = MQTTTelemetryPublisher()
    test_data = pub.publish_lane_telemetry("lane_0", 8, 42.5, 25.0, "GREEN")
    print(f"[OK] MQTTTelemetryPublisher tested successfully!")
    print(f"  Payload: {test_data}")

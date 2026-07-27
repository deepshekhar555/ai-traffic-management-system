import sys
from pathlib import Path

# Ensure backend and root paths are in sys.path
root_dir = Path(__file__).parent.parent.resolve()
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

try:
    from src.alert import AlertManager
    from src.live_camera import LiveCameraStream, MultiCameraManager
    from src.logger import logger
except ImportError:
    from backend.src.alert import AlertManager
    from backend.src.live_camera import LiveCameraStream, MultiCameraManager
    from backend.src.logger import logger

import time


print("=" * 60)
print("Testing Alert System & Live Camera")
print("=" * 60)

# Test Alert Manager
print("\n[1] Testing Alert Manager...")
alert_mgr = AlertManager()

# Create various alerts
print("\nCreating sample alerts:")
alert1 = alert_mgr.high_traffic_alert("Main Road Junction", 45, 0.85)
print(f"  [OK] High Traffic Alert: {alert1['message']}")

alert2 = alert_mgr.hsr_status_alert("CLOSING", 0.0)
print(f"  [OK] HSR Status Alert: {alert2['message']}")

alert3 = alert_mgr.accident_alert("Highway Exit 42", "SEVERE")
print(f"  [OK] Accident Alert: {alert3['message']}")

# Get statistics
stats = alert_mgr.get_alert_stats()
print(f"\nAlert Statistics:")
print(f"  Total Alerts: {stats['total_alerts']}")
print(f"  Active Alerts: {stats['active_alerts']}")
print(f"  By Type: {stats['by_type']}")
print(f"  By Severity: {stats['by_severity']}")

# Get active alerts
active = alert_mgr.get_active_alerts()
print(f"\nActive Alerts ({len(active)}):")
for alert in active:
    print(f"  [{alert['severity']}] {alert['type']}: {alert['message']}")

# Test resolving alert
print(f"\nResolving alert #{alert1['id']}...")
alert_mgr.resolve_alert(alert1['id'])
print(f"Active Alerts now: {len(alert_mgr.get_active_alerts())}")

# Test Live Camera
print("\n" + "=" * 60)
print("[2] Testing Live Camera System...")
print("=" * 60)

try:
    print("\nInitializing live camera stream...")
    camera = LiveCameraStream(camera_id="main_camera", source=0)
    camera.start_stream()
    
    print("[OK] Camera stream started")
    info = camera.get_stream_info()
    print(f"  Camera ID: {info['camera_id']}")
    print(f"  Resolution: {info['width']}x{info['height']}")
    print(f"  FPS: {info['fps']}")
    print(f"  Running: {info['running']}")
    
    # Wait for some frames
    print("\nCapturing frames for 3 seconds...")
    time.sleep(3)
    
    # Get stream info
    info = camera.get_stream_info()
    print(f"  Frames captured: {info['frames_captured']}")
    print(f"  Current FPS: {info['fps']}")
    
    # Take a snapshot
    print("\nTaking snapshot...")
    snapshot = camera.take_snapshot()
    if snapshot:
        print(f"  [OK] Saved: {snapshot}")
    
    # Stop camera
    print("\nStopping camera stream...")
    camera.stop_stream()
    print("[OK] Camera stopped")

except Exception as e:
    print(f"✗ Camera Error: {e}")

# Test Multi-Camera Manager
print("\n" + "=" * 60)
print("[3] Testing Multi-Camera Manager...")
print("=" * 60)

try:
    print("\nInitializing multi-camera manager...")
    manager = MultiCameraManager()
    
    # Add camera
    print("Adding camera...")
    cam = manager.add_camera("cam_front", source=0)
    
    if cam:
        print("[OK] Camera added")
        
        # Start streams
        print("Starting all streams...")
        manager.start_all_streams()
        
        # Wait a moment
        time.sleep(2)
        
        # Get stream info
        streams = manager.get_streams_info()
        print("\nStream Information:")
        for cam_id, info in streams.items():
            print(f"  {info['camera_id']}: {info['frames_captured']} frames @ {info['fps']} FPS")
        
        # Stop
        print("\nStopping all streams...")
        manager.stop_all_streams()
        print("[OK] All streams stopped")

except Exception as e:
    print(f"[X] Multi-Camera Error: {e}")

print("\n" + "=" * 60)
print("[OK] All tests completed!")
print("=" * 60)


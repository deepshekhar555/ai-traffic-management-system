import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent.resolve()
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.traffic_detector import TrafficDetector
except ImportError:
    from backend.src.traffic_detector import TrafficDetector


print('Loading yolo26n traffic detector...')
try:
    detector = TrafficDetector()
    print('[OK] Detector loaded successfully!')
    model_name = getattr(detector.model, 'model_name', 'yolo26n') if hasattr(detector, 'model') else 'yolo26n'
    classes = getattr(detector, 'class_names', getattr(detector, 'vehicle_classes', []))
    print(f'  Model: {model_name}')
    print(f'  Vehicle classes: {classes}')
    sys.exit(0)

except Exception as e:
    print(f'[X] Error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)


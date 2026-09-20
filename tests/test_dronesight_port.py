import importlib.util
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MODULE_PATH = os.path.join(ROOT, 'backend', 'dashboard_app.py')

spec = importlib.util.spec_from_file_location('dashboard_app_mod', MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_dronesight_aerial_telemetry_endpoint_exists():
    response = module.app.test_client().get('/api/drone-aerial-telemetry')
    assert response.status_code == 200
    data = response.get_json()
    assert 'detections' in data
    assert 'total_count' in data
    assert 'model_loaded' in data
    assert isinstance(data['detections'], list)

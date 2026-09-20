import importlib.util
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MODULE_PATH = os.path.join(ROOT, 'backend', 'dashboard_app.py')

spec = importlib.util.spec_from_file_location('dashboard_app_mod', MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_lidar_camera_perception_endpoint_exists_and_has_payload():
    response = module.app.test_client().get('/api/lidar-camera-perception')
    assert response.status_code == 200
    data = response.get_json()
    assert 'status' in data
    assert data['status'] in {'ONLINE', 'DEGRADED'}
    assert 'objects' in data
    assert isinstance(data['objects'], list)
    assert 'metrics' in data
    assert 'fusion_mode' in data

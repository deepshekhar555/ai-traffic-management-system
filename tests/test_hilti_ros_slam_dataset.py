import importlib.util
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MODULE_PATH = os.path.join(ROOT, 'backend', 'dashboard_app.py')

spec = importlib.util.spec_from_file_location('dashboard_app_mod', MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_hilti_ros_slam_endpoint_exists():
    response = module.app.test_client().get('/api/hilti-ros-slam')
    assert response.status_code == 200
    data = response.get_json()
    assert 'dataset_name' in data
    assert 'sensor_summary' in data
    assert 'trajectory_points' in data
    assert 'ros_runtime' in data
    assert isinstance(data['trajectory_points'], list)
    assert isinstance(data['sensor_summary'], dict)

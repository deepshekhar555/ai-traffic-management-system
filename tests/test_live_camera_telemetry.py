import importlib.util
import json
import os


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MODULE_PATH = os.path.join(ROOT, 'backend', 'dashboard_app.py')


spec = importlib.util.spec_from_file_location('dashboard_app_mod', MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_live_camera_telemetry_does_not_invent_data_without_a_source(tmp_path, monkeypatch):
    monkeypatch.setattr(module, '_root_dir', tmp_path)
    response = module.app.test_client().get('/api/live-camera-telemetry')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'unavailable'
    assert data['spatial_perception'] is None
    assert 'vehicle_count' not in data


def test_live_camera_telemetry_requires_explicit_source_verification(tmp_path, monkeypatch):
    monkeypatch.setattr(module, '_root_dir', tmp_path)
    data_dir = tmp_path / 'data'
    data_dir.mkdir()
    telemetry = {
        'verified': True,
        'vehicle_count': 3,
        'spatial_perception': {'active_world_objects': 3, 'calibrated_cameras': ['test-camera']}
    }
    with open(data_dir / 'live_camera_telemetry.json', 'w', encoding='utf-8') as telemetry_file:
        json.dump(telemetry, telemetry_file)

    response = module.app.test_client().get('/api/live-camera-telemetry')
    assert response.status_code == 200
    result = response.get_json()
    assert result['status'] == 'verified'
    assert result['vehicle_count'] == 3


def test_live_camera_telemetry_rejects_unverified_file_data(tmp_path, monkeypatch):
    monkeypatch.setattr(module, '_root_dir', tmp_path)
    data_dir = tmp_path / 'data'
    data_dir.mkdir()
    with open(data_dir / 'live_camera_telemetry.json', 'w', encoding='utf-8') as telemetry_file:
        json.dump({'vehicle_count': 14, 'spatial_perception': {'active_world_objects': 23}}, telemetry_file)

    response = module.app.test_client().get('/api/live-camera-telemetry')
    assert response.status_code == 200
    result = response.get_json()
    assert result['status'] == 'unverified'
    assert result['spatial_perception'] is None
    assert 'vehicle_count' not in result


def test_unmeasured_dashboard_metrics_are_not_fabricated():
    client = module.app.test_client()

    research = client.get('/api/research-metrics').get_json()
    assert research['status'] == 'unavailable'
    assert research['q_learning_reward'] is None
    assert research['ttc_min_seconds'] is None

    hardware = client.get('/api/hardware-status').get_json()
    assert hardware['status'] == 'unverified'
    assert hardware['edge_fps'] is None
    assert hardware['rpi_gpio_status'] is None

    impact = client.get('/api/eco-impact').get_json()
    assert impact['status'] == 'not_measured'
    assert impact['co2_saved_kg'] is None
    assert impact['fuel_saved_liters'] is None

    assert client.get('/api/multi-camera-nodes').get_json() == []


def test_legacy_dashboard_renders_prototype_boundaries():
    response = module.app.test_client().get('/legacy-dashboard')
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'field performance have not been verified' in page
    assert 'Sample data is not field evidence.' in page
    assert 'background: #0a1424' in page


class FakeCamera:
    def __init__(self, opened=True, frames=None):
        self.opened = opened
        self.frames = list(frames or [])
        self.released = False

    def isOpened(self):
        return self.opened and not self.released

    def read(self):
        if self.frames:
            frame = self.frames.pop(0)
            return (frame is not None, frame)
        return False, None

    def release(self):
        self.released = True


def test_webcam_route_returns_unavailable_without_a_camera_frame(monkeypatch):
    camera = FakeCamera(opened=False)
    monkeypatch.setattr(module, '_open_physical_webcam', lambda: camera)

    response = module.app.test_client().get('/video_feed/webcam')
    assert response.status_code == 503
    assert response.get_json()['status'] == 'unavailable'
    assert 'could not be opened' in response.get_json()['message']
    assert camera.released


def test_webcam_route_streams_received_frame_and_releases_camera(monkeypatch):
    frame = module.np.full((32, 48, 3), (30, 180, 90), dtype=module.np.uint8)
    camera = FakeCamera(frames=[frame])
    monkeypatch.setattr(module, '_open_physical_webcam', lambda: camera)

    response = module.app.test_client().get('/video_feed/webcam', buffered=False)
    assert response.status_code == 200
    assert response.mimetype == 'multipart/x-mixed-replace'
    chunk = next(iter(response.response))
    assert b'Content-Type: image/jpeg' in chunk
    encoded = chunk.split(b'\r\n\r\n', 1)[1].split(b'\r\n', 1)[0]
    decoded = module.cv2.imdecode(module.np.frombuffer(encoded, dtype=module.np.uint8), module.cv2.IMREAD_COLOR)
    assert decoded is not None
    assert decoded.shape[:2] == (32, 48)
    response.close()
    assert camera.released


def test_remote_camera_route_requires_configuration(monkeypatch):
    monkeypatch.delitem(module._custom_ip_cams, 4, raising=False)
    response = module.app.test_client().get('/video_feed/4')
    assert response.status_code == 503
    assert response.get_json()['status'] == 'unavailable'


def test_camera_verification_page_does_not_fall_back_to_simulated_feed():
    response = module.app.test_client().get('/webcam')
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'onerror="handleFeedError()"' in page
    assert "this.src='/video_feed/1'" not in page
    assert 'Detection accuracy · not measured' in page
    assert 'Illustrative simulation — lane 1' in page
    assert 'LAST DETECTED LICENSE PLATE' not in page

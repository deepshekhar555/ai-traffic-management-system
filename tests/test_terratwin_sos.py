import pytest

from backend.dashboard_app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def test_terratwin_sos_page_loads(client):
    response = client.get('/terratwin-sos')
    assert response.status_code == 200
    assert b'TerraTwin SOS' in response.data


def test_terratwin_sos_api_returns_hazard_data(client):
    response = client.get('/api/emergency-sos')
    assert response.status_code == 200
    payload = response.get_json()
    assert payload.get('status') == 'ONLINE'
    assert 'overview' in payload
    assert len(payload.get('hazards', [])) >= 1

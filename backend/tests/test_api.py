from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_and_catalogue():
    assert client.get('/health').json()['status'] == 'ok'
    assert client.get('/catalog').status_code == 200

def test_editor_cannot_publish():
    response = client.post('/admin/catalog/publish', headers={'X-User': 'editor@example.com'})
    assert response.status_code == 403

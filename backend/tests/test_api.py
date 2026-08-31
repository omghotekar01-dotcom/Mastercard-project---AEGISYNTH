from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_and_dashboard():
    assert client.get('/health').status_code == 200
    page = client.get('/')
    assert page.status_code == 200
    assert 'AEGISYNTH' in page.text

def test_lab_api_schema():
    res = client.get('/api/v1/lab/run?seed=42&generations=2')
    assert res.status_code == 200
    data = res.json()
    assert data['final_policy']['verified'] is True
    assert data['metrics']['benign_acceptance_rate'] >= 0.98

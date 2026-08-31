from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app

client = TestClient(app)


def test_health_readiness_and_dashboard():
    health = client.get('/health')
    assert health.status_code == 200
    assert health.json()['status'] == 'ok'

    ready = client.get('/ready')
    assert ready.status_code == 200
    ready_data = ready.json()
    assert ready_data['status'] == 'ready'
    assert ready_data['checks']['dashboard_present'] is True
    assert ready_data['checks']['z3_formal_verifier_available'] is True
    assert ready_data['formal_verifier'] == 'z3'

    page = client.get('/')
    assert page.status_code == 200
    assert 'AEGISYNTH' in page.text


def test_readiness_fails_closed_without_formal_verifier(monkeypatch):
    monkeypatch.setattr(main_module, 'HAS_Z3', False)
    res = client.get('/ready')
    assert res.status_code == 503
    data = res.json()
    assert data['status'] == 'not_ready'
    assert data['checks']['z3_formal_verifier_available'] is False
    assert data['formal_verifier'] == 'unavailable'


def test_meta_is_explicitly_synthetic_and_governed():
    res = client.get('/api/v1/meta')
    assert res.status_code == 200
    data = res.json()
    assert data['production_claim'] is False
    assert data['benchmark_seed'] == 42
    assert set(data['responsible_actions']) == {'STEP_UP', 'REVIEW'}
    assert 'synthetic' in data['scope'].lower()


def test_reproducible_demo_matches_committed_benchmark():
    res = client.get('/api/v1/demo')
    assert res.status_code == 200
    data = res.json()
    assert data['seed'] == 42
    assert data['baseline_attack_success_rate'] == 0.5383
    assert data['final_attack_success_rate'] == 0.0743
    assert data['metrics']['final_fraud_coverage'] == 0.9257
    assert data['metrics']['benign_acceptance_rate'] == 0.9943
    assert data['final_policy']['verified'] is True
    assert data['final_policy']['action'] in {'STEP_UP', 'REVIEW'}


def test_runtime_self_check_passes_all_contracts():
    res = client.get('/api/v1/self-check')
    assert res.status_code == 200
    data = res.json()
    assert data['status'] == 'pass'
    assert data['checks']
    assert data['checks']['z3_formal_verifier_available'] is True
    assert all(data['checks'].values())
    assert 'synthetic' in data['scope'].lower()


def test_runtime_self_check_reports_missing_formal_verifier(monkeypatch):
    monkeypatch.setattr(main_module, 'HAS_Z3', False)
    res = client.get('/api/v1/self-check')
    assert res.status_code == 200
    data = res.json()
    assert data['status'] == 'fail'
    assert data['checks']['z3_formal_verifier_available'] is False


def test_lab_api_schema():
    res = client.get('/api/v1/lab/run?seed=42&generations=2')
    assert res.status_code == 200
    data = res.json()
    assert data['final_policy']['verified'] is True
    assert data['metrics']['benign_acceptance_rate'] >= 0.98


def test_lab_rejects_out_of_bounds_inputs():
    assert client.get('/api/v1/lab/run?seed=-1&generations=4').status_code == 422
    assert client.get('/api/v1/lab/run?seed=42&generations=99').status_code == 422

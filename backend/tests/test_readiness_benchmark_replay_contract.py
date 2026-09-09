from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app

client = TestClient(app)


def test_readiness_fails_closed_when_benchmark_runtime_breaks(monkeypatch):
    def broken_benchmark():
        raise RuntimeError("sensitive benchmark engine details")

    monkeypatch.setattr(main_module, "_benchmark", broken_benchmark)

    response = client.get("/ready")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "not_ready"
    assert data["checks"]["benchmark_replay_operational"] is False
    assert "sensitive benchmark engine details" not in response.text


def test_readiness_fails_closed_when_benchmark_claim_drifts(monkeypatch):
    benchmark = main_module._benchmark()
    drifted = benchmark.model_copy(
        update={"final_attack_success_rate": benchmark.final_attack_success_rate + 0.0001}
    )
    monkeypatch.setattr(main_module, "_benchmark", lambda: drifted)

    response = client.get("/ready")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "not_ready"
    assert data["checks"]["benchmark_replay_operational"] is False

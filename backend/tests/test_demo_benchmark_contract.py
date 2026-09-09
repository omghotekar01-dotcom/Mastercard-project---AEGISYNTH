from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app

client = TestClient(app)


def test_demo_returns_committed_benchmark_when_contract_matches():
    response = client.get("/api/v1/demo")

    assert response.status_code == 200
    payload = response.json()
    assert payload["seed"] == main_module.BENCHMARK_SEED
    assert payload["attack_family"] == main_module.ATTACK_FAMILY
    assert len(payload["iterations"]) == main_module.BENCHMARK_GENERATIONS
    assert (
        payload["baseline_attack_success_rate"]
        == main_module.BENCHMARK_CONTRACT["baseline_attack_success_rate"]
    )
    assert (
        payload["final_attack_success_rate"]
        == main_module.BENCHMARK_CONTRACT["final_attack_success_rate"]
    )
    assert (
        payload["metrics"]["final_fraud_coverage"]
        == main_module.BENCHMARK_CONTRACT["final_fraud_coverage"]
    )
    assert (
        payload["metrics"]["benign_acceptance_rate"]
        == main_module.BENCHMARK_CONTRACT["benign_acceptance_rate"]
    )


def test_demo_fails_closed_when_committed_benchmark_drifts(monkeypatch):
    benchmark = main_module._benchmark()
    drifted = benchmark.model_copy(
        update={"final_attack_success_rate": benchmark.final_attack_success_rate + 0.0001}
    )
    monkeypatch.setattr(main_module, "_benchmark", lambda: drifted)

    response = client.get("/api/v1/demo")

    assert response.status_code == 503
    assert response.json() == {
        "detail": {
            "status": "unavailable",
            "reason": "benchmark_replay_failed",
            "scope": "synthetic defensive payment-security laboratory",
        }
    }
    assert "0.0001" not in response.text
    assert "committed contract" not in response.text

from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app

client = TestClient(app)


def test_readiness_fails_closed_when_review_package_build_breaks(monkeypatch):
    def broken_review_package(_result):
        raise RuntimeError("sensitive review-package verifier details")

    monkeypatch.setattr(main_module, "build_review_package", broken_review_package)

    response = client.get("/ready")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "not_ready"
    assert data["checks"]["review_package_operational"] is False
    assert "sensitive review-package verifier details" not in response.text


def test_readiness_fails_closed_when_review_package_verification_rejects(monkeypatch):
    monkeypatch.setattr(main_module, "verify_review_package", lambda _package: False)

    response = client.get("/ready")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "not_ready"
    assert data["checks"]["review_package_operational"] is False


def test_readiness_uses_one_authoritative_benchmark_replay(monkeypatch):
    benchmark = main_module._benchmark()
    replay_calls = 0
    review_inputs = []

    def replay_once():
        nonlocal replay_calls
        replay_calls += 1
        return benchmark

    def verify_review_from_same_replay(result):
        review_inputs.append(result)
        return True

    monkeypatch.setattr(main_module, "_benchmark", replay_once)
    monkeypatch.setattr(main_module, "_review_package_operational", verify_review_from_same_replay)
    monkeypatch.setattr(main_module, "_formal_verifier_operational", lambda: True)
    monkeypatch.setattr(main_module, "HAS_Z3", True)

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert replay_calls == 1
    assert len(review_inputs) == 1
    assert review_inputs[0] is benchmark

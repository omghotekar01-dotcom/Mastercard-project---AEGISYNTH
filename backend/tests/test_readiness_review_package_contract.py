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

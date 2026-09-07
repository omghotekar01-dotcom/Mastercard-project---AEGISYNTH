from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app


client = TestClient(app)


def test_self_check_reports_structured_503_when_artifact_verifier_crashes(monkeypatch):
    def broken_artifact_verifier(_package):
        raise RuntimeError("artifact verifier unavailable")

    monkeypatch.setattr(main_module, "verify_review_package", broken_artifact_verifier)

    response = client.get("/api/v1/self-check")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "fail"
    assert payload["checks"]["benchmark_runtime_operational"] is True
    assert payload["checks"]["z3_formal_verifier_operational"] is True
    assert payload["checks"]["artifact_integrity"] is False
    assert payload["checks"]["human_approval_required"] is False
    assert payload["checks"]["not_auto_deployed"] is False
    assert payload["scope"] == "synthetic prototype runtime self-check"

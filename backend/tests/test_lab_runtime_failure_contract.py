from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app

client = TestClient(app)


def test_lab_run_fails_closed_with_structured_503_and_no_internal_leak(monkeypatch):
    class BrokenEngine:
        def __init__(self, seed: int):
            self.seed = seed

        def run(self, *, generations: int, attack_family: str):
            raise RuntimeError(
                f"sensitive solver internals seed={self.seed} "
                f"generations={generations} family={attack_family}"
            )

    monkeypatch.setattr(main_module, "AegisynthEngine", BrokenEngine)

    response = client.get("/api/v1/lab/run?seed=7&generations=2")

    assert response.status_code == 503
    assert response.json()["detail"] == {
        "status": "unavailable",
        "reason": "lab_runtime_failed",
        "scope": "synthetic defensive payment-security laboratory",
    }
    assert "sensitive solver internals" not in response.text
    assert "seed=7" not in response.text

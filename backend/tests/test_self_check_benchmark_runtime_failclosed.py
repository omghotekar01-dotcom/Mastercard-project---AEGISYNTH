from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app


client = TestClient(app)


def test_self_check_reports_structured_503_when_benchmark_runtime_crashes(monkeypatch):
    def broken_benchmark():
        raise RuntimeError("synthetic benchmark unavailable")

    monkeypatch.setattr(main_module, "_benchmark", broken_benchmark)

    response = client.get("/api/v1/self-check")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "fail"
    assert payload["checks"] == {"benchmark_runtime_operational": False}
    assert payload["scope"] == "synthetic prototype runtime self-check"

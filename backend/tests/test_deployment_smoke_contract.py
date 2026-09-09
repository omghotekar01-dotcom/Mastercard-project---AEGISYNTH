import pytest

import smoke


def test_deployment_smoke_requires_latency_budget_evidence(monkeypatch):
    checks_without_latency = {
        name: True
        for name in smoke.REQUIRED_SELF_CHECKS
        if name != "latency_budget"
    }
    responses = {
        "/health": (200, {"status": "ok", "version": "test"}),
        "/ready": (200, {"status": "ready", "checks": {"runtime": True}}),
        "/api/v1/self-check": (200, {"status": "pass", "checks": checks_without_latency}),
    }

    monkeypatch.setattr(smoke, "fetch_json", lambda _base_url, path: responses[path])

    with pytest.raises(AssertionError, match="latency_budget"):
        smoke.run("http://example.invalid")

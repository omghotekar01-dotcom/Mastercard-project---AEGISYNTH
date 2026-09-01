import pytest

import smoke


def test_smoke_probe_accepts_complete_runtime_contract(monkeypatch):
    responses = {
        "/health": (200, {"status": "ok", "version": "test"}),
        "/ready": (200, {"status": "ready", "checks": {"dashboard_present": True, "z3_formal_verifier_available": True}}),
        "/api/v1/self-check": (
            200,
            {"status": "pass", "checks": {name: True for name in smoke.REQUIRED_SELF_CHECKS}},
        ),
        "/api/v1/demo": (
            200,
            {"seed": 42, "final_policy": {"verified": True, "action": "STEP_UP"}},
        ),
    }

    monkeypatch.setattr(smoke, "fetch_json", lambda _base, path: responses[path])
    smoke.run("http://example.invalid")


def test_smoke_probe_fails_closed_when_runtime_check_is_false(monkeypatch):
    checks = {name: True for name in smoke.REQUIRED_SELF_CHECKS}
    checks["artifact_integrity"] = False
    responses = {
        "/health": (200, {"status": "ok", "version": "test"}),
        "/ready": (200, {"status": "ready", "checks": {"dashboard_present": True, "z3_formal_verifier_available": True}}),
        "/api/v1/self-check": (200, {"status": "pass", "checks": checks}),
        "/api/v1/demo": (200, {"seed": 42, "final_policy": {"verified": True, "action": "STEP_UP"}}),
    }

    monkeypatch.setattr(smoke, "fetch_json", lambda _base, path: responses[path])
    with pytest.raises(AssertionError):
        smoke.run("http://example.invalid")


def test_smoke_probe_fails_when_contract_check_is_missing(monkeypatch):
    checks = {name: True for name in smoke.REQUIRED_SELF_CHECKS}
    checks.pop("human_approval_required")
    responses = {
        "/health": (200, {"status": "ok", "version": "test"}),
        "/ready": (200, {"status": "ready", "checks": {"dashboard_present": True, "z3_formal_verifier_available": True}}),
        "/api/v1/self-check": (200, {"status": "pass", "checks": checks}),
        "/api/v1/demo": (200, {"seed": 42, "final_policy": {"verified": True, "action": "STEP_UP"}}),
    }

    monkeypatch.setattr(smoke, "fetch_json", lambda _base, path: responses[path])
    with pytest.raises(AssertionError):
        smoke.run("http://example.invalid")

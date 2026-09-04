import pytest

import app.engine as engine_module
from app.engine import AegisynthEngine


def test_engine_aborts_when_policy_verification_fails(monkeypatch):
    calls = []

    def reject_policy(policy, max_fpr):
        calls.append((policy.policy_id, max_fpr))
        return False, ["synthetic verifier failure"]

    monkeypatch.setattr(engine_module, "verify_policy", reject_policy)

    with pytest.raises(
        RuntimeError,
        match=r"Policy verification failed at generation 1; refusing to emit unverified lab evidence",
    ):
        AegisynthEngine(seed=42).run(generations=2)

    assert len(calls) == 1
    assert calls[0][1] == 0.02


def test_engine_marks_candidate_verified_only_after_success(monkeypatch):
    observed_verified_state = []

    def accept_policy(policy, max_fpr):
        observed_verified_state.append(policy.verified)
        return True, ["verified"]

    monkeypatch.setattr(engine_module, "verify_policy", accept_policy)

    result = AegisynthEngine(seed=42).run(generations=1)

    assert observed_verified_state == [False]
    assert result.final_policy.verified is True
    assert result.verification_notes == ["verified"]

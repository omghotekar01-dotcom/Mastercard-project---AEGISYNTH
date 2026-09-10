from z3 import sat

from app import verification
from app.contracts import DEFAULT_Z3_TIMEOUT_MS
from app.schemas import Policy


class _CapturingSolver:
    configured_timeout = None

    def set(self, **kwargs: object) -> None:
        type(self).configured_timeout = kwargs.get("timeout")

    def add(self, *_constraints: object) -> None:
        pass

    def check(self):
        return sat


def test_verifier_uses_shared_bounded_z3_timeout(monkeypatch):
    assert DEFAULT_Z3_TIMEOUT_MS == 1000
    assert isinstance(DEFAULT_Z3_TIMEOUT_MS, int)
    assert DEFAULT_Z3_TIMEOUT_MS > 0

    _CapturingSolver.configured_timeout = None
    monkeypatch.setattr(verification, "Solver", _CapturingSolver)

    policy = Policy(
        policy_id="z3-timeout-contract",
        merchant_age_max=72,
        first_time_card_ratio_min=0.64,
        settlement_change_days_max=14,
        temporal_burst_score_min=0.64,
        action="STEP_UP",
        false_positive_rate=0.01,
        estimated_latency_ms=0.35,
    )

    verified, _notes = verification.verify_policy(policy)

    assert verified is True
    assert _CapturingSolver.configured_timeout == DEFAULT_Z3_TIMEOUT_MS

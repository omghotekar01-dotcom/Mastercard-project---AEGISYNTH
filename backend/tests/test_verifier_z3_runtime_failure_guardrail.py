from app import verification
from app.schemas import Policy


class _FailingSolver:
    """Minimal solver double that models a Z3 runtime failure during verification."""

    def set(self, **_kwargs: object) -> None:
        pass

    def add(self, *_constraints: object) -> None:
        pass

    def check(self):
        raise RuntimeError("synthetic solver failure")


def test_verifier_fails_closed_when_z3_runtime_errors(monkeypatch):
    """A solver runtime exception must never be promoted to verified evidence."""
    monkeypatch.setattr(verification, "Solver", _FailingSolver)

    policy = Policy(
        policy_id="z3-runtime-failure-guardrail",
        merchant_age_max=72,
        first_time_card_ratio_min=0.64,
        settlement_change_days_max=14,
        temporal_burst_score_min=0.64,
        action="STEP_UP",
        false_positive_rate=0.01,
        estimated_latency_ms=0.35,
    )

    verified, notes = verification.verify_policy(policy)

    assert verified is False
    assert notes == ["Formal verification failed closed: Z3 runtime error"]

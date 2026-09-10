from z3 import unknown

from app import verification
from app.schemas import Policy


class _InconclusiveSolver:
    """Minimal solver double that models Z3 returning `unknown`."""

    def set(self, **_kwargs: object) -> None:
        pass

    def add(self, *_constraints: object) -> None:
        pass

    def check(self):
        return unknown


def test_verifier_fails_closed_when_z3_is_inconclusive(monkeypatch):
    """An `unknown` solver result must never be promoted to verified evidence."""
    monkeypatch.setattr(verification, "Solver", _InconclusiveSolver)

    policy = Policy(
        policy_id="z3-inconclusive-guardrail",
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
    assert notes == ["Formal verification inconclusive: Z3 did not return sat or unsat"]

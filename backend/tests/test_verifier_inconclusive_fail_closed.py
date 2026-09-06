import pytest

import app.verification as verification
from app.schemas import Policy


class _InconclusiveSolver:
    """Minimal solver double that models Z3 returning unknown/inconclusive."""

    def set(self, **_kwargs):
        return None

    def add(self, *_constraints):
        return None

    def check(self):
        return object()


@pytest.mark.skipif(not verification.HAS_Z3, reason="z3-solver is required for verifier contract tests")
def test_verifier_fails_closed_when_z3_is_inconclusive(monkeypatch):
    """A timeout/unknown formal result must never be promoted to an approved policy."""
    policy = Policy(
        policy_id="external-review-policy",
        merchant_age_max=72,
        first_time_card_ratio_min=0.64,
        settlement_change_days_max=14,
        temporal_burst_score_min=0.70,
        action="STEP_UP",
        fraud_coverage=0.90,
        false_positive_rate=0.01,
        estimated_latency_ms=0.35,
        counterexamples_remaining=0,
    )
    monkeypatch.setattr(verification, "Solver", _InconclusiveSolver)

    verified, notes = verification.verify_policy(policy)

    assert verified is False
    assert notes == ["Formal verification inconclusive: Z3 did not return sat or unsat"]

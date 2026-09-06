import pytest

import app.verification as verification
from app.schemas import Policy


class _RecordingSolver:
    last_instance = None

    def __init__(self):
        self.timeout_ms = None
        self.checked = False
        _RecordingSolver.last_instance = self

    def set(self, **kwargs):
        self.timeout_ms = kwargs.get("timeout")

    def add(self, *_constraints):
        return None

    def check(self):
        self.checked = True
        return verification.sat


@pytest.mark.skipif(not verification.HAS_Z3, reason="z3-solver is required for verifier contract tests")
def test_verifier_applies_bounded_z3_timeout_before_solver_check(monkeypatch):
    """Formal verification must remain time-bounded so API and review paths cannot hang indefinitely."""
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
    monkeypatch.setattr(verification, "Solver", _RecordingSolver)

    verified, _notes = verification.verify_policy(policy)

    solver = _RecordingSolver.last_instance
    assert verified is True
    assert solver is not None
    assert solver.timeout_ms == verification.DEFAULT_Z3_TIMEOUT_MS == 1000
    assert solver.checked is True

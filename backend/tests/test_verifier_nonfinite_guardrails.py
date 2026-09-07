import math

import pytest

from app.engine import AegisynthEngine
from app.verification import verify_policy


@pytest.mark.parametrize("max_fpr", [math.nan, math.inf, -math.inf])
def test_verifier_rejects_nonfinite_false_positive_budgets(max_fpr):
    """NaN/inf business budgets must never weaken the false-positive guardrail."""
    policy = AegisynthEngine(seed=42).run(generations=1).final_policy

    verified, notes = verify_policy(policy, max_fpr=max_fpr)

    assert verified is False
    assert notes == ["Verifier configuration invalid: max_fpr must be finite and within [0, 1]"]


@pytest.mark.parametrize("max_latency_ms", [math.nan, math.inf, -math.inf])
def test_verifier_rejects_nonfinite_latency_budgets(max_latency_ms):
    """NaN/inf latency budgets must fail closed before formal verification."""
    policy = AegisynthEngine(seed=42).run(generations=1).final_policy

    verified, notes = verify_policy(policy, max_latency_ms=max_latency_ms)

    assert verified is False
    assert notes == ["Verifier configuration invalid: max_latency_ms must be finite and > 0"]


@pytest.mark.parametrize(
    "field",
    [
        "merchant_age_max",
        "first_time_card_ratio_min",
        "settlement_change_days_max",
        "temporal_burst_score_min",
        "fraud_coverage",
        "false_positive_rate",
        "estimated_latency_ms",
    ],
)
def test_verifier_rejects_schema_bypassed_nonfinite_policy_fields(field):
    """Malformed nonfinite policy numerics must not reach Z3 or business comparisons."""
    policy = AegisynthEngine(seed=42).run(generations=1).final_policy
    policy.__dict__[field] = math.nan

    verified, notes = verify_policy(policy)

    assert verified is False
    assert notes
    assert notes[0].startswith("Policy numeric field invalid:")
    assert "finite" in notes[0]

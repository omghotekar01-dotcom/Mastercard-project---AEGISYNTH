import pytest

from app.engine import AegisynthEngine
from app.verification import verify_policy


@pytest.mark.parametrize("max_fpr", [False, True])
def test_verifier_rejects_boolean_false_positive_budgets(max_fpr):
    """Python booleans must not masquerade as numeric false-positive budgets."""
    policy = AegisynthEngine(seed=42).run(generations=1).final_policy

    verified, notes = verify_policy(policy, max_fpr=max_fpr)

    assert verified is False
    assert notes == ["Verifier configuration invalid: max_fpr must be a real numeric value"]


@pytest.mark.parametrize("max_latency_ms", [False, True])
def test_verifier_rejects_boolean_latency_budgets(max_latency_ms):
    """Boolean latency values must fail closed before business or Z3 checks."""
    policy = AegisynthEngine(seed=42).run(generations=1).final_policy

    verified, notes = verify_policy(policy, max_latency_ms=max_latency_ms)

    assert verified is False
    assert notes == ["Verifier configuration invalid: max_latency_ms must be a real numeric value"]


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
def test_verifier_rejects_schema_bypassed_boolean_policy_numeric_fields(field):
    """Booleans must not enter policy numeric comparisons or formal constraints as 0/1."""
    policy = AegisynthEngine(seed=42).run(generations=1).final_policy
    policy.__dict__[field] = True

    verified, notes = verify_policy(policy)

    assert verified is False
    assert notes
    assert notes[0].startswith("Policy numeric field invalid:")
    assert "real numeric value" in notes[0]


@pytest.mark.parametrize("value", [False, True])
def test_verifier_rejects_boolean_counterexample_counts(value):
    """Boolean counterexample counts must not be accepted as integer robustness evidence."""
    policy = AegisynthEngine(seed=42).run(generations=1).final_policy
    policy.__dict__["counterexamples_remaining"] = value

    verified, notes = verify_policy(policy)

    assert verified is False
    assert notes == [
        "Policy numeric field invalid: counterexamples_remaining must be a non-negative integer"
    ]

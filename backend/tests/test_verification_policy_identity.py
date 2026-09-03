import pytest

from app.schemas import Policy
from app.verification import verify_policy


def _policy() -> Policy:
    return Policy(
        policy_id="ZD-01-048-50-07-50",
        merchant_age_max=48.0,
        first_time_card_ratio_min=0.50,
        settlement_change_days_max=7.0,
        temporal_burst_score_min=0.50,
        action="STEP_UP",
        fraud_coverage=0.90,
        false_positive_rate=0.01,
        estimated_latency_ms=0.35,
    )


@pytest.mark.parametrize(
    "bad_policy_id,expected_message",
    [
        ("X" * 81, "policy_id must be at most 80 characters"),
        (" ZD-01-048-50-07-50", "policy_id must not contain surrounding whitespace"),
        ("ZD-01-048-50-07-50 ", "policy_id must not contain surrounding whitespace"),
    ],
)
def test_verifier_rejects_schema_bypassed_policy_identity_drift(bad_policy_id, expected_message):
    policy = _policy()
    policy.__dict__["policy_id"] = bad_policy_id

    verified, notes = verify_policy(policy)

    assert verified is False
    assert notes == [f"Policy identity invalid: {expected_message}"]

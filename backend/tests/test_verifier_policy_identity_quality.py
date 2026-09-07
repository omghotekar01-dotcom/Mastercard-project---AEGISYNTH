import pytest

from app.schemas import Policy
from app.verification import verify_policy


@pytest.mark.parametrize("policy_id", ["---", "...", "___", "._-"])
def test_verifier_rejects_punctuation_only_policy_ids(policy_id: str) -> None:
    policy = Policy(
        policy_id=policy_id,
        merchant_age_max=24,
        first_time_card_ratio_min=0.5,
        settlement_change_days_max=7,
        temporal_burst_score_min=0.5,
        action="STEP_UP",
        fraud_coverage=0.9,
        false_positive_rate=0.01,
        estimated_latency_ms=0.35,
        counterexamples_remaining=0,
    )

    verified, notes = verify_policy(policy)

    assert verified is False
    assert notes == [
        "Policy identity invalid: policy_id must contain at least one ASCII letter or digit"
    ]

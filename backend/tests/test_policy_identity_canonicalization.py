import pytest

from app.schemas import Policy
from app.verification import verify_policy


def _policy() -> Policy:
    return Policy(
        policy_id="ZD-01-048-50-07-50",
        merchant_age_max=48,
        first_time_card_ratio_min=0.50,
        settlement_change_days_max=7,
        temporal_burst_score_min=0.50,
        action="STEP_UP",
        fraud_coverage=0.90,
        false_positive_rate=0.01,
        estimated_latency_ms=0.35,
    )


@pytest.mark.parametrize(
    "invalid_policy_id",
    [
        "ZD-01-048-50-07-50\x00suffix",
        "ZD-01-048-50-07-50/forged",
        "ZD-01-048-50-07-50:forged",
        "ZD-01-048-50-07-5０",
    ],
)
def test_verifier_rejects_noncanonical_policy_identity(invalid_policy_id):
    policy = _policy().model_copy(update={"policy_id": invalid_policy_id})

    verified, notes = verify_policy(policy)

    assert verified is False
    assert notes == [
        "Policy identity invalid: policy_id may contain only ASCII letters, digits, '.', '_', and '-'"
    ]

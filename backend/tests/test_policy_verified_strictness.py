import pytest
from pydantic import ValidationError

from app.schemas import Policy


def _policy_payload() -> dict:
    return {
        "policy_id": "strict-verification-evidence",
        "merchant_age_max": 24.0,
        "first_time_card_ratio_min": 0.5,
        "settlement_change_days_max": 7.0,
        "temporal_burst_score_min": 0.8,
    }


@pytest.mark.parametrize("value", [1, 0, "true", "false", "yes", None])
def test_policy_verified_rejects_coercible_non_booleans(value):
    payload = _policy_payload()
    payload["verified"] = value

    with pytest.raises(ValidationError):
        Policy.model_validate(payload)


@pytest.mark.parametrize("value", [True, False])
def test_policy_verified_accepts_only_real_booleans(value):
    payload = _policy_payload()
    payload["verified"] = value

    assert Policy.model_validate(payload).verified is value

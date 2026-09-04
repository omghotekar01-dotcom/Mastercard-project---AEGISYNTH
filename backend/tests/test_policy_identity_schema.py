import pytest
from pydantic import ValidationError

from app.schemas import Policy


def _policy(policy_id: str) -> Policy:
    return Policy(
        policy_id=policy_id,
        merchant_age_max=72.0,
        first_time_card_ratio_min=0.58,
        settlement_change_days_max=14.0,
        temporal_burst_score_min=0.58,
    )


@pytest.mark.parametrize(
    "policy_id",
    [
        " ZD-01-58-58",
        "ZD-01-58-58 ",
        "\tZD-01-58-58\n",
        "ZD-01-58 58",
        "ZD-01-58\t58",
        "ZD-01-58\n58",
    ],
)
def test_policy_schema_rejects_identity_whitespace(policy_id: str) -> None:
    with pytest.raises(ValidationError, match="policy_id must not contain whitespace"):
        _policy(policy_id)


def test_policy_schema_preserves_canonical_identity() -> None:
    policy_id = "ZD-01-58-58"

    assert _policy(policy_id).policy_id == policy_id

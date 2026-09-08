import pytest
from pydantic import ValidationError

from app.policy import score_policy
from app.schemas import Policy, Transaction


def _policy() -> Policy:
    return Policy(
        policy_id="AUDIT-1",
        merchant_age_max=48,
        first_time_card_ratio_min=0.5,
        settlement_change_days_max=7,
        temporal_burst_score_min=0.5,
        action="STEP_UP",
        estimated_latency_ms=0.35,
    )


def _tx(tx_id: str, *, fraud: bool) -> Transaction:
    return Transaction(
        tx_id=tx_id,
        amount=100.0,
        merchant_age_hours=24 if fraud else 400,
        first_time_card_ratio=0.9 if fraud else 0.1,
        settlement_change_days=2 if fraud else 100,
        temporal_burst_score=0.9 if fraud else 0.1,
        device_entropy=0.5,
        geo_velocity=0.0,
        label=int(fraud),
        attack_family="ghost_merchant_swarm" if fraud else "benign",
    )


@pytest.mark.parametrize("tx_id", ["---", "...", "___", "._-"])
def test_transaction_schema_rejects_punctuation_only_transaction_ids(tx_id: str) -> None:
    with pytest.raises(ValidationError, match="tx_id must contain at least one ASCII letter or digit"):
        _tx(tx_id, fraud=False)


@pytest.mark.parametrize("tx_id", ["---", "...", "___", "._-"])
@pytest.mark.parametrize("population", ["benign", "attack"])
def test_scoring_rejects_schema_bypassed_punctuation_only_transaction_ids(
    tx_id: str, population: str
) -> None:
    benign = [_tx("B-1", fraud=False)]
    attacks = [_tx("A-1", fraud=True)]
    if population == "benign":
        benign = [benign[0].model_copy(update={"tx_id": tx_id})]
    else:
        attacks = [attacks[0].model_copy(update={"tx_id": tx_id})]

    with pytest.raises(
        ValueError,
        match=rf"{population} evaluation transaction tx_id must contain at least one ASCII letter or digit",
    ):
        score_policy(_policy(), benign, attacks)
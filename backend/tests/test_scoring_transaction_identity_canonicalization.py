import pytest

from app.policy import score_policy
from app.schemas import Policy, Transaction


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


def _transaction(tx_id: str, label: int, attack_family: str) -> Transaction:
    return Transaction(
        tx_id=tx_id,
        amount=100.0,
        merchant_age_hours=24.0,
        first_time_card_ratio=0.75,
        settlement_change_days=2.0,
        temporal_burst_score=0.80,
        device_entropy=0.50,
        geo_velocity=10.0,
        label=label,
        attack_family=attack_family,
    )


@pytest.mark.parametrize(
    "tx_id",
    [
        "A/000001",
        "A:000001",
        "A\x0000001",
        "A-０００００１",
    ],
)
def test_score_policy_rejects_noncanonical_attack_transaction_ids(tx_id: str):
    benign = [_transaction("B-000001", 0, "benign")]
    attacks = [_transaction(tx_id, 1, "ghost_merchant_swarm")]

    with pytest.raises(ValueError, match="tx_id may contain only ASCII letters"):
        score_policy(_policy(), benign, attacks)


def test_score_policy_accepts_canonical_ascii_transaction_ids():
    benign = [_transaction("BENIGN_000001.v1", 0, "benign")]
    attacks = [_transaction("ATTACK-000001.v1", 1, "ghost_merchant_swarm")]

    score = score_policy(_policy(), benign, attacks)

    assert score.coverage == 1.0
    assert score.fpr == 1.0

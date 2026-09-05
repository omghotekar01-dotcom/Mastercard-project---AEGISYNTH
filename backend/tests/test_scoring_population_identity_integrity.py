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


def test_score_policy_rejects_duplicate_benign_transaction_ids():
    benign = [
        _transaction("B-000001", 0, "benign"),
        _transaction("B-000001", 0, "benign"),
    ]
    attacks = [_transaction("A-000001", 1, "ghost_merchant_swarm")]

    with pytest.raises(ValueError, match="benign evaluation population contains duplicate tx_id"):
        score_policy(_policy(), benign, attacks)


def test_score_policy_rejects_duplicate_attack_transaction_ids():
    benign = [_transaction("B-000001", 0, "benign")]
    attacks = [
        _transaction("A-000001", 1, "ghost_merchant_swarm"),
        _transaction("A-000001", 1, "ghost_merchant_swarm"),
    ]

    with pytest.raises(ValueError, match="attack evaluation population contains duplicate tx_id"):
        score_policy(_policy(), benign, attacks)


def test_score_policy_rejects_cross_population_transaction_id_overlap():
    benign = [_transaction("EVIDENCE-000001", 0, "benign")]
    attacks = [_transaction("EVIDENCE-000001", 1, "ghost_merchant_swarm")]

    with pytest.raises(ValueError, match="benign and attack evaluation populations share tx_id"):
        score_policy(_policy(), benign, attacks)


def test_score_policy_accepts_distinct_population_identities():
    benign = [_transaction("B-000001", 0, "benign")]
    attacks = [_transaction("A-000001", 1, "ghost_merchant_swarm")]

    score = score_policy(_policy(), benign, attacks)

    assert score.blocked_attacks == 1
    assert score.benign_hits == 1
    assert score.coverage == 1.0
    assert score.fpr == 1.0

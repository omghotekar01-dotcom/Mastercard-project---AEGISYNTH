from __future__ import annotations

import pytest

from app.policy import score_policy
from app.schemas import Policy, Transaction
from app.verification import verify_policy


def _compiler_policy() -> Policy:
    return Policy(
        policy_id="ZD-04-096-64-21-64",
        merchant_age_max=96,
        first_time_card_ratio_min=0.64,
        settlement_change_days_max=21,
        temporal_burst_score_min=0.64,
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


def _scoring_accepts(policy: Policy) -> bool:
    try:
        score_policy(
            policy,
            [_transaction("benign-1", 0, "benign")],
            [_transaction("attack-1", 1, "ghost_merchant_swarm")],
        )
    except ValueError:
        return False
    return True


@pytest.mark.parametrize(
    "mutation",
    [
        {"action": "REVIEW"},
        {"estimated_latency_ms": 0.10},
        {"merchant_age_max": 120},
        {"first_time_card_ratio_min": 0.70},
        {"settlement_change_days_max": 30},
        {"temporal_burst_score_min": 0.70},
        {"policy_id": "ZD-04-96-64-21-64"},
        {"policy_id": "ZD-09-096-64-21-64"},
        {"policy_id": "ZD-04-097-64-21-64", "merchant_age_max": 97},
        {"policy_id": "ZD-04-096-63-21-64", "first_time_card_ratio_min": 0.63},
        {"policy_id": "ZD-04-096-64-22-64", "settlement_change_days_max": 22},
        {"policy_id": "ZD-04-096-64-21-63", "temporal_burst_score_min": 0.63},
    ],
)
def test_scoring_and_formal_verification_reject_the_same_stale_compiler_lineage(
    mutation: dict[str, object],
) -> None:
    policy = _compiler_policy().model_copy(update=mutation)

    scoring_accepts = _scoring_accepts(policy)
    verified, _notes = verify_policy(policy)

    assert scoring_accepts is False
    assert verified is False


def test_scoring_and_formal_verification_accept_the_same_native_compiler_lineage() -> None:
    policy = _compiler_policy()

    scoring_accepts = _scoring_accepts(policy)
    verified, notes = verify_policy(policy)

    assert scoring_accepts is True
    assert verified is True
    assert any(note.startswith("Z3:") for note in notes)

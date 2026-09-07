import math

import pytest

from app.policy import score_policy
from app.schemas import Policy, Transaction


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


def _policy() -> Policy:
    return Policy(
        policy_id="external-review-1",
        merchant_age_max=48,
        first_time_card_ratio_min=0.5,
        settlement_change_days_max=7,
        temporal_burst_score_min=0.5,
        action="REVIEW",
        estimated_latency_ms=0.5,
    )


@pytest.mark.parametrize("latency", [True, False])
def test_scoring_rejects_boolean_latency_evidence(latency: bool) -> None:
    policy = _policy()
    policy.__dict__["estimated_latency_ms"] = latency

    with pytest.raises(ValueError, match="scored policy has non-numeric estimated_latency_ms"):
        score_policy(policy, [_tx("B-1", fraud=False)], [_tx("A-1", fraud=True)])


@pytest.mark.parametrize("latency", [math.nan, math.inf, -math.inf, -0.01])
def test_scoring_rejects_nonfinite_or_negative_latency_evidence(latency: float) -> None:
    policy = _policy()
    policy.__dict__["estimated_latency_ms"] = latency

    with pytest.raises(
        ValueError,
        match="scored policy estimated_latency_ms must be finite and >= 0",
    ):
        score_policy(policy, [_tx("B-1", fraud=False)], [_tx("A-1", fraud=True)])

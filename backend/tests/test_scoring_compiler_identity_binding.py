import pytest

from app.policy import score_policy
from app.schemas import Policy, Transaction


def _compiled_policy() -> Policy:
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


def _score(policy: Policy):
    return score_policy(
        policy,
        [_transaction("benign-1", 0, "benign")],
        [_transaction("attack-1", 1, "ghost_merchant_swarm")],
    )


def test_scoring_accepts_compiler_identity_when_encoded_semantics_match():
    score = _score(_compiled_policy())

    assert score.blocked_attacks == 1
    assert score.coverage == 1.0


def test_scoring_rejects_mutated_review_action_under_compiler_identity():
    policy = _compiled_policy().model_copy(update={"action": "REVIEW"})

    with pytest.raises(
        ValueError,
        match="scored compiler policy must retain the compiler STEP_UP action",
    ):
        _score(policy)


def test_scoring_rejects_mutated_latency_under_compiler_identity():
    policy = _compiled_policy().model_copy(update={"estimated_latency_ms": 0.10})

    with pytest.raises(
        ValueError,
        match="scored compiler policy must retain the compiler estimated latency",
    ):
        _score(policy)


@pytest.mark.parametrize(
    ("field", "tampered_value"),
    [
        ("merchant_age_max", 72),
        ("first_time_card_ratio_min", 0.58),
        ("settlement_change_days_max", 14),
        ("temporal_burst_score_min", 0.58),
    ],
)
def test_scoring_rejects_mutated_thresholds_under_stale_compiler_identity(field, tampered_value):
    policy = _compiled_policy().model_copy(update={field: tampered_value})

    with pytest.raises(
        ValueError,
        match="scored compiler policy ZD policy_id does not encode the scored thresholds",
    ):
        _score(policy)


def test_scoring_rejects_malformed_identity_that_claims_compiler_lineage():
    policy = _compiled_policy().model_copy(update={"policy_id": "ZD-01-48-50-07-50"})

    with pytest.raises(ValueError, match="scored compiler policy has malformed ZD policy_id"):
        _score(policy)


def test_scoring_rejects_out_of_range_generation_encoded_in_compiler_identity():
    policy = _compiled_policy().model_copy(update={"policy_id": "ZD-09-048-50-07-50"})

    with pytest.raises(ValueError, match="scored compiler policy generation must be within"):
        _score(policy)

import pytest

from app.policy import DefenceCompiler, score_policy
from app.schemas import Transaction


def _tx(tx_id: str, *, fraud: bool) -> Transaction:
    return Transaction(
        tx_id=tx_id,
        amount=100.0,
        merchant_age_hours=20.0 if fraud else 400.0,
        first_time_card_ratio=0.90 if fraud else 0.10,
        settlement_change_days=2.0 if fraud else 100.0,
        temporal_burst_score=0.90 if fraud else 0.10,
        device_entropy=0.50,
        geo_velocity=0.0,
        label=int(fraud),
        attack_family="ghost_merchant_swarm" if fraud else "benign",
    )


@pytest.mark.parametrize(
    "policy_id,expected_error",
    [
        (" ZD-01-048-50-07-50", "must not contain whitespace"),
        ("ZD-01-048-50-07-50 ", "must not contain whitespace"),
        ("ZD-01-048 50-07-50", "must not contain whitespace"),
        ("X" * 81, "must be at most 80 characters"),
    ],
)
def test_score_policy_rejects_schema_bypassed_noncanonical_policy_ids(policy_id, expected_error):
    benign = [_tx("B-1", fraud=False)]
    attacks = [_tx("A-1", fraud=True)]
    policy = DefenceCompiler(max_fpr=0.02).synthesize(benign, attacks, generation=1)
    policy.__dict__["policy_id"] = policy_id

    with pytest.raises(ValueError, match=expected_error):
        score_policy(policy, benign, attacks)


def test_score_policy_preserves_canonical_compiler_policy_identity():
    benign = [_tx("B-1", fraud=False)]
    attacks = [_tx("A-1", fraud=True)]
    policy = DefenceCompiler(max_fpr=0.02).synthesize(benign, attacks, generation=1)
    original_policy_id = policy.policy_id

    score = score_policy(policy, benign, attacks)

    assert policy.policy_id == original_policy_id
    assert not any(char.isspace() for char in policy.policy_id)
    assert len(policy.policy_id) <= 80
    assert score.coverage == 1.0
    assert score.fpr == 0.0

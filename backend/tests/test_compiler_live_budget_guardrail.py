import pytest

from app.policy import DefenceCompiler, score_policy
from app.schemas import Transaction


def _world():
    benign = [
        Transaction(
            tx_id="B-LIVE-1",
            amount=100.0,
            merchant_age_hours=400.0,
            first_time_card_ratio=0.10,
            settlement_change_days=100.0,
            temporal_burst_score=0.10,
            device_entropy=0.50,
            geo_velocity=0.0,
            label=0,
            attack_family="benign",
        )
    ]
    attacks = [
        Transaction(
            tx_id="A-LIVE-1",
            amount=100.0,
            merchant_age_hours=20.0,
            first_time_card_ratio=0.90,
            settlement_change_days=2.0,
            temporal_burst_score=0.90,
            device_entropy=0.50,
            geo_velocity=0.0,
            label=1,
            attack_family="ghost_merchant_swarm",
        )
    ]
    return benign, attacks


@pytest.mark.parametrize("invalid_budget", [True, False, "0.02", None])
def test_synthesize_rejects_non_numeric_budget_mutated_after_construction(invalid_budget):
    benign, attacks = _world()
    compiler = DefenceCompiler(max_fpr=0.02)
    compiler.max_fpr = invalid_budget

    with pytest.raises(ValueError, match="max_fpr must be a real numeric value"):
        compiler.synthesize(benign, attacks, generation=1)


@pytest.mark.parametrize(
    "invalid_budget",
    [-0.01, 1.01, float("nan"), float("inf"), float("-inf")],
)
def test_synthesize_rejects_out_of_domain_budget_mutated_after_construction(invalid_budget):
    benign, attacks = _world()
    compiler = DefenceCompiler(max_fpr=0.02)
    compiler.max_fpr = invalid_budget

    with pytest.raises(ValueError, match=r"max_fpr must be finite and within \[0, 1\]"):
        compiler.synthesize(benign, attacks, generation=1)


def test_synthesize_accepts_valid_live_budget_and_enforces_it():
    benign, attacks = _world()
    compiler = DefenceCompiler(max_fpr=0.02)
    compiler.max_fpr = 0.0

    policy = compiler.synthesize(benign, attacks, generation=1)
    score = score_policy(policy, benign, attacks)

    assert score.fpr <= compiler.max_fpr
    assert policy.action == "STEP_UP"

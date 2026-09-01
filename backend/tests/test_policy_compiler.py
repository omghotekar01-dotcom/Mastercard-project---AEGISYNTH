import pytest

from app.policy import DefenceCompiler, score_policy
from app.schemas import Transaction


def tx(tx_id: str, *, age: float, card: float, settle: float, burst: float, fraud: bool) -> Transaction:
    """Build a minimal synthetic transaction using the canonical API schema.

    Compiler tests intentionally keep non-policy features at deterministic neutral values so
    failures reflect compiler behaviour rather than fixture/schema drift.
    """
    return Transaction(
        tx_id=tx_id,
        amount=100.0,
        merchant_age_hours=age,
        first_time_card_ratio=card,
        settlement_change_days=settle,
        temporal_burst_score=burst,
        device_entropy=0.50,
        geo_velocity=0.0,
        label=int(fraud),
        attack_family="ghost_merchant_swarm" if fraud else "benign",
    )


def fixture_world():
    benign = [
        tx("B-1", age=400, card=0.10, settle=100, burst=0.10, fraud=False),
        tx("B-2", age=300, card=0.20, settle=90, burst=0.20, fraud=False),
        tx("B-3", age=220, card=0.30, settle=80, burst=0.30, fraud=False),
    ]
    attacks = [
        tx("A-1", age=20, card=0.90, settle=2, burst=0.90, fraud=True),
        tx("A-2", age=30, card=0.85, settle=3, burst=0.85, fraud=True),
        tx("A-3", age=40, card=0.80, settle=4, burst=0.80, fraud=True),
    ]
    assert all(row.label == 0 and row.attack_family == "benign" for row in benign)
    assert all(row.label == 1 and row.attack_family == "ghost_merchant_swarm" for row in attacks)
    return benign, attacks


def test_compiler_is_deterministic_for_identical_inputs():
    benign, attacks = fixture_world()
    compiler = DefenceCompiler(max_fpr=0.02)

    first = compiler.synthesize(benign, attacks, generation=1)
    second = compiler.synthesize(benign, attacks, generation=1)

    assert first.model_dump() == second.model_dump()


def test_compiler_output_respects_configured_false_positive_budget():
    benign, attacks = fixture_world()
    compiler = DefenceCompiler(max_fpr=0.02)
    policy = compiler.synthesize(benign, attacks, generation=2)
    score = score_policy(policy, benign, attacks)

    assert score.fpr <= compiler.max_fpr
    assert policy.false_positive_rate == round(score.fpr, 4)
    assert policy.fraud_coverage == round(score.coverage, 4)
    assert policy.action == "STEP_UP"


def test_empty_attack_set_does_not_create_fake_coverage():
    benign, _ = fixture_world()
    policy = DefenceCompiler(max_fpr=0.02).synthesize(benign, [], generation=3)
    score = score_policy(policy, benign, [])

    assert score.blocked_attacks == 0
    assert score.coverage == 0.0
    assert policy.fraud_coverage == 0.0


@pytest.mark.parametrize("invalid_budget", [-0.01, 1.01, float("nan"), float("inf"), float("-inf")])
def test_compiler_rejects_malformed_false_positive_budgets(invalid_budget):
    with pytest.raises(ValueError, match=r"max_fpr must be finite and within \[0, 1\]"):
        DefenceCompiler(max_fpr=invalid_budget)

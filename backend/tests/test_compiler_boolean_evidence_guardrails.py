import pytest

from app.policy import DefenceCompiler, score_policy
from app.schemas import Policy, Transaction


POLICY_FEATURES = (
    "merchant_age_hours",
    "first_time_card_ratio",
    "settlement_change_days",
    "temporal_burst_score",
)


def _world() -> tuple[list[Transaction], list[Transaction]]:
    benign = [
        Transaction(
            tx_id="B-BOOL-1",
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
            tx_id="A-BOOL-1",
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


def _policy() -> Policy:
    return Policy(
        policy_id="BOOL-GUARDRAIL",
        merchant_age_max=48.0,
        first_time_card_ratio_min=0.50,
        settlement_change_days_max=7.0,
        temporal_burst_score_min=0.50,
        action="STEP_UP",
        estimated_latency_ms=0.35,
    )


@pytest.mark.parametrize("field", POLICY_FEATURES)
@pytest.mark.parametrize("population", ["benign", "attack"])
def test_compiler_rejects_schema_bypassed_boolean_policy_features(field, population):
    """Booleans must never enter compiler evidence comparisons as Python 0/1 values."""
    benign, attacks = _world()
    target = benign[0] if population == "benign" else attacks[0]
    target.__dict__[field] = True

    with pytest.raises(ValueError, match=rf"{population} transaction .* has non-numeric {field}"):
        DefenceCompiler(max_fpr=0.02).synthesize(benign, attacks, generation=1)


@pytest.mark.parametrize("field", POLICY_FEATURES)
def test_direct_scoring_rejects_schema_bypassed_boolean_policy_features(field):
    """Direct score calls retain the same bool-as-number guardrail as synthesis."""
    benign, attacks = _world()
    attacks[0].__dict__[field] = False

    with pytest.raises(ValueError, match=rf"attack transaction .* has non-numeric {field}"):
        score_policy(_policy(), benign, attacks)

import math

import pytest

from app.policy import DefenceCompiler, score_policy
from app.schemas import Policy, Transaction


POLICY_FEATURES = (
    "merchant_age_hours",
    "first_time_card_ratio",
    "settlement_change_days",
    "temporal_burst_score",
)
NONFINITE_VALUES = (float("nan"), float("inf"), float("-inf"))


def _world() -> tuple[list[Transaction], list[Transaction]]:
    benign = [
        Transaction(
            tx_id="B-NONFINITE-1",
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
            tx_id="A-NONFINITE-1",
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
        policy_id="NONFINITE-GUARDRAIL",
        merchant_age_max=48.0,
        first_time_card_ratio_min=0.50,
        settlement_change_days_max=7.0,
        temporal_burst_score_min=0.50,
        action="STEP_UP",
        estimated_latency_ms=0.35,
    )


@pytest.mark.parametrize("value", NONFINITE_VALUES)
@pytest.mark.parametrize("field", POLICY_FEATURES)
@pytest.mark.parametrize("population", ["benign", "attack"])
def test_compiler_rejects_schema_bypassed_nonfinite_policy_features(field, population, value):
    """Non-finite evidence must never enter compiler threshold comparisons."""
    benign, attacks = _world()
    target = benign[0] if population == "benign" else attacks[0]
    target.__dict__[field] = value

    with pytest.raises(ValueError, match=rf"{population} transaction .* has non-finite {field}"):
        DefenceCompiler(max_fpr=0.02).synthesize(benign, attacks, generation=1)


@pytest.mark.parametrize("value", NONFINITE_VALUES)
@pytest.mark.parametrize("field", POLICY_FEATURES)
def test_direct_scoring_rejects_schema_bypassed_nonfinite_policy_features(field, value):
    """Direct scoring retains the same finite-evidence boundary as synthesis."""
    benign, attacks = _world()
    attacks[0].__dict__[field] = value

    with pytest.raises(ValueError, match=rf"attack transaction .* has non-finite {field}"):
        score_policy(_policy(), benign, attacks)

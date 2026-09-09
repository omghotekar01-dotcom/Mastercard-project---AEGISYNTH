import math

import pytest

from app.contracts import (
    POLICY_MERCHANT_AGE_HOURS_MAX,
    POLICY_MERCHANT_AGE_HOURS_MIN,
    POLICY_TEMPORAL_BURST_SCORE_MAX,
    POLICY_TEMPORAL_BURST_SCORE_MIN,
)
from app.engine import AegisynthEngine
from app.schemas import Transaction


def _attack(**updates) -> Transaction:
    tx = Transaction(
        tx_id="attack-001",
        amount=100.0,
        merchant_age_hours=48.0,
        first_time_card_ratio=0.5,
        settlement_change_days=7.0,
        temporal_burst_score=0.5,
        device_entropy=0.5,
        geo_velocity=0.0,
        label=1,
        attack_family="ghost_merchant_swarm",
    )
    return tx.model_copy(update=updates)


@pytest.mark.parametrize(
    ("feature", "value"),
    [
        ("merchant_age_hours", POLICY_MERCHANT_AGE_HOURS_MIN),
        ("merchant_age_hours", POLICY_MERCHANT_AGE_HOURS_MAX),
        ("temporal_burst_score", POLICY_TEMPORAL_BURST_SCORE_MIN),
        ("temporal_burst_score", POLICY_TEMPORAL_BURST_SCORE_MAX),
    ],
)
def test_baseline_accepts_shared_feature_domain_boundaries(feature, value):
    result = AegisynthEngine._baseline_attack_success([_attack(**{feature: value})])

    assert 0.0 <= result <= 1.0


@pytest.mark.parametrize(
    ("feature", "value"),
    [
        (
            "merchant_age_hours",
            math.nextafter(POLICY_MERCHANT_AGE_HOURS_MIN, -math.inf),
        ),
        (
            "merchant_age_hours",
            math.nextafter(POLICY_MERCHANT_AGE_HOURS_MAX, math.inf),
        ),
        (
            "temporal_burst_score",
            math.nextafter(POLICY_TEMPORAL_BURST_SCORE_MIN, -math.inf),
        ),
        (
            "temporal_burst_score",
            math.nextafter(POLICY_TEMPORAL_BURST_SCORE_MAX, math.inf),
        ),
    ],
)
def test_baseline_rejects_values_immediately_outside_shared_feature_domains(feature, value):
    with pytest.raises(ValueError, match=rf"baseline attack evidence has invalid {feature}"):
        AegisynthEngine._baseline_attack_success([_attack(**{feature: value})])

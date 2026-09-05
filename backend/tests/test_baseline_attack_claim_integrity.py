import math

import pytest

from app.engine import AegisynthEngine
from app.simulator import PaymentWorld


def test_baseline_attack_success_accepts_canonical_synthetic_evidence():
    attacks = PaymentWorld(seed=42).attack(20, hardness=0.05)

    result = AegisynthEngine._baseline_attack_success(attacks)

    assert 0 <= result <= 1


@pytest.mark.parametrize(
    ("update", "message"),
    [
        ({"label": 0}, "only label=1"),
        ({"attack_family": "unimplemented_family"}, "unsupported synthetic attack family"),
        ({"merchant_age_hours": math.nan}, "invalid merchant_age_hours"),
        ({"temporal_burst_score": math.inf}, "invalid temporal_burst_score"),
    ],
)
def test_baseline_attack_success_rejects_malformed_claim_evidence(update, message):
    attack = PaymentWorld(seed=42).attack(1)[0]
    malformed = attack.model_copy(update=update)

    with pytest.raises(ValueError, match=message):
        AegisynthEngine._baseline_attack_success([malformed])


def test_baseline_attack_success_rejects_duplicate_weighting():
    attack = PaymentWorld(seed=42).attack(1)[0]

    with pytest.raises(ValueError, match="duplicate tx_id"):
        AegisynthEngine._baseline_attack_success([attack, attack.model_copy()])

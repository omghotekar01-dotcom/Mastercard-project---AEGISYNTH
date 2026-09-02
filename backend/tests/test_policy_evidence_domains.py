import pytest

from app.policy import DefenceCompiler
from app.simulator import PaymentWorld


@pytest.mark.parametrize(
    "population,feature,value",
    [
        ("benign", "merchant_age_hours", 24 * 365 * 20 + 1),
        ("attack", "merchant_age_hours", 24 * 365 * 20 + 1),
        ("benign", "settlement_change_days", 3650.1),
        ("attack", "settlement_change_days", 3650.1),
    ],
)
def test_compiler_rejects_evidence_outside_formal_verifier_domains(population, feature, value):
    world = PaymentWorld(seed=42)
    benign = world.benign(8)
    attacks = world.attack(8, hardness=0.05)
    rows = benign if population == "benign" else attacks
    rows[0] = rows[0].model_copy(update={feature: value})

    with pytest.raises(ValueError, match=rf"{population} transaction .* has out-of-range {feature}"):
        DefenceCompiler(max_fpr=0.02).synthesize(benign, attacks, generation=1)

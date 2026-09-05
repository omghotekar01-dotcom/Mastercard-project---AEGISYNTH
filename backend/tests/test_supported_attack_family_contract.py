import pytest

from app.engine import AegisynthEngine
from app.simulator import PaymentWorld, SUPPORTED_ATTACK_FAMILIES


def test_only_documented_synthetic_attack_family_is_supported():
    assert SUPPORTED_ATTACK_FAMILIES == frozenset({"ghost_merchant_swarm"})

    world = PaymentWorld(seed=42)
    rows = world.attack(3, family="ghost_merchant_swarm", hardness=0.2)

    assert len(rows) == 3
    assert {row.attack_family for row in rows} == {"ghost_merchant_swarm"}


def test_unsupported_family_fails_before_rng_state_advances():
    rejected_world = PaymentWorld(seed=123)
    clean_world = PaymentWorld(seed=123)

    with pytest.raises(ValueError, match="unsupported synthetic attack family"):
        rejected_world.attack(4, family="unimplemented_family", hardness=0.3)

    assert rejected_world.attack(4, hardness=0.3) == clean_world.attack(4, hardness=0.3)


def test_engine_refuses_to_relabel_one_generator_as_an_unimplemented_family():
    with pytest.raises(ValueError, match="unsupported synthetic attack family"):
        AegisynthEngine(seed=42).run(
            generations=1,
            attack_family="unimplemented_family",
        )

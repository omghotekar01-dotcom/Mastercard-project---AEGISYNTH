import pytest

from app.simulator import PaymentWorld


@pytest.mark.parametrize("hardness", [-0.0001, -1, 1.0001, 2])
def test_attack_rejects_out_of_domain_hardness(hardness):
    world = PaymentWorld(seed=17)

    with pytest.raises(ValueError, match=r"hardness must be a finite number within \[0, 1\]"):
        world.attack(n=1, hardness=hardness)


def test_rejected_attack_hardness_does_not_advance_rng_state():
    rejected_world = PaymentWorld(seed=17)
    clean_world = PaymentWorld(seed=17)

    with pytest.raises(ValueError):
        rejected_world.attack(n=4, hardness=1.5)

    assert rejected_world.attack(n=4, hardness=0.5) == clean_world.attack(n=4, hardness=0.5)


def test_calibration_rejects_out_of_domain_hardness_before_generating_benign_rows():
    rejected_world = PaymentWorld(seed=23)
    clean_world = PaymentWorld(seed=23)

    with pytest.raises(ValueError, match=r"hardness must be a finite number within \[0, 1\]"):
        rejected_world.calibration_set(benign_n=4, attack_n=4, hardness=-0.25)

    assert rejected_world.benign(4) == clean_world.benign(4)


@pytest.mark.parametrize("hardness", [0, 0.0, 0.5, 1, 1.0])
def test_supported_hardness_domain_remains_deterministic(hardness):
    left = PaymentWorld(seed=29).attack(n=5, hardness=hardness)
    right = PaymentWorld(seed=29).attack(n=5, hardness=hardness)

    assert left == right

import pytest

from app.simulator import PaymentWorld


@pytest.mark.parametrize("seed", [True, False, 42.0, "42", None])
def test_payment_world_rejects_non_integer_seeds(seed):
    with pytest.raises(ValueError, match="seed must be an integer"):
        PaymentWorld(seed=seed)


def test_payment_world_same_integer_seed_is_reproducible():
    first = PaymentWorld(seed=42).calibration_set(benign_n=3, attack_n=3, hardness=0.2)
    second = PaymentWorld(seed=42).calibration_set(benign_n=3, attack_n=3, hardness=0.2)

    assert first == second

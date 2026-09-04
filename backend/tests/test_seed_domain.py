import pytest

from app.engine import AegisynthEngine
from app.simulator import PaymentWorld


@pytest.mark.parametrize("seed", [-1, -42, True, False, 1.5, "42", None])
def test_payment_world_rejects_invalid_seed_before_rng_initialization(seed):
    with pytest.raises(ValueError, match="seed must be a non-negative integer"):
        PaymentWorld(seed)


def test_engine_negative_seed_fails_before_simulation_runs():
    engine = AegisynthEngine(seed=-1)

    with pytest.raises(ValueError, match="seed must be a non-negative integer"):
        engine.run(generations=1)


def test_zero_seed_remains_valid_and_deterministic():
    first = PaymentWorld(0).benign(3)
    second = PaymentWorld(0).benign(3)

    assert first == second

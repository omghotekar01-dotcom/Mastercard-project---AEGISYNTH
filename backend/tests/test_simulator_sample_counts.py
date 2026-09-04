import pytest

from app.simulator import PaymentWorld


@pytest.mark.parametrize("bad_count", [0, -1, True, False, 1.5, "10"])
def test_benign_rejects_invalid_sample_counts(bad_count):
    world = PaymentWorld(seed=42)

    with pytest.raises(ValueError, match=r"benign sample count must be a positive integer"):
        world.benign(bad_count)


@pytest.mark.parametrize("bad_count", [0, -5, True, False, 2.0, "5"])
def test_attack_rejects_invalid_sample_counts(bad_count):
    world = PaymentWorld(seed=42)

    with pytest.raises(ValueError, match=r"attack sample count must be a positive integer"):
        world.attack(bad_count)


def test_calibration_rejects_all_counts_before_rng_state_advances():
    world = PaymentWorld(seed=42)
    fresh = PaymentWorld(seed=42)

    with pytest.raises(ValueError, match=r"attack sample count must be a positive integer"):
        world.calibration_set(benign_n=3, attack_n=0)

    assert [tx.model_dump() for tx in world.benign(2)] == [tx.model_dump() for tx in fresh.benign(2)]


def test_positive_sample_counts_preserve_exact_requested_sizes():
    world = PaymentWorld(seed=42)

    benign, attacks = world.calibration_set(benign_n=3, attack_n=2)

    assert len(benign) == 3
    assert len(attacks) == 2
    assert [tx.tx_id for tx in benign] == ["B-000000", "B-000001", "B-000002"]
    assert [tx.tx_id for tx in attacks] == ["A-000000", "A-000001"]

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


@pytest.mark.parametrize("bad_hardness", [True, False, float("nan"), float("inf"), float("-inf"), "0.5", None])
def test_attack_rejects_non_finite_or_non_numeric_hardness(bad_hardness):
    world = PaymentWorld(seed=42)

    with pytest.raises(ValueError, match=r"hardness must be a finite number"):
        world.attack(2, hardness=bad_hardness)


@pytest.mark.parametrize("bad_family", ["", None, 123, "A" * 65])
def test_attack_rejects_malformed_family_before_rng_state_advances(bad_family):
    world = PaymentWorld(seed=42)
    fresh = PaymentWorld(seed=42)

    with pytest.raises(ValueError, match=r"attack family must be a non-empty string of at most 64 characters"):
        world.attack(2, family=bad_family)

    assert [tx.model_dump() for tx in world.attack(2)] == [tx.model_dump() for tx in fresh.attack(2)]


@pytest.mark.parametrize("bad_family", [" ghost_merchant_swarm", "ghost merchant swarm", "ghost\tmerchant", "ghost\nmerchant"])
def test_attack_rejects_whitespace_family_before_rng_state_advances(bad_family):
    world = PaymentWorld(seed=42)
    fresh = PaymentWorld(seed=42)

    with pytest.raises(ValueError, match=r"attack family must not contain whitespace"):
        world.attack(2, family=bad_family)

    assert [tx.model_dump() for tx in world.attack(2)] == [tx.model_dump() for tx in fresh.attack(2)]


def test_attack_rejects_reserved_benign_family_before_rng_state_advances():
    world = PaymentWorld(seed=42)
    fresh = PaymentWorld(seed=42)

    with pytest.raises(ValueError, match=r"attack family must not use the reserved benign provenance label"):
        world.attack(2, family="benign")

    assert [tx.model_dump() for tx in world.attack(2)] == [tx.model_dump() for tx in fresh.attack(2)]


def test_valid_custom_attack_family_is_preserved():
    rows = PaymentWorld(seed=42).attack(2, family="synthetic_variant_1")

    assert [tx.attack_family for tx in rows] == ["synthetic_variant_1", "synthetic_variant_1"]


def test_calibration_rejects_all_counts_before_rng_state_advances():
    world = PaymentWorld(seed=42)
    fresh = PaymentWorld(seed=42)

    with pytest.raises(ValueError, match=r"attack sample count must be a positive integer"):
        world.calibration_set(benign_n=3, attack_n=0)

    assert [tx.model_dump() for tx in world.benign(2)] == [tx.model_dump() for tx in fresh.benign(2)]


def test_calibration_rejects_bad_hardness_before_rng_state_advances():
    world = PaymentWorld(seed=42)
    fresh = PaymentWorld(seed=42)

    with pytest.raises(ValueError, match=r"hardness must be a finite number"):
        world.calibration_set(benign_n=3, attack_n=2, hardness=float("nan"))

    assert [tx.model_dump() for tx in world.benign(2)] == [tx.model_dump() for tx in fresh.benign(2)]


def test_positive_sample_counts_preserve_exact_requested_sizes():
    world = PaymentWorld(seed=42)

    benign, attacks = world.calibration_set(benign_n=3, attack_n=2)

    assert len(benign) == 3
    assert len(attacks) == 2
    assert [tx.tx_id for tx in benign] == ["B-000000", "B-000001", "B-000002"]
    assert [tx.tx_id for tx in attacks] == ["A-000000", "A-000001"]

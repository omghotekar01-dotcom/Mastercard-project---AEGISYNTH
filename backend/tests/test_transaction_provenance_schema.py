import pytest
from pydantic import ValidationError

from app.schemas import Transaction


def _tx(**overrides):
    values = {
        "tx_id": "B-000001",
        "amount": 125.0,
        "merchant_age_hours": 720.0,
        "first_time_card_ratio": 0.2,
        "settlement_change_days": 90.0,
        "temporal_burst_score": 0.15,
        "device_entropy": 0.3,
        "geo_velocity": 5.0,
        "label": 0,
        "attack_family": "benign",
    }
    values.update(overrides)
    return Transaction(**values)


@pytest.mark.parametrize(
    "tx_id",
    [" B-000001", "B-000001 ", "B 000001", "B-000001\t", "B-000001\n"],
)
def test_transaction_rejects_whitespace_identity(tx_id):
    with pytest.raises(ValidationError, match="tx_id must not contain whitespace"):
        _tx(tx_id=tx_id)


@pytest.mark.parametrize(
    "attack_family",
    ["ghost merchant", " ghost_merchant", "ghost_merchant ", "ghost\tmerchant", "ghost\nmerchant"],
)
def test_transaction_rejects_whitespace_attack_family(attack_family):
    with pytest.raises(ValidationError, match="attack_family must not contain whitespace"):
        _tx(tx_id="A-000001", label=1, attack_family=attack_family)


def test_benign_transaction_rejects_attack_provenance():
    with pytest.raises(ValidationError, match="benign transactions must use the benign"):
        _tx(attack_family="ghost_merchant_swarm")


def test_attack_transaction_rejects_reserved_benign_provenance():
    with pytest.raises(ValidationError, match="attack transactions must identify a non-benign"):
        _tx(tx_id="A-000001", label=1, attack_family="benign")


def test_canonical_benign_and_attack_transactions_remain_valid():
    benign = _tx()
    attack = _tx(tx_id="A-000001", label=1, attack_family="ghost_merchant_swarm")

    assert benign.attack_family == "benign"
    assert benign.label == 0
    assert attack.attack_family == "ghost_merchant_swarm"
    assert attack.label == 1

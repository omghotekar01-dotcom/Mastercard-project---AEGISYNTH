from app.policy import DefenceCompiler
from app.schemas import Transaction


def _tx(
    tx_id: str,
    *,
    age: float,
    card: float,
    settle: float,
    burst: float,
    fraud: bool,
) -> Transaction:
    return Transaction(
        tx_id=tx_id,
        amount=100.0,
        merchant_age_hours=age,
        first_time_card_ratio=card,
        settlement_change_days=settle,
        temporal_burst_score=burst,
        device_entropy=0.5,
        geo_velocity=0.0,
        label=int(fraud),
        attack_family="ghost_merchant_swarm" if fraud else "benign",
    )


def _evidence() -> tuple[list[Transaction], list[Transaction]]:
    benign = [
        _tx("B-1", age=400, card=0.10, settle=100, burst=0.10, fraud=False),
        _tx("B-2", age=300, card=0.20, settle=90, burst=0.20, fraud=False),
        _tx("B-3", age=220, card=0.30, settle=80, burst=0.30, fraud=False),
    ]
    attacks = [
        _tx("A-1", age=20, card=0.90, settle=2, burst=0.90, fraud=True),
        _tx("A-2", age=30, card=0.85, settle=3, burst=0.85, fraud=True),
        _tx("A-3", age=40, card=0.80, settle=4, burst=0.80, fraud=True),
    ]
    return benign, attacks


def test_compiler_policy_identity_is_reproducible_and_semantic():
    """Identical evidence must yield the same ID, and the ID must encode the chosen thresholds."""
    benign, attacks = _evidence()
    compiler = DefenceCompiler(max_fpr=0.02)

    first = compiler.synthesize(benign, attacks, generation=3)
    second = compiler.synthesize(benign, attacks, generation=3)

    assert first.policy_id == second.policy_id
    assert first.model_dump() == second.model_dump()

    prefix, generation, age, card, settle, burst = first.policy_id.split("-")
    assert prefix == "ZD"
    assert int(generation) == 3
    assert int(age) == int(first.merchant_age_max)
    assert int(card) == round(first.first_time_card_ratio_min * 100)
    assert int(settle) == int(first.settlement_change_days_max)
    assert int(burst) == round(first.temporal_burst_score_min * 100)

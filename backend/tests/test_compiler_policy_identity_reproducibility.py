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


def test_compiler_output_is_invariant_to_evidence_row_order():
    """Dataset row ordering must not change the policy or judge-facing metrics."""
    benign, attacks = _evidence()
    compiler = DefenceCompiler(max_fpr=0.02)

    canonical = compiler.synthesize(benign, attacks, generation=3)
    reordered = compiler.synthesize(
        [benign[2], benign[0], benign[1]],
        [attacks[1], attacks[2], attacks[0]],
        generation=3,
    )

    assert reordered.model_dump() == canonical.model_dump()


def test_generation_metadata_does_not_change_policy_semantics_or_metrics():
    """Generation bookkeeping may change lineage identity, never synthesis results."""
    benign, attacks = _evidence()
    compiler = DefenceCompiler(max_fpr=0.02)

    generation_one = compiler.synthesize(benign, attacks, generation=1)
    generation_eight = compiler.synthesize(benign, attacks, generation=8)

    first_payload = generation_one.model_dump()
    eighth_payload = generation_eight.model_dump()
    first_id = first_payload.pop("policy_id")
    eighth_id = eighth_payload.pop("policy_id")

    assert first_payload == eighth_payload
    assert first_id.startswith("ZD-01-")
    assert eighth_id.startswith("ZD-08-")
    assert first_id.removeprefix("ZD-01-") == eighth_id.removeprefix("ZD-08-")


def test_compiler_does_not_mutate_benchmark_evidence():
    """Synthesis must be read-only over benchmark evidence used for reproducible claims."""
    benign, attacks = _evidence()
    benign_before = [tx.model_dump(mode="json") for tx in benign]
    attacks_before = [tx.model_dump(mode="json") for tx in attacks]

    DefenceCompiler(max_fpr=0.02).synthesize(benign, attacks, generation=3)

    assert [tx.model_dump(mode="json") for tx in benign] == benign_before
    assert [tx.model_dump(mode="json") for tx in attacks] == attacks_before

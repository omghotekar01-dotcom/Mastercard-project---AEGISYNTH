from app.policy import DefenceCompiler, score_policy
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
        _tx("B-4", age=180, card=0.45, settle=60, burst=0.42, fraud=False),
    ]
    attacks = [
        _tx("A-1", age=20, card=0.90, settle=2, burst=0.90, fraud=True),
        _tx("A-2", age=30, card=0.85, settle=3, burst=0.85, fraud=True),
        _tx("A-3", age=40, card=0.80, settle=4, burst=0.80, fraud=True),
        _tx("A-4", age=100, card=0.72, settle=18, burst=0.68, fraud=True),
    ]
    return benign, attacks


def test_compiler_reported_metrics_equal_independent_rescore():
    """Judge-visible compiler metrics must be derivable from the returned policy and evidence."""
    benign, attacks = _evidence()
    compiler = DefenceCompiler(max_fpr=0.25)

    for generation in (1, 4, 8):
        policy = compiler.synthesize(benign, attacks, generation=generation)
        rescored = score_policy(policy, benign, attacks)

        assert policy.fraud_coverage == round(rescored.coverage, 4)
        assert policy.false_positive_rate == round(rescored.fpr, 4)
        assert rescored.blocked_attacks == round(rescored.coverage * len(attacks))
        assert rescored.benign_hits == round(rescored.fpr * len(benign))
        assert policy.false_positive_rate <= compiler.max_fpr

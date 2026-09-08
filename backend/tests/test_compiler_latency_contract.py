from app import policy as policy_module
from app.schemas import Transaction


def _tx(*, tx_id: str, label: int, attack_family: str, age: float, card: float, settle: float, burst: float) -> Transaction:
    return Transaction(
        tx_id=tx_id,
        amount=100.0,
        merchant_age_hours=age,
        first_time_card_ratio=card,
        settlement_change_days=settle,
        temporal_burst_score=burst,
        device_entropy=0.5,
        geo_velocity=0.0,
        label=label,
        attack_family=attack_family,
    )


def test_synthesis_emits_the_shared_compiler_latency_contract(monkeypatch):
    """Synthesis must consume the same latency constant enforced by provenance validation."""
    expected_latency = 0.41
    monkeypatch.setattr(policy_module, "_COMPILER_ESTIMATED_LATENCY_MS", expected_latency)

    benign = [
        _tx(
            tx_id="benign-1",
            label=0,
            attack_family="benign",
            age=1000.0,
            card=0.10,
            settle=100.0,
            burst=0.10,
        )
    ]
    attacks = [
        _tx(
            tx_id="attack-1",
            label=1,
            attack_family="ghost_merchant_swarm",
            age=24.0,
            card=0.90,
            settle=1.0,
            burst=0.90,
        )
    ]

    policy = policy_module.DefenceCompiler(max_fpr=0.02).synthesize(benign, attacks, generation=1)

    assert policy.estimated_latency_ms == expected_latency

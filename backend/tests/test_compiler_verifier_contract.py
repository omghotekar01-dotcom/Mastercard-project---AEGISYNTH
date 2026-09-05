import re

import pytest

from app.policy import DefenceCompiler
from app.schemas import Transaction
from app.verification import verify_policy


_CANONICAL_POLICY_ID = re.compile(r"^[A-Za-z0-9._-]+$")


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


@pytest.mark.parametrize("generation", [1, 8])
def test_compiler_output_satisfies_verifier_boundary(generation: int):
    """Compiler output must be directly admissible to the formal/business verifier.

    This contract prevents the compiler and verifier from silently drifting on identity,
    action, numeric-domain, false-positive, or latency guardrails.
    """
    benign, attacks = _evidence()
    compiler = DefenceCompiler(max_fpr=0.02)

    policy = compiler.synthesize(benign, attacks, generation=generation)
    verified, notes = verify_policy(policy, max_fpr=compiler.max_fpr)

    assert _CANONICAL_POLICY_ID.fullmatch(policy.policy_id)
    assert policy.action in {"STEP_UP", "REVIEW"}
    assert policy.false_positive_rate <= compiler.max_fpr
    assert verified, notes
    assert any(note.startswith("Z3:") for note in notes)

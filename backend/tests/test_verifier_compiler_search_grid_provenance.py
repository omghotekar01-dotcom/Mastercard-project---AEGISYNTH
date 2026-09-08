from __future__ import annotations

import pytest

from app.schemas import Policy
from app.verification import verify_policy


def _policy(policy_id: str, *, age: float, card: float, settle: float, burst: float) -> Policy:
    return Policy(
        policy_id=policy_id,
        merchant_age_max=age,
        first_time_card_ratio_min=card,
        settlement_change_days_max=settle,
        temporal_burst_score_min=burst,
        action="STEP_UP",
        fraud_coverage=0.90,
        false_positive_rate=0.01,
        estimated_latency_ms=0.35,
    )


@pytest.mark.parametrize(
    ("policy_id", "age", "card", "settle", "burst"),
    [
        ("ZD-04-097-64-21-64", 97, 0.64, 21, 0.64),
        ("ZD-04-096-63-21-64", 96, 0.63, 21, 0.64),
        ("ZD-04-096-64-22-64", 96, 0.64, 22, 0.64),
        ("ZD-04-096-64-21-63", 96, 0.64, 21, 0.63),
    ],
)
def test_verifier_rejects_compiler_ids_with_thresholds_outside_native_search_grid(
    policy_id: str,
    age: float,
    card: float,
    settle: float,
    burst: float,
) -> None:
    verified, notes = verify_policy(
        _policy(policy_id, age=age, card=card, settle=settle, burst=burst)
    )

    assert verified is False
    assert notes == [
        "Compiler policy identity invalid: thresholds are outside the native compiler search grid"
    ]


def test_verifier_accepts_native_compiler_search_grid_identity() -> None:
    verified, notes = verify_policy(
        _policy("ZD-04-096-64-21-64", age=96, card=0.64, settle=21, burst=0.64)
    )

    assert verified is True
    assert any(note.startswith("Z3:") for note in notes)

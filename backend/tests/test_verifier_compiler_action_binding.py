from __future__ import annotations

from app.schemas import Policy
from app.verification import verify_policy


def _compiler_policy(action: str = "STEP_UP") -> Policy:
    return Policy(
        policy_id="ZD-04-096-64-21-64",
        merchant_age_max=96,
        first_time_card_ratio_min=0.64,
        settlement_change_days_max=21,
        temporal_burst_score_min=0.64,
        action=action,
        fraud_coverage=0.90,
        false_positive_rate=0.01,
        estimated_latency_ms=0.35,
    )


def test_compiler_lineage_rejects_mutated_review_action() -> None:
    policy = _compiler_policy(action="REVIEW")

    verified, notes = verify_policy(policy)

    assert verified is False
    assert notes == [
        "Compiler policy identity mismatch: ZD policies must retain the compiler STEP_UP action"
    ]


def test_compiler_lineage_still_accepts_native_step_up_action() -> None:
    policy = _compiler_policy()

    verified, notes = verify_policy(policy)

    assert verified is True
    assert any(note.startswith("Z3:") for note in notes)


def test_generic_external_review_policy_remains_supported() -> None:
    policy = _compiler_policy(action="REVIEW").model_copy(update={"policy_id": "external-review-v1"})

    verified, notes = verify_policy(policy)

    assert verified is True
    assert any("step-up/review only" in note for note in notes)

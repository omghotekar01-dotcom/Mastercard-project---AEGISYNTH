from app.contracts import (
    DEFAULT_MAX_FALSE_POSITIVE_RATE,
    DEFAULT_MAX_POLICY_LATENCY_MS,
)
from app.schemas import Policy
from app.verification import _validate_budgets, verify_policy


def _policy() -> Policy:
    return Policy(
        policy_id="external-review-policy",
        merchant_age_max=72,
        first_time_card_ratio_min=0.64,
        settlement_change_days_max=14,
        temporal_burst_score_min=0.64,
        action="STEP_UP",
        fraud_coverage=0.9,
        false_positive_rate=0.01,
        estimated_latency_ms=0.5,
    )


def test_verifier_rejects_relaxed_fpr_budget_before_policy_evaluation() -> None:
    ok, notes = verify_policy(
        _policy(),
        max_fpr=DEFAULT_MAX_FALSE_POSITIVE_RATE + 0.0001,
    )

    assert ok is False
    assert notes == [
        "Verifier configuration invalid: max_fpr must be finite and within "
        f"[0, {DEFAULT_MAX_FALSE_POSITIVE_RATE:g}]"
    ]


def test_verifier_rejects_relaxed_latency_budget_before_policy_evaluation() -> None:
    ok, notes = verify_policy(
        _policy(),
        max_latency_ms=DEFAULT_MAX_POLICY_LATENCY_MS + 0.01,
    )

    assert ok is False
    assert notes == [
        "Verifier configuration invalid: max_latency_ms must be finite and within "
        f"(0, {DEFAULT_MAX_POLICY_LATENCY_MS:g}]"
    ]


def test_verifier_budget_validator_allows_stricter_business_limits() -> None:
    ok, notes = _validate_budgets(
        DEFAULT_MAX_FALSE_POSITIVE_RATE / 2,
        DEFAULT_MAX_POLICY_LATENCY_MS / 2,
    )

    assert ok is True
    assert notes == []

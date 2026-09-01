from __future__ import annotations

import math

try:
    from z3 import And, Real, Solver, sat
    HAS_Z3 = True
except ImportError:  # local/offline fallback; production requirements install z3-solver
    HAS_Z3 = False

from .schemas import Policy

ALLOWED_ACTIONS = {"PASS", "STEP_UP", "REVIEW"}
DEFAULT_MAX_POLICY_LATENCY_MS = 5.0


def _validate_budgets(max_fpr: float, max_latency_ms: float) -> tuple[bool, list[str]]:
    """Reject malformed verifier configuration before evaluating a policy.

    Business guardrails are safety boundaries. Invalid budgets must fail closed rather than
    accidentally weakening verification through negative, non-finite, or out-of-range values.
    """
    if not math.isfinite(max_fpr) or not 0 <= max_fpr <= 1:
        return False, ["Verifier configuration invalid: max_fpr must be finite and within [0, 1]"]
    if not math.isfinite(max_latency_ms) or max_latency_ms <= 0:
        return False, ["Verifier configuration invalid: max_latency_ms must be finite and > 0"]
    return True, []


def verify_policy(
    policy: Policy,
    max_fpr: float = 0.02,
    max_latency_ms: float = DEFAULT_MAX_POLICY_LATENCY_MS,
) -> tuple[bool, list[str]]:
    """Verify policy governance, business budgets, and formal feature-domain consistency.

    The verifier intentionally checks only properties represented by the compact policy artifact.
    It does not claim end-to-end payment-network performance or production certification.
    """

    budgets_ok, budget_notes = _validate_budgets(max_fpr, max_latency_ms)
    if not budgets_ok:
        return False, budget_notes

    notes: list[str] = []
    if policy.action not in ALLOWED_ACTIONS:
        return False, ["Action is not allowed"]
    if policy.action == "PASS":
        return False, ["Compiled fraud defences may not use PASS as the triggered action"]
    if policy.false_positive_rate > max_fpr:
        return False, ["False-positive budget exceeded"]
    if policy.estimated_latency_ms > max_latency_ms:
        return False, [
            f"Estimated policy latency {policy.estimated_latency_ms:.2f} ms exceeds "
            f"the configured {max_latency_ms:.2f} ms budget"
        ]

    if HAS_Z3:
        age = Real("age")
        card = Real("card")
        settle = Real("settle")
        burst = Real("burst")
        solver = Solver()
        solver.add(And(age >= 0, age <= 24 * 365 * 20))
        solver.add(And(card >= 0, card <= 1))
        solver.add(And(settle >= 0, settle <= 3650))
        solver.add(And(burst >= 0, burst <= 1))
        solver.add(age <= policy.merchant_age_max)
        solver.add(card >= policy.first_time_card_ratio_min)
        solver.add(settle <= policy.settlement_change_days_max)
        solver.add(burst >= policy.temporal_burst_score_min)
        if solver.check() != sat:
            return False, ["Policy conditions are unsatisfiable"]
        formal_note = "Z3: policy is satisfiable over valid payment-feature domains."
    else:
        satisfiable = (
            policy.merchant_age_max >= 0
            and 0 <= policy.first_time_card_ratio_min <= 1
            and policy.settlement_change_days_max >= 0
            and 0 <= policy.temporal_burst_score_min <= 1
        )
        if not satisfiable:
            return False, ["Policy conditions are outside valid domains"]
        formal_note = "Offline verifier: domain constraints satisfied (Z3 used when installed)."

    notes.extend(
        [
            formal_note,
            f"False-positive rate {policy.false_positive_rate:.2%} is within {max_fpr:.2%} budget.",
            f"Estimated policy latency {policy.estimated_latency_ms:.2f} ms is within {max_latency_ms:.2f} ms budget.",
            "Triggered action is step-up/review only; no autonomous hard decline is emitted.",
            "Policy uses operational payment features only; no protected demographic attributes are present.",
        ]
    )
    return True, notes

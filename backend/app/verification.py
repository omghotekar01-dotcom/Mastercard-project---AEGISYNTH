from __future__ import annotations

import math

try:
    from z3 import And, Real, Solver, sat
    HAS_Z3 = True
except ImportError:  # production requirements install z3-solver; verification fails closed without it
    HAS_Z3 = False

from .schemas import Policy

ALLOWED_ACTIONS = {"PASS", "STEP_UP", "REVIEW"}
DEFAULT_MAX_POLICY_LATENCY_MS = 5.0


def _is_real_number(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float))


def _validate_budgets(max_fpr: float, max_latency_ms: float) -> tuple[bool, list[str]]:
    """Reject malformed verifier configuration before evaluating a policy."""
    if not _is_real_number(max_fpr):
        return False, ["Verifier configuration invalid: max_fpr must be a real numeric value"]
    if not math.isfinite(max_fpr) or not 0 <= max_fpr <= 1:
        return False, ["Verifier configuration invalid: max_fpr must be finite and within [0, 1]"]
    if not _is_real_number(max_latency_ms):
        return False, ["Verifier configuration invalid: max_latency_ms must be a real numeric value"]
    if not math.isfinite(max_latency_ms) or max_latency_ms <= 0:
        return False, ["Verifier configuration invalid: max_latency_ms must be finite and > 0"]
    return True, []


def _validate_policy_identity(policy: Policy) -> tuple[bool, list[str]]:
    """Require a durable policy identity at the verification trust boundary."""
    if not isinstance(policy.policy_id, str) or not policy.policy_id.strip():
        return False, ["Policy identity invalid: policy_id must be a non-empty string"]
    return True, []


def _validate_policy_action(policy: Policy) -> tuple[bool, list[str]]:
    """Reject schema-bypassed action values before allow-list membership checks."""
    if not isinstance(policy.action, str):
        return False, ["Policy action invalid: action must be a string"]
    if policy.action not in ALLOWED_ACTIONS:
        return False, ["Action is not allowed"]
    if policy.action == "PASS":
        return False, ["Compiled fraud defences may not use PASS as the triggered action"]
    return True, []


def _validate_policy_numeric_fields(policy: Policy) -> tuple[bool, list[str]]:
    """Fail closed if schema-bypassed policy numerics are malformed."""
    bounded_fields = {
        "merchant_age_max": (policy.merchant_age_max, 0.0, float(24 * 365 * 20)),
        "first_time_card_ratio_min": (policy.first_time_card_ratio_min, 0.0, 1.0),
        "settlement_change_days_max": (policy.settlement_change_days_max, 0.0, 3650.0),
        "temporal_burst_score_min": (policy.temporal_burst_score_min, 0.0, 1.0),
        "fraud_coverage": (policy.fraud_coverage, 0.0, 1.0),
        "false_positive_rate": (policy.false_positive_rate, 0.0, 1.0),
    }
    for name, (value, lower, upper) in bounded_fields.items():
        if not _is_real_number(value):
            return False, [f"Policy numeric field invalid: {name} must be a real numeric value"]
        if not math.isfinite(value) or not lower <= value <= upper:
            return False, [f"Policy numeric field invalid: {name} must be finite and within [{lower:g}, {upper:g}]"]

    if not _is_real_number(policy.estimated_latency_ms):
        return False, ["Policy numeric field invalid: estimated_latency_ms must be a real numeric value"]
    if not math.isfinite(policy.estimated_latency_ms) or policy.estimated_latency_ms < 0:
        return False, ["Policy numeric field invalid: estimated_latency_ms must be finite and >= 0"]
    if type(policy.counterexamples_remaining) is not int or policy.counterexamples_remaining < 0:
        return False, ["Policy numeric field invalid: counterexamples_remaining must be a non-negative integer"]
    return True, []


def verify_policy(
    policy: Policy,
    max_fpr: float = 0.02,
    max_latency_ms: float = DEFAULT_MAX_POLICY_LATENCY_MS,
) -> tuple[bool, list[str]]:
    """Verify policy governance, business budgets, and formal feature-domain consistency.

    The empirical counterexample count is reported as robustness evidence, not promoted to
    a formal proof obligation. A nonzero count therefore does not invalidate Z3/domain or
    business-budget verification; callers must preserve the count alongside benchmark ASR.
    """
    budgets_ok, budget_notes = _validate_budgets(max_fpr, max_latency_ms)
    if not budgets_ok:
        return False, budget_notes

    identity_ok, identity_notes = _validate_policy_identity(policy)
    if not identity_ok:
        return False, identity_notes

    action_ok, action_notes = _validate_policy_action(policy)
    if not action_ok:
        return False, action_notes

    policy_numbers_ok, policy_number_notes = _validate_policy_numeric_fields(policy)
    if not policy_numbers_ok:
        return False, policy_number_notes

    notes: list[str] = []
    if policy.false_positive_rate > max_fpr:
        return False, ["False-positive budget exceeded"]
    if policy.estimated_latency_ms > max_latency_ms:
        return False, [
            f"Estimated policy latency {policy.estimated_latency_ms:.2f} ms exceeds "
            f"the configured {max_latency_ms:.2f} ms budget"
        ]

    if not HAS_Z3:
        return False, ["Formal verification unavailable: z3-solver is required"]

    try:
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
        solver_result = solver.check()
    except Exception:
        return False, ["Formal verification failed closed: Z3 runtime error"]

    if solver_result != sat:
        return False, ["Policy conditions are unsatisfiable"]
    formal_note = "Z3: policy is satisfiable over valid payment-feature domains."

    notes.extend(
        [
            formal_note,
            f"False-positive rate {policy.false_positive_rate:.2%} is within {max_fpr:.2%} budget.",
            f"Estimated policy latency {policy.estimated_latency_ms:.2f} ms is within {max_latency_ms:.2f} ms budget.",
            (
                f"Empirical counterexamples reported: {policy.counterexamples_remaining}; "
                "this is robustness evidence, not a formal zero-counterexample proof."
            ),
            "Triggered action is step-up/review only; no autonomous hard decline is emitted.",
            "Policy uses operational payment features only; no protected demographic attributes are present.",
        ]
    )
    return True, notes

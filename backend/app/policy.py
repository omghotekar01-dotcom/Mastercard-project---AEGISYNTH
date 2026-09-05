from __future__ import annotations
import math
import re
from dataclasses import dataclass
from decimal import Decimal
from itertools import product
from .schemas import Policy, Transaction
from .simulator import SUPPORTED_ATTACK_FAMILIES

FEATURES = (
    "merchant_age_hours",
    "first_time_card_ratio",
    "settlement_change_days",
    "temporal_burst_score",
)
_CANONICAL_POLICY_ID = re.compile(r"^[A-Za-z0-9._-]+$")
_CANONICAL_TX_ID = re.compile(r"^[A-Za-z0-9._-]+$")

@dataclass
class Score:
    coverage: float
    fpr: float
    blocked_attacks: int
    benign_hits: int


def matches(policy: Policy, tx: Transaction) -> bool:
    return (
        tx.merchant_age_hours <= policy.merchant_age_max
        and tx.first_time_card_ratio >= policy.first_time_card_ratio_min
        and tx.settlement_change_days <= policy.settlement_change_days_max
        and tx.temporal_burst_score >= policy.temporal_burst_score_min
    )


def score_policy(policy: Policy, benign: list[Transaction], attacks: list[Transaction]) -> Score:
    """Score a policy only against valid, independent evidence populations.

    A missing denominator, contaminated evidence, or malformed policy is invalid evaluation
    evidence, not a meaningful rate. Keep direct scoring calls behind the same validation
    boundary used by compiler synthesis so benchmark metrics cannot bypass policy, label,
    identity, or feature-domain checks.
    """
    if not benign:
        raise ValueError("benign scoring population must not be empty")
    if not attacks:
        raise ValueError("attack scoring population must not be empty")
    _validate_policy_definition(policy)
    _validate_evaluation_populations(benign, attacks)

    blocked = sum(matches(policy, tx) for tx in attacks)
    benign_hits = sum(matches(policy, tx) for tx in benign)
    return Score(
        coverage=blocked / len(attacks),
        fpr=benign_hits / len(benign),
        blocked_attacks=blocked,
        benign_hits=benign_hits,
    )


def _is_real_number(value: object) -> bool:
    """Accept real scalar evidence, but never Python booleans masquerading as 0/1."""
    return not isinstance(value, bool) and isinstance(value, (int, float))


def _validate_max_fpr(value: object) -> None:
    """Keep the live compiler budget inside the same safe domain enforced at construction."""
    if not _is_real_number(value):
        raise ValueError("max_fpr must be a real numeric value")
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("max_fpr must be finite and within [0, 1]")


def _validate_policy_definition(policy: Policy) -> None:
    """Fail closed if a schema-bypassed policy could distort scoring or exceed safe actions."""
    if not isinstance(policy.policy_id, str) or not policy.policy_id.strip():
        raise ValueError("scored policy must have a non-empty string policy_id")
    if len(policy.policy_id) > 80:
        raise ValueError("scored policy policy_id must be at most 80 characters")
    if _CANONICAL_POLICY_ID.fullmatch(policy.policy_id) is None:
        raise ValueError(
            "scored policy policy_id may contain only ASCII letters, digits, '.', '_', and '-'"
        )
    if not isinstance(policy.action, str):
        raise ValueError("scored policy action must be a string")
    if policy.action not in {"PASS", "STEP_UP", "REVIEW"}:
        raise ValueError("scored policy action must be one of PASS, STEP_UP, or REVIEW")
    if policy.action == "PASS":
        raise ValueError("scored fraud defence may not use PASS as the triggered action")

    bounds = {
        "merchant_age_max": (0.0, float(24 * 365 * 20)),
        "first_time_card_ratio_min": (0.0, 1.0),
        "settlement_change_days_max": (0.0, 3650.0),
        "temporal_burst_score_min": (0.0, 1.0),
    }
    for field, (minimum, maximum) in bounds.items():
        value = getattr(policy, field)
        if not _is_real_number(value):
            raise ValueError(f"scored policy has non-numeric {field}")
        if not math.isfinite(value):
            raise ValueError(f"scored policy has non-finite {field}")
        if value < minimum or value > maximum:
            raise ValueError(
                f"scored policy has out-of-range {field}; expected [{minimum:g}, {maximum:g}]"
            )


def _validate_policy_features(tx: Transaction, population: str) -> None:
    """Validate policy-driving evidence against the same domains used by formal verification."""
    bounds = {
        "merchant_age_hours": (0.0, float(24 * 365 * 20)),
        "first_time_card_ratio": (0.0, 1.0),
        "settlement_change_days": (0.0, 3650.0),
        "temporal_burst_score": (0.0, 1.0),
    }
    for feature, (minimum, maximum) in bounds.items():
        value = getattr(tx, feature)
        if not _is_real_number(value):
            raise ValueError(f"{population} transaction {tx.tx_id!r} has non-numeric {feature}")
        if not math.isfinite(value):
            raise ValueError(f"{population} transaction {tx.tx_id!r} has non-finite {feature}")
        if value < minimum or value > maximum:
            raise ValueError(
                f"{population} transaction {tx.tx_id!r} has out-of-range {feature}; "
                f"expected [{minimum:g}, {maximum:g}]"
            )


def _validate_evidence_metadata(tx: Transaction, population: str, expected_label: int) -> None:
    """Reject schema-bypassed identity, label, or provenance before scoring can trust evidence."""
    if not isinstance(tx.tx_id, str) or not tx.tx_id.strip():
        raise ValueError(f"{population} evaluation transaction must have a non-empty string tx_id")
    if len(tx.tx_id) > 64:
        raise ValueError(f"{population} evaluation transaction tx_id must be at most 64 characters")
    if _CANONICAL_TX_ID.fullmatch(tx.tx_id) is None:
        raise ValueError(
            f"{population} evaluation transaction tx_id may contain only ASCII letters, digits, '.', '_', and '-'"
        )
    if type(tx.label) is not int or tx.label != expected_label:
        raise ValueError(
            f"{population} evaluation population must contain only label={expected_label} integer transactions"
        )
    if not isinstance(tx.attack_family, str) or not tx.attack_family or len(tx.attack_family) > 64:
        raise ValueError(
            f"{population} evaluation transaction attack_family must be a non-empty string of at most 64 characters"
        )
    if any(char.isspace() for char in tx.attack_family):
        raise ValueError(f"{population} evaluation transaction attack_family must not contain whitespace")
    if expected_label == 0 and tx.attack_family != "benign":
        raise ValueError("benign evaluation population must use the benign attack_family provenance label")
    if expected_label == 1 and tx.attack_family == "benign":
        raise ValueError("attack evaluation population must not use the benign attack_family provenance label")
    if expected_label == 1 and tx.attack_family not in SUPPORTED_ATTACK_FAMILIES:
        raise ValueError(
            "attack evaluation population contains an unsupported synthetic attack family; "
            "supported families: " + ", ".join(sorted(SUPPORTED_ATTACK_FAMILIES))
        )


def _duplicate_tx_ids(rows: list[Transaction]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for tx in rows:
        if tx.tx_id in seen:
            duplicates.add(tx.tx_id)
        seen.add(tx.tx_id)
    return duplicates


def _validate_evaluation_populations(
    benign: list[Transaction], attacks: list[Transaction]
) -> None:
    """Fail closed when compiler evidence populations are absent, malformed, or contaminated.

    FPR and coverage are only meaningful when evaluated against non-empty, correctly
    labeled populations with finite policy-driving features and independent transaction
    identities. Refuse synthesis rather than allowing denominator fallbacks, dataset
    inversion, duplicate weighting, cross-population contamination, or NaN comparison
    semantics to create misleading safety evidence.
    """
    if not benign:
        raise ValueError("benign evaluation population must not be empty")
    if not attacks:
        raise ValueError("attack evaluation population must not be empty")

    for tx in benign:
        _validate_evidence_metadata(tx, "benign", 0)
    for tx in attacks:
        _validate_evidence_metadata(tx, "attack", 1)

    duplicate_benign = _duplicate_tx_ids(benign)
    if duplicate_benign:
        raise ValueError(
            f"benign evaluation population contains duplicate tx_id values: {sorted(duplicate_benign)!r}"
        )
    duplicate_attacks = _duplicate_tx_ids(attacks)
    if duplicate_attacks:
        raise ValueError(
            f"attack evaluation population contains duplicate tx_id values: {sorted(duplicate_attacks)!r}"
        )
    overlapping_ids = {tx.tx_id for tx in benign} & {tx.tx_id for tx in attacks}
    if overlapping_ids:
        raise ValueError(
            f"benign and attack evaluation populations share tx_id values: {sorted(overlapping_ids)!r}"
        )

    for tx in benign:
        _validate_policy_features(tx, "benign")
    for tx in attacks:
        _validate_policy_features(tx, "attack")


def _percent_code(value: float) -> int:
    """Encode a compiler percentage threshold without binary-float truncation drift."""
    return int(Decimal(str(value)) * 100)


def _policy_id(generation: int, age: int, card: float, settle: int, burst: float) -> str:
    """Return a stable identity that encodes every threshold affecting policy semantics."""
    return (
        f"ZD-{generation:02d}-{int(age):03d}-{_percent_code(card):02d}-"
        f"{int(settle):02d}-{_percent_code(burst):02d}"
    )


class DefenceCompiler:
    """Searches a compact policy space for the best safe generalization."""

    def __init__(self, max_fpr: float = 0.02):
        _validate_max_fpr(max_fpr)
        self.max_fpr = max_fpr

    def synthesize(self, benign: list[Transaction], attacks: list[Transaction], generation: int) -> Policy:
        _validate_max_fpr(self.max_fpr)
        if isinstance(generation, bool) or not isinstance(generation, int) or not 1 <= generation <= 8:
            raise ValueError("generation must be an integer within [1, 8]")
        _validate_evaluation_populations(benign, attacks)

        age_grid = [48, 72, 96, 120, 168, 240]
        card_grid = [0.50, 0.58, 0.64, 0.70, 0.76]
        settlement_grid = [7, 14, 21, 30, 45]
        burst_grid = [0.50, 0.58, 0.64, 0.70, 0.76]

        best: tuple[float, Policy] | None = None
        for age, card, settle, burst in product(age_grid, card_grid, settlement_grid, burst_grid):
            candidate = Policy(
                policy_id=_policy_id(generation, age, card, settle, burst),
                merchant_age_max=age,
                first_time_card_ratio_min=card,
                settlement_change_days_max=settle,
                temporal_burst_score_min=burst,
                action="STEP_UP",
                estimated_latency_ms=0.35,
            )
            s = score_policy(candidate, benign, attacks)
            if s.fpr > self.max_fpr:
                continue
            complexity_penalty = (age / 240 + (1-card) + settle / 45 + (1-burst)) * 0.004
            utility = s.coverage - 3.5*s.fpr - complexity_penalty
            if best is None or utility > best[0]:
                candidate.fraud_coverage = round(s.coverage, 4)
                candidate.false_positive_rate = round(s.fpr, 4)
                candidate.explanation = (
                    "Step up transactions when a very young merchant simultaneously exhibits "
                    "high first-time-card concentration, a recent settlement change, and burst-like timing."
                )
                best = (utility, candidate)

        if best is None:
            raise RuntimeError("No policy satisfies the configured false-positive budget")
        return best[1]
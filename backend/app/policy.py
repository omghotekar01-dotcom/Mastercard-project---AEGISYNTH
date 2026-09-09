from __future__ import annotations
import math
import re
from dataclasses import dataclass
from decimal import Decimal
from itertools import product
from .contracts import (
    COMPILER_GENERATION_MAX,
    COMPILER_GENERATION_MIN,
    DEFAULT_MAX_FALSE_POSITIVE_RATE,
    POLICY_FIRST_TIME_CARD_RATIO_MAX,
    POLICY_FIRST_TIME_CARD_RATIO_MIN,
    POLICY_MERCHANT_AGE_HOURS_MAX,
    POLICY_MERCHANT_AGE_HOURS_MIN,
    POLICY_SETTLEMENT_CHANGE_DAYS_MAX,
    POLICY_SETTLEMENT_CHANGE_DAYS_MIN,
    POLICY_TEMPORAL_BURST_SCORE_MAX,
    POLICY_TEMPORAL_BURST_SCORE_MIN,
)
from .schemas import Policy, Transaction
from .simulator import SUPPORTED_ATTACK_FAMILIES

FEATURES = (
    "merchant_age_hours",
    "first_time_card_ratio",
    "settlement_change_days",
    "temporal_burst_score",
)
_COMPILER_ESTIMATED_LATENCY_MS = 0.35
_CANONICAL_POLICY_ID = re.compile(r"^[A-Za-z0-9._-]+$")
_CANONICAL_TX_ID = re.compile(r"^[A-Za-z0-9._-]+$")
_COMPILER_POLICY_ID = re.compile(r"^ZD-(\d{2})-(\d{3})-(\d{2})-(\d{2})-(\d{2})$")
_COMPILER_AGE_GRID = (48, 72, 96, 120, 168, 240)
_COMPILER_CARD_GRID = (0.50, 0.58, 0.64, 0.70, 0.76)
_COMPILER_SETTLEMENT_GRID = (7, 14, 21, 30, 45)
_COMPILER_BURST_GRID = (0.50, 0.58, 0.64, 0.70, 0.76)
_COMPILER_AGE_CODES = frozenset(_COMPILER_AGE_GRID)
_COMPILER_CARD_PERCENT_CODES = frozenset(int(Decimal(str(value)) * 100) for value in _COMPILER_CARD_GRID)
_COMPILER_SETTLEMENT_CODES = frozenset(_COMPILER_SETTLEMENT_GRID)
_COMPILER_BURST_PERCENT_CODES = frozenset(int(Decimal(str(value)) * 100) for value in _COMPILER_BURST_GRID)

_POLICY_BOUNDS = {
    "merchant_age_max": (POLICY_MERCHANT_AGE_HOURS_MIN, POLICY_MERCHANT_AGE_HOURS_MAX),
    "first_time_card_ratio_min": (POLICY_FIRST_TIME_CARD_RATIO_MIN, POLICY_FIRST_TIME_CARD_RATIO_MAX),
    "settlement_change_days_max": (
        POLICY_SETTLEMENT_CHANGE_DAYS_MIN,
        POLICY_SETTLEMENT_CHANGE_DAYS_MAX,
    ),
    "temporal_burst_score_min": (POLICY_TEMPORAL_BURST_SCORE_MIN, POLICY_TEMPORAL_BURST_SCORE_MAX),
}
_TRANSACTION_FEATURE_BOUNDS = {
    "merchant_age_hours": (POLICY_MERCHANT_AGE_HOURS_MIN, POLICY_MERCHANT_AGE_HOURS_MAX),
    "first_time_card_ratio": (POLICY_FIRST_TIME_CARD_RATIO_MIN, POLICY_FIRST_TIME_CARD_RATIO_MAX),
    "settlement_change_days": (
        POLICY_SETTLEMENT_CHANGE_DAYS_MIN,
        POLICY_SETTLEMENT_CHANGE_DAYS_MAX,
    ),
    "temporal_burst_score": (POLICY_TEMPORAL_BURST_SCORE_MIN, POLICY_TEMPORAL_BURST_SCORE_MAX),
}

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
    if not any(char.isalnum() for char in policy.policy_id):
        raise ValueError("scored policy policy_id must contain at least one ASCII letter or digit")
    if not isinstance(policy.action, str):
        raise ValueError("scored policy action must be a string")
    if policy.action not in {"PASS", "STEP_UP", "REVIEW"}:
        raise ValueError("scored policy action must be one of PASS, STEP_UP, or REVIEW")
    if policy.action == "PASS":
        raise ValueError("scored fraud defence may not use PASS as the triggered action")

    for field, (minimum, maximum) in _POLICY_BOUNDS.items():
        value = getattr(policy, field)
        if not _is_real_number(value):
            raise ValueError(f"scored policy has non-numeric {field}")
        if not math.isfinite(value):
            raise ValueError(f"scored policy has non-finite {field}")
        if value < minimum or value > maximum:
            raise ValueError(
                f"scored policy has out-of-range {field}; expected [{minimum:g}, {maximum:g}]"
            )

    if not _is_real_number(policy.estimated_latency_ms):
        raise ValueError("scored policy has non-numeric estimated_latency_ms")
    if not math.isfinite(policy.estimated_latency_ms) or policy.estimated_latency_ms < 0:
        raise ValueError("scored policy estimated_latency_ms must be finite and >= 0")

    _validate_compiler_identity_binding(policy)


def _validate_compiler_identity_binding(policy: Policy) -> None:
    """Reject stale or fabricated compiler identities before metrics can be scored or reported.

    Any ID that claims compiler lineage via the ``ZD-`` prefix, regardless of prefix case,
    must use the exact canonical compiler identity, retain compiler action/latency claims,
    encode a threshold tuple from the native search grid, and match the policy semantics.
    This keeps benchmark scoring aligned with formal verification and prevents a mutated
    off-grid policy from presenting itself as native compiler output.
    """
    if not policy.policy_id.upper().startswith("ZD-"):
        return

    match = _COMPILER_POLICY_ID.fullmatch(policy.policy_id)
    if match is None:
        raise ValueError("scored compiler policy has malformed ZD policy_id")

    generation, age, card_percent, settle, burst_percent = (int(value) for value in match.groups())
    if not COMPILER_GENERATION_MIN <= generation <= COMPILER_GENERATION_MAX:
        raise ValueError(
            f"scored compiler policy generation must be within "
            f"[{COMPILER_GENERATION_MIN}, {COMPILER_GENERATION_MAX}]"
        )
    if (
        age not in _COMPILER_AGE_CODES
        or card_percent not in _COMPILER_CARD_PERCENT_CODES
        or settle not in _COMPILER_SETTLEMENT_CODES
        or burst_percent not in _COMPILER_BURST_PERCENT_CODES
    ):
        raise ValueError("scored compiler policy thresholds are outside the native compiler search grid")
    if policy.action != "STEP_UP":
        raise ValueError("scored compiler policy must retain the compiler STEP_UP action")
    if (
        not _is_real_number(policy.estimated_latency_ms)
        or float(policy.estimated_latency_ms) != _COMPILER_ESTIMATED_LATENCY_MS
    ):
        raise ValueError("scored compiler policy must retain the compiler estimated latency")

    expected = (
        float(age),
        card_percent / 100,
        float(settle),
        burst_percent / 100,
    )
    actual = (
        float(policy.merchant_age_max),
        float(policy.first_time_card_ratio_min),
        float(policy.settlement_change_days_max),
        float(policy.temporal_burst_score_min),
    )
    if actual != expected:
        raise ValueError(
            "scored compiler policy ZD policy_id does not encode the scored thresholds"
        )


def _validate_policy_features(tx: Transaction, population: str) -> None:
    """Validate policy-driving evidence against the same domains used by formal verification."""
    for feature, (minimum, maximum) in _TRANSACTION_FEATURE_BOUNDS.items():
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
    if not any(char.isalnum() for char in tx.tx_id):
        raise ValueError(
            f"{population} evaluation transaction tx_id must contain at least one ASCII letter or digit"
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

    def __init__(self, max_fpr: float = DEFAULT_MAX_FALSE_POSITIVE_RATE):
        _validate_max_fpr(max_fpr)
        self.max_fpr = max_fpr

    def synthesize(self, benign: list[Transaction], attacks: list[Transaction], generation: int) -> Policy:
        _validate_max_fpr(self.max_fpr)
        if (
            type(generation) is not int
            or not COMPILER_GENERATION_MIN <= generation <= COMPILER_GENERATION_MAX
        ):
            raise ValueError(
                f"generation must be an integer within "
                f"[{COMPILER_GENERATION_MIN}, {COMPILER_GENERATION_MAX}]"
            )
        _validate_evaluation_populations(benign, attacks)

        best: tuple[float, Policy] | None = None
        for age, card, settle, burst in product(
            _COMPILER_AGE_GRID,
            _COMPILER_CARD_GRID,
            _COMPILER_SETTLEMENT_GRID,
            _COMPILER_BURST_GRID,
        ):
            candidate = Policy(
                policy_id=_policy_id(generation, age, card, settle, burst),
                merchant_age_max=age,
                first_time_card_ratio_min=card,
                settlement_change_days_max=settle,
                temporal_burst_score_min=burst,
                action="STEP_UP",
                estimated_latency_ms=_COMPILER_ESTIMATED_LATENCY_MS,
            )
            s = score_policy(candidate, benign, attacks)
            reported_fpr = round(s.fpr, 4)
            if s.fpr > self.max_fpr or reported_fpr > self.max_fpr:
                continue
            complexity_penalty = (age / 240 + (1-card) + settle / 45 + (1-burst)) * 0.004
            utility = s.coverage - 3.5*s.fpr - complexity_penalty
            if best is None or utility > best[0]:
                candidate.fraud_coverage = round(s.coverage, 4)
                candidate.false_positive_rate = reported_fpr
                candidate.explanation = (
                    "Step up transactions when a very young merchant simultaneously exhibits "
                    "high first-time-card concentration, a recent settlement change, and burst-like timing."
                )
                best = (utility, candidate)

        if best is None:
            raise RuntimeError("No policy satisfies the configured false-positive budget")
        return best[1]
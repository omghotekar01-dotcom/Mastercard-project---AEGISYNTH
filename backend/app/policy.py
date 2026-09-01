from __future__ import annotations
import math
from dataclasses import dataclass
from itertools import product
from .schemas import Policy, Transaction

FEATURES = (
    "merchant_age_hours",
    "first_time_card_ratio",
    "settlement_change_days",
    "temporal_burst_score",
)

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
    blocked = sum(matches(policy, tx) for tx in attacks)
    benign_hits = sum(matches(policy, tx) for tx in benign)
    return Score(
        coverage=blocked / max(1, len(attacks)),
        fpr=benign_hits / max(1, len(benign)),
        blocked_attacks=blocked,
        benign_hits=benign_hits,
    )


def _validate_evaluation_populations(
    benign: list[Transaction], attacks: list[Transaction]
) -> None:
    """Fail closed when compiler evidence populations are absent or mislabeled.

    FPR and coverage are only meaningful when evaluated against non-empty, correctly
    labeled populations. Refuse synthesis rather than allowing denominator fallbacks or
    accidental dataset inversion to create misleading safety evidence.
    """
    if not benign:
        raise ValueError("benign evaluation population must not be empty")
    if not attacks:
        raise ValueError("attack evaluation population must not be empty")
    if any(tx.label != 0 for tx in benign):
        raise ValueError("benign evaluation population must contain only label=0 transactions")
    if any(tx.label != 1 for tx in attacks):
        raise ValueError("attack evaluation population must contain only label=1 transactions")


class DefenceCompiler:
    """Searches a compact policy space for the best safe generalization."""

    def __init__(self, max_fpr: float = 0.02):
        if not math.isfinite(max_fpr) or not 0 <= max_fpr <= 1:
            raise ValueError("max_fpr must be finite and within [0, 1]")
        self.max_fpr = max_fpr

    def synthesize(self, benign: list[Transaction], attacks: list[Transaction], generation: int) -> Policy:
        _validate_evaluation_populations(benign, attacks)

        age_grid = [48, 72, 96, 120, 168, 240]
        card_grid = [0.50, 0.58, 0.64, 0.70, 0.76]
        settlement_grid = [7, 14, 21, 30, 45]
        burst_grid = [0.50, 0.58, 0.64, 0.70, 0.76]

        best: tuple[float, Policy] | None = None
        for age, card, settle, burst in product(age_grid, card_grid, settlement_grid, burst_grid):
            candidate = Policy(
                policy_id=f"ZD-{generation:02d}-{int(age):03d}-{int(card*100):02d}",
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

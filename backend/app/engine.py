from __future__ import annotations
import math
import re
from .schemas import LabResult, IterationResult, Policy, CounterexampleTrace
from .simulator import PaymentWorld, SUPPORTED_ATTACK_FAMILIES
from .policy import DefenceCompiler, score_policy, matches
from .verification import verify_policy

_CANONICAL_TX_ID = re.compile(r"^[A-Za-z0-9._-]+$")


class AegisynthEngine:
    def __init__(self, seed: int = 42, max_fpr: float = 0.02):
        self.seed = self._validate_seed(seed)
        self.max_fpr = max_fpr

    @staticmethod
    def _validate_seed(seed: object) -> int:
        """Require canonical non-negative integer seeds before any benchmark RNG is created."""
        if type(seed) is not int or seed < 0:
            raise ValueError("seed must be a non-negative integer")
        return seed

    @staticmethod
    def _baseline_attack_success(attacks) -> float:
        """Compute baseline ASR only from valid, independent synthetic attack evidence."""
        if not attacks:
            raise ValueError("baseline attack population must not be empty")

        seen_ids: set[str] = set()
        for tx in attacks:
            if not isinstance(tx.tx_id, str) or not tx.tx_id.strip():
                raise ValueError("baseline attack evidence must have a non-empty string tx_id")
            if len(tx.tx_id) > 64:
                raise ValueError("baseline attack evidence tx_id must be at most 64 characters")
            if _CANONICAL_TX_ID.fullmatch(tx.tx_id) is None:
                raise ValueError(
                    "baseline attack evidence tx_id may contain only ASCII letters, digits, '.', '_', and '-'"
                )
            if tx.tx_id in seen_ids:
                raise ValueError("baseline attack evidence must not contain duplicate tx_id values")
            seen_ids.add(tx.tx_id)

            if type(tx.label) is not int or tx.label != 1:
                raise ValueError("baseline attack evidence must contain only label=1 integer transactions")
            if tx.attack_family not in SUPPORTED_ATTACK_FAMILIES:
                raise ValueError(
                    "baseline attack evidence contains an unsupported synthetic attack family"
                )

            feature_bounds = {
                "merchant_age_hours": (0.0, float(24 * 365 * 20)),
                "temporal_burst_score": (0.0, 1.0),
            }
            for feature, (minimum, maximum) in feature_bounds.items():
                value = getattr(tx, feature)
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ValueError(f"baseline attack evidence has non-numeric {feature}")
                if not math.isfinite(value) or not minimum <= value <= maximum:
                    raise ValueError(f"baseline attack evidence has invalid {feature}")

        caught = sum(
            (tx.merchant_age_hours < 48 and tx.temporal_burst_score > 0.82)
            for tx in attacks
        )
        return 1 - caught / len(attacks)

    @staticmethod
    def _validate_generations(generations: object) -> int:
        """Keep direct engine runs inside the supported, review-package-safe generation domain."""
        if type(generations) is not int or not 1 <= generations <= 8:
            raise ValueError("generations must be an integer within [1, 8]")
        return generations

    def run(self, generations: int = 4, attack_family: str = "ghost_merchant_swarm") -> LabResult:
        generations = self._validate_generations(generations)
        world = PaymentWorld(self.seed)
        compiler = DefenceCompiler(self.max_fpr)
        benign = world.benign(1400)
        seed_attacks = world.attack(600, attack_family, hardness=0.05)
        baseline_asr = self._baseline_attack_success(seed_attacks)

        iterations: list[IterationResult] = []
        current_attacks = seed_attacks
        final_policy: Policy | None = None
        verification_notes: list[str] = []

        for generation in range(1, generations + 1):
            training_attack_count = len(current_attacks)
            candidate = compiler.synthesize(benign, current_attacks, generation)
            harder = world.attack(700, attack_family, hardness=min(0.18*generation, 0.72))
            counterexamples = [tx for tx in harder if not matches(candidate, tx)]
            s = score_policy(candidate, benign, harder)
            candidate.counterexamples_remaining = len(counterexamples)
            candidate.fraud_coverage = round(s.coverage, 4)
            candidate.false_positive_rate = round(s.fpr, 4)
            ok, notes = verify_policy(candidate, self.max_fpr)
            if not ok:
                raise RuntimeError(
                    f"Policy verification failed at generation {generation}; refusing to emit unverified lab evidence"
                )
            candidate.verified = True

            trace = CounterexampleTrace(
                training_attack_count=training_attack_count,
                redteam_attack_count=len(harder),
                escaped_count=len(counterexamples),
                escaped_rate=round(len(counterexamples) / max(1, len(harder)), 4),
                sample_tx_ids=[tx.tx_id for tx in counterexamples[:5]],
            )

            iterations.append(IterationResult(
                iteration=generation,
                candidate=candidate,
                counterexamples=len(counterexamples),
                attack_success_rate=round(1 - s.coverage, 4),
                trace=trace,
            ))
            final_policy = candidate
            verification_notes = notes
            replayed_counterexamples = [
                tx.model_copy(update={"tx_id": f"{tx.tx_id}-CE{generation:02d}"})
                for tx in counterexamples
            ]
            current_attacks = seed_attacks + harder + replayed_counterexamples

        assert final_policy is not None
        final_asr = iterations[-1].attack_success_rate
        metrics = {
            "attack_success_reduction": round(baseline_asr - final_asr, 4),
            "final_fraud_coverage": final_policy.fraud_coverage,
            "final_false_positive_rate": final_policy.false_positive_rate,
            "estimated_policy_latency_ms": final_policy.estimated_latency_ms,
            "benign_acceptance_rate": round(1-final_policy.false_positive_rate, 4),
        }
        return LabResult(
            attack_family=attack_family,
            seed=self.seed,
            baseline_attack_success_rate=round(baseline_asr, 4),
            final_attack_success_rate=final_asr,
            iterations=iterations,
            final_policy=final_policy,
            verification_notes=verification_notes,
            metrics=metrics,
        )
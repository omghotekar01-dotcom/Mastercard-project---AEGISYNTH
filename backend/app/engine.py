from __future__ import annotations
from .schemas import LabResult, IterationResult, Policy, CounterexampleTrace
from .simulator import PaymentWorld
from .policy import DefenceCompiler, score_policy, matches
from .verification import verify_policy

class AegisynthEngine:
    def __init__(self, seed: int = 42, max_fpr: float = 0.02):
        self.seed = seed
        self.max_fpr = max_fpr

    @staticmethod
    def _baseline_attack_success(attacks) -> float:
        caught = sum(
            (tx.merchant_age_hours < 48 and tx.temporal_burst_score > 0.82)
            for tx in attacks
        )
        return 1 - caught / max(1, len(attacks))

    def run(self, generations: int = 4, attack_family: str = "ghost_merchant_swarm") -> LabResult:
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
            candidate.verified = ok

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
            current_attacks = seed_attacks + harder + counterexamples

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

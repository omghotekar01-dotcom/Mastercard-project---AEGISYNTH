from app.engine import AegisynthEngine
from app.verification import verify_policy


def test_lab_compiles_verified_policy():
    result = AegisynthEngine(seed=7).run(generations=3)
    assert result.final_policy.verified
    assert result.final_policy.false_positive_rate <= 0.02
    assert result.final_policy.action in {"STEP_UP", "REVIEW"}


def test_compiled_policy_reduces_attack_success():
    result = AegisynthEngine(seed=11).run(generations=4)
    assert result.final_attack_success_rate < result.baseline_attack_success_rate
    assert result.metrics.benign_acceptance_rate >= 0.98
    assert result.metrics.final_fraud_coverage == result.final_policy.fraud_coverage
    assert result.metrics.final_false_positive_rate == result.final_policy.false_positive_rate


def test_verifier_accepts_compiler_output():
    result = AegisynthEngine(seed=19).run(generations=2)
    ok, notes = verify_policy(result.final_policy)
    assert ok
    assert len(notes) >= 3

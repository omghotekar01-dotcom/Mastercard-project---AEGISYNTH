import pytest

from app.engine import AegisynthEngine
from app.simulator import PaymentWorld
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


def test_counterexample_trace_is_consistent_and_deterministic():
    a = AegisynthEngine(seed=42).run(generations=4)
    b = AegisynthEngine(seed=42).run(generations=4)

    assert [i.trace.model_dump() for i in a.iterations] == [i.trace.model_dump() for i in b.iterations]
    for iteration in a.iterations:
        trace = iteration.trace
        assert trace.redteam_attack_count == 700
        assert trace.escaped_count == iteration.counterexamples
        assert trace.escaped_rate == iteration.attack_success_rate
        assert len(trace.sample_tx_ids) <= 5
        assert all(tx_id.startswith("A-") for tx_id in trace.sample_tx_ids)


def test_payment_world_assigns_unique_ids_across_repeated_batches():
    world = PaymentWorld(seed=42)
    benign_a = world.benign(3)
    benign_b = world.benign(2)
    attack_a = world.attack(3)
    attack_b = world.attack(2, hardness=0.2)

    benign_ids = [tx.tx_id for tx in benign_a + benign_b]
    attack_ids = [tx.tx_id for tx in attack_a + attack_b]

    assert benign_ids == ["B-000000", "B-000001", "B-000002", "B-000003", "B-000004"]
    assert attack_ids == ["A-000000", "A-000001", "A-000002", "A-000003", "A-000004"]
    assert len(benign_ids) == len(set(benign_ids))
    assert len(attack_ids) == len(set(attack_ids))


def test_baseline_attack_success_rejects_empty_population():
    with pytest.raises(ValueError, match="baseline attack population must not be empty"):
        AegisynthEngine._baseline_attack_success([])


@pytest.mark.parametrize("generations", [0, 9, True, 2.0, "4", None])
def test_engine_rejects_unsupported_generation_counts(generations):
    with pytest.raises(ValueError, match=r"generations must be an integer within \[1, 8\]"):
        AegisynthEngine(seed=42).run(generations=generations)

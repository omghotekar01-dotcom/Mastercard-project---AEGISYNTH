import inspect

from app import main as main_module
from app.contracts import DEFAULT_MAX_POLICY_LATENCY_MS
from app.verification import verify_policy


def test_default_policy_latency_budget_matches_submitted_contract():
    assert DEFAULT_MAX_POLICY_LATENCY_MS == 5.0
    assert DEFAULT_MAX_POLICY_LATENCY_MS > 0


def test_verifier_default_uses_shared_latency_budget():
    signature = inspect.signature(verify_policy)
    assert signature.parameters["max_latency_ms"].default == DEFAULT_MAX_POLICY_LATENCY_MS


def test_deployment_benchmark_gate_uses_same_latency_budget():
    result = main_module._benchmark()
    assert result.final_policy.estimated_latency_ms <= DEFAULT_MAX_POLICY_LATENCY_MS

    checks = main_module._benchmark_contract_checks(result)
    assert checks["latency_budget"] is True


def test_deployment_gate_fails_closed_immediately_above_latency_budget():
    result = main_module._benchmark()
    drifted = result.model_copy(
        update={
            "final_policy": result.final_policy.model_copy(
                update={"estimated_latency_ms": DEFAULT_MAX_POLICY_LATENCY_MS + 0.0001}
            )
        }
    )

    checks = main_module._benchmark_contract_checks(drifted)
    assert checks["latency_budget"] is False
    assert main_module._benchmark_replay_operational(drifted) is False

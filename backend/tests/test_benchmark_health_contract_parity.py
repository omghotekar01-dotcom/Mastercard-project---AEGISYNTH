import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app

client = TestClient(app)


def _drift_seed(result):
    return result.model_copy(update={"seed": result.seed + 1})


def _drift_attack_family(result):
    return result.model_copy(update={"attack_family": "synthetic_contract_drift"})


def _drift_generation_count(result):
    return result.model_copy(update={"iterations": result.iterations[:-1]})


def _drift_baseline_claim(result):
    return result.model_copy(
        update={"baseline_attack_success_rate": result.baseline_attack_success_rate + 0.0001}
    )


def _drift_final_claim(result):
    return result.model_copy(
        update={"final_attack_success_rate": result.final_attack_success_rate + 0.0001}
    )


def _drift_fraud_coverage(result):
    return result.model_copy(
        update={
            "metrics": result.metrics.model_copy(
                update={"final_fraud_coverage": result.metrics.final_fraud_coverage - 0.0001}
            )
        }
    )


def _drift_benign_acceptance(result):
    return result.model_copy(
        update={
            "metrics": result.metrics.model_copy(
                update={"benign_acceptance_rate": result.metrics.benign_acceptance_rate - 0.0001}
            )
        }
    )


def _drift_policy_verified(result):
    return result.model_copy(
        update={"final_policy": result.final_policy.model_copy(update={"verified": False})}
    )


def _drift_responsible_action(result):
    return result.model_copy(
        update={"final_policy": result.final_policy.model_copy(update={"action": "ALLOW"})}
    )


def _drift_false_positive_budget(result):
    return result.model_copy(
        update={
            "final_policy": result.final_policy.model_copy(
                update={
                    "false_positive_rate": main_module.DEFAULT_MAX_FALSE_POSITIVE_RATE + 0.0001
                }
            )
        }
    )


def _drift_latency_budget(result):
    return result.model_copy(
        update={
            "final_policy": result.final_policy.model_copy(
                update={
                    "estimated_latency_ms": main_module.DEFAULT_MAX_POLICY_LATENCY_MS + 0.0001
                }
            )
        }
    )


@pytest.mark.parametrize(
    "drift,failed_check",
    [
        (_drift_seed, "benchmark_seed"),
        (_drift_attack_family, "attack_family"),
        (_drift_generation_count, "generation_count"),
        (_drift_baseline_claim, "baseline_attack_success"),
        (_drift_final_claim, "final_attack_success"),
        (_drift_fraud_coverage, "fraud_coverage"),
        (_drift_benign_acceptance, "benign_acceptance"),
        (_drift_policy_verified, "policy_verified"),
        (_drift_responsible_action, "responsible_action"),
        (_drift_false_positive_budget, "false_positive_budget"),
        (_drift_latency_budget, "latency_budget"),
    ],
    ids=[
        "seed",
        "attack-family",
        "generation-count",
        "baseline-attack-success",
        "final-attack-success",
        "fraud-coverage",
        "benign-acceptance",
        "policy-verified",
        "responsible-action",
        "false-positive-budget",
        "latency-budget",
    ],
)
def test_readiness_and_self_check_fail_closed_on_same_committed_benchmark_drift(
    monkeypatch, drift, failed_check
):
    """Deployment probes must share one benchmark/safety contract evaluator."""
    benchmark = main_module._benchmark()
    drifted = drift(benchmark)

    contract_checks = main_module._benchmark_contract_checks(drifted)
    assert contract_checks[failed_check] is False
    assert sum(not value for value in contract_checks.values()) == 1

    monkeypatch.setattr(main_module, "_benchmark", lambda: drifted)

    ready_response = client.get("/ready")
    self_check_response = client.get("/api/v1/self-check")

    assert ready_response.status_code == 503
    assert ready_response.json()["status"] == "not_ready"
    assert ready_response.json()["checks"]["benchmark_replay_operational"] is False

    assert self_check_response.status_code == 503
    assert self_check_response.json()["status"] == "fail"
    assert self_check_response.json()["checks"][failed_check] is False

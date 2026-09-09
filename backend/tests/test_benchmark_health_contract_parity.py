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


@pytest.mark.parametrize(
    "drift",
    [
        _drift_seed,
        _drift_attack_family,
        _drift_generation_count,
        _drift_baseline_claim,
        _drift_final_claim,
        _drift_fraud_coverage,
        _drift_benign_acceptance,
    ],
    ids=[
        "seed",
        "attack-family",
        "generation-count",
        "baseline-attack-success",
        "final-attack-success",
        "fraud-coverage",
        "benign-acceptance",
    ],
)
def test_readiness_and_self_check_fail_closed_on_same_committed_benchmark_drift(
    monkeypatch, drift
):
    """Deployment probes must agree when any submitted benchmark contract field drifts."""
    benchmark = main_module._benchmark()
    drifted = drift(benchmark)
    monkeypatch.setattr(main_module, "_benchmark", lambda: drifted)

    ready_response = client.get("/ready")
    self_check_response = client.get("/api/v1/self-check")

    assert ready_response.status_code == 503
    assert ready_response.json()["status"] == "not_ready"
    assert ready_response.json()["checks"]["benchmark_replay_operational"] is False

    assert self_check_response.status_code == 503
    assert self_check_response.json()["status"] == "fail"

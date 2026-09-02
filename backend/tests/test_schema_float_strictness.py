import pytest
from pydantic import ValidationError

from app.schemas import (
    CompilationProvenance,
    CounterexampleTrace,
    IterationResult,
    LabMetrics,
    LabResult,
    Policy,
)


def _policy() -> Policy:
    return Policy(
        policy_id="strict-float-test",
        merchant_age_max=24,
        first_time_card_ratio_min=0.5,
        settlement_change_days_max=7,
        temporal_burst_score_min=0.5,
    )


def _trace() -> CounterexampleTrace:
    return CounterexampleTrace(
        training_attack_count=1,
        redteam_attack_count=1,
        escaped_count=0,
        escaped_rate=0.0,
    )


def _metrics_payload() -> dict:
    return {
        "attack_success_reduction": 0.0,
        "final_fraud_coverage": 0.0,
        "final_false_positive_rate": 0.0,
        "estimated_policy_latency_ms": 1.0,
        "benign_acceptance_rate": 1.0,
    }


@pytest.mark.parametrize("value", [False, True])
def test_counterexample_trace_rejects_boolean_escaped_rate(value):
    with pytest.raises(ValidationError):
        CounterexampleTrace(
            training_attack_count=1,
            redteam_attack_count=1,
            escaped_count=0,
            escaped_rate=value,
        )


@pytest.mark.parametrize("value", [False, True])
def test_iteration_result_rejects_boolean_attack_success_rate(value):
    with pytest.raises(ValidationError):
        IterationResult(
            iteration=1,
            candidate=_policy(),
            counterexamples=0,
            attack_success_rate=value,
            trace=_trace(),
        )


@pytest.mark.parametrize(
    "field",
    [
        "attack_success_reduction",
        "final_fraud_coverage",
        "final_false_positive_rate",
        "estimated_policy_latency_ms",
        "benign_acceptance_rate",
    ],
)
@pytest.mark.parametrize("value", [False, True])
def test_lab_metrics_reject_boolean_numeric_evidence(field, value):
    payload = _metrics_payload()
    payload[field] = value

    with pytest.raises(ValidationError):
        LabMetrics(**payload)


@pytest.mark.parametrize("field", ["baseline_attack_success_rate", "final_attack_success_rate"])
@pytest.mark.parametrize("value", [False, True])
def test_lab_result_rejects_boolean_rates(field, value):
    payload = {
        "attack_family": "synthetic",
        "seed": 42,
        "baseline_attack_success_rate": 1.0,
        "final_attack_success_rate": 0.0,
        "iterations": [],
        "final_policy": _policy(),
        "verification_notes": [],
        "metrics": LabMetrics(**_metrics_payload()),
    }
    payload[field] = value

    with pytest.raises(ValidationError):
        LabResult(**payload)


@pytest.mark.parametrize("field", ["max_false_positive_rate", "max_policy_latency_ms"])
@pytest.mark.parametrize("value", [False, True])
def test_compilation_provenance_rejects_boolean_budgets(field, value):
    payload = {
        "compiler_id": "compiler",
        "verifier_id": "verifier",
        "generation_count": 1,
        "max_false_positive_rate": 0.02,
        "max_policy_latency_ms": 5.0,
    }
    payload[field] = value

    with pytest.raises(ValidationError):
        CompilationProvenance(**payload)

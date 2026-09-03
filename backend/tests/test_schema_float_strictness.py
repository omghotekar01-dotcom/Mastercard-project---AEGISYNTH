import math

import pytest
from pydantic import ValidationError

from app.schemas import (
    CompilationProvenance,
    CounterexampleTrace,
    IterationResult,
    LabMetrics,
    LabResult,
    Policy,
    Transaction,
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


def _transaction_payload() -> dict:
    return {
        "tx_id": "synthetic-1",
        "amount": 10.0,
        "merchant_age_hours": 24.0,
        "first_time_card_ratio": 0.5,
        "settlement_change_days": 2.0,
        "temporal_burst_score": 0.4,
        "device_entropy": 0.7,
        "geo_velocity": 3.0,
        "label": 0,
        "attack_family": "benign",
    }


@pytest.mark.parametrize(
    "field",
    [
        "amount",
        "merchant_age_hours",
        "first_time_card_ratio",
        "settlement_change_days",
        "temporal_burst_score",
        "device_entropy",
        "geo_velocity",
    ],
)
@pytest.mark.parametrize("value", [math.inf, -math.inf, math.nan])
def test_transaction_rejects_non_finite_numeric_features(field, value):
    payload = _transaction_payload()
    payload[field] = value

    with pytest.raises(ValidationError):
        Transaction(**payload)


@pytest.mark.parametrize("value", [math.inf, -math.inf, math.nan])
def test_policy_rejects_non_finite_latency(value):
    payload = _policy().model_dump()
    payload["estimated_latency_ms"] = value

    with pytest.raises(ValidationError):
        Policy(**payload)


@pytest.mark.parametrize("value", [math.inf, -math.inf, math.nan])
def test_lab_metrics_reject_non_finite_latency(value):
    payload = _metrics_payload()
    payload["estimated_policy_latency_ms"] = value

    with pytest.raises(ValidationError):
        LabMetrics(**payload)


@pytest.mark.parametrize("value", [math.inf, -math.inf, math.nan])
def test_compilation_provenance_rejects_non_finite_latency_budget(value):
    with pytest.raises(ValidationError):
        CompilationProvenance(
            compiler_id="compiler",
            verifier_id="verifier",
            generation_count=1,
            max_false_positive_rate=0.02,
            max_policy_latency_ms=value,
        )


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

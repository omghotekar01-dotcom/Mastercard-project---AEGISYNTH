import pytest
from pydantic import ValidationError

from app.schemas import (
    CompilationProvenance,
    CounterexampleTrace,
    IterationResult,
    LabMetrics,
    LabResult,
    Policy,
    ReviewPackage,
)


def _policy() -> Policy:
    return Policy(
        policy_id="strict-int-test",
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


def _metrics() -> LabMetrics:
    return LabMetrics(
        attack_success_reduction=0.0,
        final_fraud_coverage=0.0,
        final_false_positive_rate=0.0,
        estimated_policy_latency_ms=1.0,
        benign_acceptance_rate=1.0,
    )


def _provenance() -> CompilationProvenance:
    return CompilationProvenance(
        compiler_id="compiler",
        verifier_id="verifier",
        generation_count=1,
        max_false_positive_rate=0.02,
        max_policy_latency_ms=5.0,
    )


@pytest.mark.parametrize(
    "field",
    ["training_attack_count", "redteam_attack_count", "escaped_count"],
)
def test_counterexample_trace_rejects_boolean_counts(field):
    payload = {
        "training_attack_count": 1,
        "redteam_attack_count": 1,
        "escaped_count": 0,
        "escaped_rate": 0.0,
    }
    payload[field] = True

    with pytest.raises(ValidationError):
        CounterexampleTrace(**payload)


@pytest.mark.parametrize("field", ["iteration", "counterexamples"])
def test_iteration_result_rejects_boolean_integer_fields(field):
    payload = {
        "iteration": 1,
        "candidate": _policy(),
        "counterexamples": 0,
        "attack_success_rate": 0.0,
        "trace": _trace(),
    }
    payload[field] = True

    with pytest.raises(ValidationError):
        IterationResult(**payload)


def test_lab_result_rejects_boolean_seed():
    with pytest.raises(ValidationError):
        LabResult(
            attack_family="synthetic",
            seed=True,
            baseline_attack_success_rate=1.0,
            final_attack_success_rate=0.0,
            iterations=[],
            final_policy=_policy(),
            verification_notes=[],
            metrics=_metrics(),
        )


def test_compilation_provenance_rejects_boolean_generation_count():
    with pytest.raises(ValidationError):
        CompilationProvenance(
            compiler_id="compiler",
            verifier_id="verifier",
            generation_count=True,
            max_false_positive_rate=0.02,
            max_policy_latency_ms=5.0,
        )


def test_review_package_rejects_boolean_seed():
    with pytest.raises(ValidationError):
        ReviewPackage(
            artifact_sha256="0" * 64,
            attack_family="synthetic",
            seed=True,
            provenance=_provenance(),
            policy=_policy(),
            verification_notes=[],
        )

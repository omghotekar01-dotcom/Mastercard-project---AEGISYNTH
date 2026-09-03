import pytest
from pydantic import ValidationError

from app.engine import AegisynthEngine
from app.schemas import LabResult


def _result_payload() -> dict:
    return AegisynthEngine(seed=42).run(generations=2).model_dump()


def test_lab_result_rejects_empty_iterations():
    payload = _result_payload()
    payload["iterations"] = []

    with pytest.raises(ValidationError, match="iterations must contain at least one result"):
        LabResult.model_validate(payload)


def test_lab_result_rejects_final_policy_mismatch():
    payload = _result_payload()
    payload["final_policy"]["policy_id"] = "tampered-final-policy"

    with pytest.raises(ValidationError, match="final_policy must equal the last iteration candidate"):
        LabResult.model_validate(payload)


def test_lab_result_rejects_final_attack_success_mismatch():
    payload = _result_payload()
    payload["final_attack_success_rate"] = 1.0 - payload["final_attack_success_rate"]

    with pytest.raises(ValidationError, match="final_attack_success_rate must equal"):
        LabResult.model_validate(payload)


@pytest.mark.parametrize(
    ("metric", "replacement", "message"),
    [
        ("final_fraud_coverage", 0.0, "metrics.final_fraud_coverage must equal"),
        ("final_false_positive_rate", 1.0, "metrics.final_false_positive_rate must equal"),
        ("estimated_policy_latency_ms", 999.0, "metrics.estimated_policy_latency_ms must equal"),
        ("attack_success_reduction", 0.0, "metrics.attack_success_reduction must equal"),
        ("benign_acceptance_rate", 0.0, "metrics.benign_acceptance_rate must equal"),
    ],
)
def test_lab_result_rejects_contradictory_final_metrics(metric, replacement, message):
    payload = _result_payload()
    original = payload["metrics"][metric]
    payload["metrics"][metric] = replacement if replacement != original else 0.1234

    with pytest.raises(ValidationError, match=message):
        LabResult.model_validate(payload)


def test_current_engine_lab_result_remains_valid():
    result = AegisynthEngine(seed=42).run(generations=2)
    assert LabResult.model_validate(result.model_dump()) == result

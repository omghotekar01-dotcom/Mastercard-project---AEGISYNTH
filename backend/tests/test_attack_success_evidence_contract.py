import pytest

from app.engine import AegisynthEngine
from app.schemas import IterationResult


def test_iteration_attack_success_matches_escape_and_coverage_evidence():
    """Lock every reported ASR to the underlying escaped red-team population."""
    result = AegisynthEngine(seed=42).run(generations=4)

    for iteration in result.iterations:
        expected_asr = round(
            iteration.trace.escaped_count / iteration.trace.redteam_attack_count,
            4,
        )
        expected_from_coverage = round(1 - iteration.candidate.fraud_coverage, 4)

        assert iteration.trace.escaped_rate == expected_asr
        assert iteration.attack_success_rate == expected_asr
        assert iteration.attack_success_rate == expected_from_coverage

    assert result.final_attack_success_rate == result.iterations[-1].attack_success_rate
    assert result.metrics.final_fraud_coverage == result.final_policy.fraud_coverage


def test_iteration_schema_rejects_asr_that_disagrees_with_escape_trace():
    iteration = AegisynthEngine(seed=42).run(generations=1).iterations[0]
    payload = iteration.model_dump()
    payload["attack_success_rate"] = 1.0 if iteration.attack_success_rate != 1.0 else 0.0

    with pytest.raises(ValueError, match="attack_success_rate must equal trace.escaped_rate"):
        IterationResult.model_validate(payload)


def test_iteration_schema_rejects_asr_that_disagrees_with_policy_coverage():
    iteration = AegisynthEngine(seed=42).run(generations=1).iterations[0]
    payload = iteration.model_dump()
    original_coverage = payload["candidate"]["fraud_coverage"]
    payload["candidate"]["fraud_coverage"] = 0.0 if original_coverage != 0.0 else 1.0

    with pytest.raises(
        ValueError,
        match="attack_success_rate must equal one minus candidate.fraud_coverage",
    ):
        IterationResult.model_validate(payload)

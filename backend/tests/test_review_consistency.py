import pytest

from app.artifact import build_review_package
from app.engine import AegisynthEngine


def test_review_package_rejects_final_policy_detached_from_last_iteration():
    result = AegisynthEngine(seed=42).run(generations=4)
    result.final_policy = result.final_policy.model_copy(
        update={"policy_id": "ZD-detached-but-verifiable"}
    )

    with pytest.raises(ValueError, match="final policy does not match"):
        build_review_package(result)


def test_review_package_rejects_stale_summary_metrics():
    result = AegisynthEngine(seed=42).run(generations=4)
    result.metrics = result.metrics.model_copy(
        update={"final_fraud_coverage": max(0.0, result.metrics.final_fraud_coverage - 0.01)}
    )

    with pytest.raises(ValueError, match="summary metrics are inconsistent"):
        build_review_package(result)


def test_review_package_rejects_attack_reduction_beyond_reported_precision():
    result = AegisynthEngine(seed=42).run(generations=4)
    result.metrics = result.metrics.model_copy(
        update={
            "attack_success_reduction": round(
                result.metrics.attack_success_reduction + 0.0002, 4
            )
        }
    )

    with pytest.raises(ValueError, match="summary metrics are inconsistent"):
        build_review_package(result)


def test_review_package_rejects_noncontiguous_iteration_history():
    result = AegisynthEngine(seed=42).run(generations=4)
    result.iterations[2] = result.iterations[2].model_copy(update={"iteration": 4})

    with pytest.raises(ValueError, match="iteration history must be contiguous and ordered"):
        build_review_package(result)


def test_review_package_accepts_consistent_engine_result():
    result = AegisynthEngine(seed=42).run(generations=4)

    package = build_review_package(result)

    assert package.policy == result.iterations[-1].candidate
    assert package.provenance.generation_count == len(result.iterations)

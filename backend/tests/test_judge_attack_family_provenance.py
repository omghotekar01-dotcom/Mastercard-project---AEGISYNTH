import pytest
from pydantic import ValidationError

from app.engine import AegisynthEngine
from app.schemas import CompilationProvenance, LabResult, ReviewPackage


def _valid_result():
    return AegisynthEngine(seed=42).run(generations=2)


def _review_payload() -> dict:
    result = _valid_result()
    return {
        "package_version": "1.2",
        "artifact_sha256": "0" * 64,
        "attack_family": result.attack_family,
        "seed": result.seed,
        "provenance": CompilationProvenance(
            compiler_id="compact-grid-search-v1",
            verifier_id="z3-business-guardrails-v1",
            generation_count=len(result.iterations),
            max_false_positive_rate=0.02,
            max_policy_latency_ms=5.0,
        ).model_dump(),
        "policy": result.final_policy.model_dump(),
        "verification_notes": result.verification_notes,
        "approval_status": "HUMAN_APPROVAL_REQUIRED",
        "deployment_status": "NOT_DEPLOYED",
        "synthetic_only": True,
        "production_claim": False,
    }


@pytest.mark.parametrize("attack_family", ["benign", " ghost_merchant_swarm", "ghost merchant swarm", "ghost_merchant_swarm\t", "ghost_merchant_swarm\n"])
def test_lab_result_rejects_ambiguous_or_reserved_attack_family(attack_family):
    payload = _valid_result().model_dump()
    payload["attack_family"] = attack_family

    with pytest.raises(ValidationError, match="attack_family"):
        LabResult.model_validate(payload)


@pytest.mark.parametrize("attack_family", ["benign", " ghost_merchant_swarm", "ghost merchant swarm", "ghost_merchant_swarm\t", "ghost_merchant_swarm\n"])
def test_review_package_rejects_ambiguous_or_reserved_attack_family(attack_family):
    payload = _review_payload()
    payload["attack_family"] = attack_family

    with pytest.raises(ValidationError, match="attack_family"):
        ReviewPackage.model_validate(payload)


def test_current_engine_attack_family_remains_valid_for_both_judge_surfaces():
    result = _valid_result()
    assert LabResult.model_validate(result.model_dump()) == result
    package = ReviewPackage.model_validate(_review_payload())
    assert package.attack_family == result.attack_family == "ghost_merchant_swarm"

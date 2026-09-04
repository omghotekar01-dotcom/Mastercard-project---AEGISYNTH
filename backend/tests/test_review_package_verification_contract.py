import pytest
from pydantic import ValidationError

from app.schemas import CompilationProvenance, Policy, ReviewPackage


def _policy(*, verified: bool) -> Policy:
    return Policy(
        policy_id="policy-review-handoff-contract",
        merchant_age_max=720.0,
        first_time_card_ratio_min=0.5,
        settlement_change_days_max=30.0,
        temporal_burst_score_min=0.5,
        action="STEP_UP",
        fraud_coverage=0.9,
        false_positive_rate=0.01,
        estimated_latency_ms=1.0,
        counterexamples_remaining=0,
        verified=verified,
    )


def _package(*, verified: bool) -> ReviewPackage:
    return ReviewPackage(
        artifact_sha256="0" * 64,
        attack_family="synthetic_review_family",
        seed=0,
        provenance=CompilationProvenance(
            compiler_id="defence-compiler-v1",
            verifier_id="z3-verifier-v1",
            generation_count=1,
            max_false_positive_rate=0.02,
            max_policy_latency_ms=5.0,
        ),
        policy=_policy(verified=verified),
        verification_notes=["Z3 verification completed before review handoff."],
    )


def test_review_package_rejects_unverified_policy():
    with pytest.raises(ValidationError, match="review package policy must be verified"):
        _package(verified=False)


def test_review_package_accepts_verified_policy():
    package = _package(verified=True)

    assert package.policy.verified is True
    assert package.approval_status == "HUMAN_APPROVAL_REQUIRED"
    assert package.deployment_status == "NOT_DEPLOYED"

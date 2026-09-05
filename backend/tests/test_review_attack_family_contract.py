import hashlib

import pytest

from app.artifact import _canonical_fields, build_review_package, verify_review_package
from app.engine import AegisynthEngine
from app.schemas import LabResult, ReviewPackage


def _result():
    return AegisynthEngine(seed=42).run(generations=2)


def test_review_builder_rejects_unimplemented_attack_family_claim():
    payload = _result().model_dump()
    payload["attack_family"] = "unimplemented_family"
    forged = LabResult.model_validate(payload)

    with pytest.raises(
        ValueError,
        match="Review package requires an implemented synthetic attack family",
    ):
        build_review_package(forged)


def test_review_verifier_rejects_rehashed_unimplemented_attack_family_claim():
    package = build_review_package(_result())
    payload = package.model_dump()
    payload["attack_family"] = "unimplemented_family"

    canonical = _canonical_fields(
        package_version=payload["package_version"],
        attack_family=payload["attack_family"],
        seed=payload["seed"],
        provenance=payload["provenance"],
        policy=payload["policy"],
        verification_notes=payload["verification_notes"],
        approval_status=payload["approval_status"],
        deployment_status=payload["deployment_status"],
        synthetic_only=payload["synthetic_only"],
        production_claim=payload["production_claim"],
    )
    payload["artifact_sha256"] = hashlib.sha256(canonical).hexdigest()
    forged = ReviewPackage.model_validate(payload)

    assert verify_review_package(forged) is False


def test_current_implemented_family_still_builds_and_verifies():
    package = build_review_package(_result())

    assert package.attack_family == "ghost_merchant_swarm"
    assert verify_review_package(package) is True

from hashlib import sha256

import pytest

from app.artifact import _canonical_fields, build_review_package, verify_review_package
from app.engine import AegisynthEngine


def _refingerprint(package):
    canonical = _canonical_fields(
        package_version=package.package_version,
        attack_family=package.attack_family,
        seed=package.seed,
        provenance=package.provenance.model_dump(mode="json"),
        policy=package.policy.model_dump(mode="json"),
        verification_notes=package.verification_notes,
        approval_status=package.approval_status,
        deployment_status=package.deployment_status,
        synthetic_only=package.synthetic_only,
        production_claim=package.production_claim,
    )
    return package.model_copy(
        update={"artifact_sha256": sha256(canonical).hexdigest()}
    )


@pytest.mark.parametrize(
    ("field", "forged_value"),
    [
        ("approval_status", "APPROVED"),
        ("deployment_status", "CANARY"),
        ("synthetic_only", False),
        ("production_claim", True),
    ],
)
def test_review_package_rejects_governance_escalation_even_after_refingerprinting(
    field, forged_value
):
    package = build_review_package(AegisynthEngine(seed=42).run(generations=1))
    forged = package.model_copy(update={field: forged_value})
    forged = _refingerprint(forged)

    assert verify_review_package(package) is True
    assert forged.artifact_sha256 != package.artifact_sha256
    assert verify_review_package(forged) is False

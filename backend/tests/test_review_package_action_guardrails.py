import hashlib

import pytest

from app.artifact import _canonical_fields, build_review_package, verify_review_package
from app.engine import AegisynthEngine


def _recompute_digest(package) -> str:
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
    return hashlib.sha256(canonical).hexdigest()


@pytest.mark.parametrize("unsafe_action", ["PASS", "DECLINE"])
def test_review_package_rejects_unsafe_actions_even_with_recomputed_digest(unsafe_action):
    package = build_review_package(AegisynthEngine(seed=42).run(generations=2))
    tampered = package.model_copy(deep=True)
    tampered.policy.action = unsafe_action
    tampered.artifact_sha256 = _recompute_digest(tampered)

    assert verify_review_package(package) is True
    assert verify_review_package(tampered) is False

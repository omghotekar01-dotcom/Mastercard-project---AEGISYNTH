from hashlib import sha256

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


def test_review_package_rejects_out_of_range_compiler_generation_with_recomputed_fingerprint():
    package = build_review_package(AegisynthEngine(seed=42).run(generations=1))
    forged_policy = package.policy.model_copy(
        update={"policy_id": package.policy.policy_id.replace("ZD-01-", "ZD-09-", 1)}
    )
    forged_provenance = package.provenance.model_copy(update={"generation_count": 9})
    forged = package.model_copy(
        update={"policy": forged_policy, "provenance": forged_provenance}
    )
    forged = _refingerprint(forged)

    assert verify_review_package(package) is True
    assert verify_review_package(forged) is False

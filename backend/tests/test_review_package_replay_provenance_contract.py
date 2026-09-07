import hashlib

from app.artifact import _canonical_fields, build_review_package, verify_review_package
from app.engine import AegisynthEngine


def test_recomputed_fingerprint_cannot_relabel_benchmark_seed():
    """A fresh digest must not authenticate provenance that deterministic replay disproves."""
    result = AegisynthEngine(seed=42, max_fpr=0.02).run(generations=2)
    package = build_review_package(result)

    tampered_seed = package.seed + 1
    canonical = _canonical_fields(
        package_version=package.package_version,
        attack_family=package.attack_family,
        seed=tampered_seed,
        provenance=package.provenance.model_dump(mode="json"),
        policy=package.policy.model_dump(mode="json"),
        verification_notes=package.verification_notes,
        approval_status=package.approval_status,
        deployment_status=package.deployment_status,
        synthetic_only=package.synthetic_only,
        production_claim=package.production_claim,
    )
    recomputed_digest = hashlib.sha256(canonical).hexdigest()
    relabelled = package.model_copy(
        update={"seed": tampered_seed, "artifact_sha256": recomputed_digest}
    )

    assert relabelled.artifact_sha256 != package.artifact_sha256
    assert verify_review_package(package) is True
    assert verify_review_package(relabelled) is False


def test_replay_runtime_failure_fails_closed(monkeypatch):
    """A replay runtime failure must reject the artifact rather than weaken provenance checks."""
    result = AegisynthEngine(seed=42, max_fpr=0.02).run(generations=2)
    package = build_review_package(result)

    def broken_run(self, *args, **kwargs):
        raise RuntimeError("deterministic replay unavailable")

    monkeypatch.setattr(AegisynthEngine, "run", broken_run)

    assert verify_review_package(package) is False


def test_unexpected_replay_exception_fails_closed(monkeypatch):
    """Unexpected replay exceptions must also reject the artifact instead of escaping verification."""
    result = AegisynthEngine(seed=42, max_fpr=0.02).run(generations=2)
    package = build_review_package(result)

    def broken_run(self, *args, **kwargs):
        raise TypeError("unexpected replay dependency failure")

    monkeypatch.setattr(AegisynthEngine, "run", broken_run)

    assert verify_review_package(package) is False

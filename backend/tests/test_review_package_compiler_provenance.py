import hashlib

from app.artifact import _canonical_fields, build_review_package, verify_review_package
from app.engine import AegisynthEngine


def _recompute_digest(package):
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


def _valid_package():
    return build_review_package(AegisynthEngine(seed=42).run(generations=4))


def test_current_review_package_matches_declared_compiler_profile():
    package = _valid_package()

    assert verify_review_package(package) is True


def test_recomputed_digest_cannot_relabel_generation_provenance():
    tampered = _valid_package().model_copy(deep=True)
    tampered.provenance.generation_count = 3
    tampered.artifact_sha256 = _recompute_digest(tampered)

    assert verify_review_package(tampered) is False


def test_recomputed_digest_cannot_claim_off_grid_policy_came_from_compiler():
    tampered = _valid_package().model_copy(deep=True)
    tampered.policy.merchant_age_max = 49
    generation = tampered.provenance.generation_count
    tampered.policy.policy_id = (
        f"ZD-{generation:02d}-049-"
        f"{int(tampered.policy.first_time_card_ratio_min * 100):02d}-"
        f"{int(tampered.policy.settlement_change_days_max):02d}-"
        f"{int(tampered.policy.temporal_burst_score_min * 100):02d}"
    )
    tampered.artifact_sha256 = _recompute_digest(tampered)

    assert verify_review_package(tampered) is False


def test_recomputed_digest_cannot_claim_review_action_was_compiler_emitted():
    tampered = _valid_package().model_copy(deep=True)
    tampered.policy.action = "REVIEW"
    tampered.artifact_sha256 = _recompute_digest(tampered)

    assert verify_review_package(tampered) is False


def test_recomputed_digest_cannot_loosen_false_positive_budget():
    tampered = _valid_package().model_copy(deep=True)
    tampered.provenance.max_false_positive_rate = 0.20
    tampered.artifact_sha256 = _recompute_digest(tampered)

    assert verify_review_package(tampered) is False


def test_recomputed_digest_cannot_loosen_latency_budget():
    tampered = _valid_package().model_copy(deep=True)
    tampered.provenance.max_policy_latency_ms = 50.0
    tampered.artifact_sha256 = _recompute_digest(tampered)

    assert verify_review_package(tampered) is False

import hashlib

import pytest

import app.artifact as artifact_module
from app.artifact import _canonical_fields, build_review_package, verify_review_package
from app.engine import AegisynthEngine
from app.main import app
from fastapi.testclient import TestClient


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


def test_review_package_is_deterministic_for_same_result():
    result_a = AegisynthEngine(seed=42).run(generations=4)
    result_b = AegisynthEngine(seed=42).run(generations=4)
    package_a = build_review_package(result_a)
    package_b = build_review_package(result_b)

    assert package_a.artifact_sha256 == package_b.artifact_sha256
    assert len(package_a.artifact_sha256) == 64
    assert package_a.policy == package_b.policy
    assert package_a.provenance == package_b.provenance
    assert verify_review_package(package_a) is True


def test_review_package_changes_when_policy_result_changes():
    package_a = build_review_package(AegisynthEngine(seed=42).run(generations=4))
    package_b = build_review_package(AegisynthEngine(seed=43).run(generations=4))

    assert package_a.artifact_sha256 != package_b.artifact_sha256


def test_review_package_binds_compilation_provenance():
    package = build_review_package(AegisynthEngine(seed=42).run(generations=4))

    assert package.package_version == "1.2"
    assert package.provenance.compiler_id == "compact-grid-search-v1"
    assert package.provenance.verifier_id == "z3-business-guardrails-v1"
    assert package.provenance.generation_count == 4
    assert package.provenance.max_false_positive_rate == 0.02
    assert package.provenance.max_policy_latency_ms == 5.0
    assert package.policy.false_positive_rate <= package.provenance.max_false_positive_rate
    assert package.policy.estimated_latency_ms <= package.provenance.max_policy_latency_ms


def test_review_package_reverifies_policy_under_declared_budgets():
    result = AegisynthEngine(seed=42).run(generations=4)
    result.final_policy.false_positive_rate = 0.5

    with pytest.raises(ValueError, match="verified final policy"):
        build_review_package(result)


def test_review_package_rejects_stale_verification_evidence():
    result = AegisynthEngine(seed=42).run(generations=4)
    result.verification_notes = [*result.verification_notes, "stale evidence"]

    with pytest.raises(ValueError, match="evidence is stale or inconsistent"):
        build_review_package(result)


def test_review_package_refuses_z3_provenance_without_z3(monkeypatch):
    result = AegisynthEngine(seed=42).run(generations=4)
    monkeypatch.setattr(artifact_module, "HAS_Z3", False)

    with pytest.raises(RuntimeError, match="requires Z3"):
        build_review_package(result)


def test_review_package_detects_policy_tampering():
    package = build_review_package(AegisynthEngine(seed=42).run(generations=4))
    tampered = package.model_copy(deep=True)
    tampered.policy.merchant_age_max += 1

    assert verify_review_package(package) is True
    assert verify_review_package(tampered) is False


def test_review_package_detects_verification_note_tampering():
    package = build_review_package(AegisynthEngine(seed=42).run(generations=4))
    tampered = package.model_copy(deep=True)
    tampered.verification_notes = [*tampered.verification_notes, "altered"]

    assert verify_review_package(tampered) is False


def test_review_package_detects_guardrail_provenance_tampering():
    package = build_review_package(AegisynthEngine(seed=42).run(generations=4))
    tampered = package.model_copy(deep=True)
    tampered.provenance.max_false_positive_rate = 0.5

    assert verify_review_package(package) is True
    assert verify_review_package(tampered) is False


def test_review_package_detects_compiler_identity_tampering():
    package = build_review_package(AegisynthEngine(seed=42).run(generations=4))
    tampered = package.model_copy(deep=True)
    tampered.provenance.compiler_id = "unknown-compiler"

    assert verify_review_package(tampered) is False


def test_review_package_detects_governance_and_scope_tampering():
    package = build_review_package(AegisynthEngine(seed=42).run(generations=4))

    approval_tampered = package.model_copy(deep=True)
    approval_tampered.approval_status = "APPROVED"
    assert verify_review_package(approval_tampered) is False

    deployment_tampered = package.model_copy(deep=True)
    deployment_tampered.deployment_status = "CANARY"
    assert verify_review_package(deployment_tampered) is False

    scope_tampered = package.model_copy(deep=True)
    scope_tampered.synthetic_only = False
    assert verify_review_package(scope_tampered) is False

    claim_tampered = package.model_copy(deep=True)
    claim_tampered.production_claim = True
    assert verify_review_package(claim_tampered) is False


def test_review_package_rejects_unsupported_contract_even_with_recomputed_digest():
    package = build_review_package(AegisynthEngine(seed=42).run(generations=4))

    unsupported_version = package.model_copy(deep=True)
    unsupported_version.package_version = "9.9"
    unsupported_version.artifact_sha256 = _recompute_digest(unsupported_version)
    assert verify_review_package(unsupported_version) is False

    unknown_verifier = package.model_copy(deep=True)
    unknown_verifier.provenance.verifier_id = "unknown-verifier"
    unknown_verifier.artifact_sha256 = _recompute_digest(unknown_verifier)
    assert verify_review_package(unknown_verifier) is False


def test_review_package_rejects_unsafe_governance_even_with_recomputed_digest():
    package = build_review_package(AegisynthEngine(seed=42).run(generations=4))

    approved = package.model_copy(deep=True)
    approved.approval_status = "APPROVED"
    approved.artifact_sha256 = _recompute_digest(approved)
    assert verify_review_package(approved) is False

    production_claim = package.model_copy(deep=True)
    production_claim.production_claim = True
    production_claim.artifact_sha256 = _recompute_digest(production_claim)
    assert verify_review_package(production_claim) is False


def test_review_package_rejects_unsafe_policy_even_with_recomputed_digest():
    package = build_review_package(AegisynthEngine(seed=42).run(generations=4))
    tampered = package.model_copy(deep=True)
    tampered.policy.false_positive_rate = 0.5
    tampered.artifact_sha256 = _recompute_digest(tampered)

    assert verify_review_package(tampered) is False


def test_review_package_rejects_stale_evidence_even_with_recomputed_digest():
    package = build_review_package(AegisynthEngine(seed=42).run(generations=4))
    tampered = package.model_copy(deep=True)
    tampered.verification_notes = [*tampered.verification_notes, "self-consistent but stale"]
    tampered.artifact_sha256 = _recompute_digest(tampered)

    assert verify_review_package(tampered) is False


def test_review_package_rejects_unverified_policy_even_with_recomputed_digest():
    package = build_review_package(AegisynthEngine(seed=42).run(generations=4))
    tampered = package.model_copy(deep=True)
    tampered.policy.verified = False
    tampered.artifact_sha256 = _recompute_digest(tampered)

    assert verify_review_package(tampered) is False


def test_review_package_verification_fails_closed_without_z3(monkeypatch):
    package = build_review_package(AegisynthEngine(seed=42).run(generations=4))
    monkeypatch.setattr(artifact_module, "HAS_Z3", False)

    assert verify_review_package(package) is False


def test_review_package_requires_human_approval_and_starts_undeployed():
    package = build_review_package(AegisynthEngine(seed=42).run(generations=4))

    assert package.approval_status == "HUMAN_APPROVAL_REQUIRED"
    assert package.deployment_status == "NOT_DEPLOYED"
    assert package.synthetic_only is True
    assert package.production_claim is False
    assert package.policy.verified is True
    assert package.policy.action in {"STEP_UP", "REVIEW"}


def test_review_package_endpoint_matches_benchmark_contract():
    client = TestClient(app)
    response = client.get("/api/v1/review-package")

    assert response.status_code == 200
    payload = response.json()
    assert payload["seed"] == 42
    assert payload["package_version"] == "1.2"
    assert payload["approval_status"] == "HUMAN_APPROVAL_REQUIRED"
    assert payload["deployment_status"] == "NOT_DEPLOYED"
    assert payload["synthetic_only"] is True
    assert payload["production_claim"] is False
    assert payload["policy"]["verified"] is True
    assert payload["provenance"]["generation_count"] == 4
    assert payload["provenance"]["max_false_positive_rate"] == 0.02
    assert payload["provenance"]["max_policy_latency_ms"] == 5.0
    assert len(payload["artifact_sha256"]) == 64


def test_self_check_includes_governance_handoff_checks():
    client = TestClient(app)
    response = client.get("/api/v1/self-check")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "pass"
    assert payload["checks"]["human_approval_required"] is True
    assert payload["checks"]["not_auto_deployed"] is True
    assert payload["checks"]["artifact_fingerprint"] is True
    assert payload["checks"]["artifact_integrity"] is True

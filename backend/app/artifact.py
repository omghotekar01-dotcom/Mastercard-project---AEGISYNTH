from __future__ import annotations

import hashlib
import hmac
import json

from .schemas import CompilationProvenance, LabResult, ReviewPackage
from .verification import (
    DEFAULT_MAX_POLICY_LATENCY_MS,
    HAS_Z3,
    verify_policy,
)

COMPILER_ID = "compact-grid-search-v1"
VERIFIER_ID = "z3-business-guardrails-v1"
DEFAULT_MAX_FPR = 0.02
REVIEW_PACKAGE_VERSION = "1.2"
APPROVAL_STATUS = "HUMAN_APPROVAL_REQUIRED"
DEPLOYMENT_STATUS = "NOT_DEPLOYED"
SYNTHETIC_ONLY = True
PRODUCTION_CLAIM = False


def _canonical_fields(
    package_version: str,
    attack_family: str,
    seed: int,
    provenance: dict,
    policy: dict,
    verification_notes: list[str],
    approval_status: str,
    deployment_status: str,
    synthetic_only: bool,
    production_claim: bool,
) -> bytes:
    """Return stable bytes for integrity fingerprinting of a review handoff.

    Governance and scope flags are part of the protected payload so changing approval,
    deployment, synthetic-only, or production-claim state invalidates the fingerprint.
    """
    payload = {
        "package_version": package_version,
        "attack_family": attack_family,
        "seed": seed,
        "provenance": provenance,
        "policy": policy,
        "verification_notes": verification_notes,
        "approval_status": approval_status,
        "deployment_status": deployment_status,
        "synthetic_only": synthetic_only,
        "production_claim": production_claim,
    }
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def _provenance(
    result: LabResult,
    max_fpr: float,
    max_latency_ms: float,
) -> CompilationProvenance:
    return CompilationProvenance(
        compiler_id=COMPILER_ID,
        verifier_id=VERIFIER_ID,
        generation_count=len(result.iterations),
        max_false_positive_rate=max_fpr,
        max_policy_latency_ms=max_latency_ms,
    )


def _canonical_payload(
    result: LabResult,
    provenance: CompilationProvenance,
) -> bytes:
    return _canonical_fields(
        package_version=REVIEW_PACKAGE_VERSION,
        attack_family=result.attack_family,
        seed=result.seed,
        provenance=provenance.model_dump(mode="json"),
        policy=result.final_policy.model_dump(mode="json"),
        verification_notes=result.verification_notes,
        approval_status=APPROVAL_STATUS,
        deployment_status=DEPLOYMENT_STATUS,
        synthetic_only=SYNTHETIC_ONLY,
        production_claim=PRODUCTION_CLAIM,
    )


def _validate_result_for_review(
    result: LabResult,
    max_fpr: float,
    max_latency_ms: float,
) -> None:
    """Re-verify the exact final policy before creating a judge-facing handoff.

    Review-package provenance declares the Z3 verifier and explicit business budgets.
    Packaging therefore fails closed if Z3 is unavailable, if the final policy no longer
    satisfies those budgets, or if the stored verification evidence is stale/tampered.
    """
    if not HAS_Z3:
        raise RuntimeError(
            "Review package requires Z3; refusing to claim z3-business-guardrails-v1 "
            "provenance without the formal verifier"
        )

    verified, current_notes = verify_policy(
        result.final_policy,
        max_fpr=max_fpr,
        max_latency_ms=max_latency_ms,
    )
    if not verified or not result.final_policy.verified:
        raise ValueError("Review package requires a verified final policy under declared budgets")
    if result.verification_notes != current_notes:
        raise ValueError("Review package verification evidence is stale or inconsistent")


def build_review_package(
    result: LabResult,
    max_fpr: float = DEFAULT_MAX_FPR,
    max_latency_ms: float = DEFAULT_MAX_POLICY_LATENCY_MS,
) -> ReviewPackage:
    """Package a verified synthetic policy for explicit human approval.

    The SHA-256 digest is an integrity fingerprint, not a cryptographic signature.
    It binds the policy, evidence, compiler/verifier profile, safety budgets, and
    governance/scope state. Deployment remains NOT_DEPLOYED until an external
    human-governance system acts.
    """
    _validate_result_for_review(
        result,
        max_fpr=max_fpr,
        max_latency_ms=max_latency_ms,
    )
    provenance = _provenance(result, max_fpr=max_fpr, max_latency_ms=max_latency_ms)
    digest = hashlib.sha256(_canonical_payload(result, provenance)).hexdigest()
    return ReviewPackage(
        package_version=REVIEW_PACKAGE_VERSION,
        artifact_sha256=digest,
        attack_family=result.attack_family,
        seed=result.seed,
        provenance=provenance,
        policy=result.final_policy,
        verification_notes=result.verification_notes,
        approval_status=APPROVAL_STATUS,
        deployment_status=DEPLOYMENT_STATUS,
        synthetic_only=SYNTHETIC_ONLY,
        production_claim=PRODUCTION_CLAIM,
    )


def _has_supported_review_contract(package: ReviewPackage) -> bool:
    """Fail closed unless the handoff matches the currently supported safe contract."""
    return (
        package.package_version == REVIEW_PACKAGE_VERSION
        and package.provenance.compiler_id == COMPILER_ID
        and package.provenance.verifier_id == VERIFIER_ID
        and package.approval_status == APPROVAL_STATUS
        and package.deployment_status == DEPLOYMENT_STATUS
        and package.synthetic_only is SYNTHETIC_ONLY
        and package.production_claim is PRODUCTION_CLAIM
    )


def verify_review_package(package: ReviewPackage) -> bool:
    """Validate review-contract compatibility and detect protected-field modification.

    This verifies content integrity only. It does not authenticate an author and is
    deliberately not presented as a digital signature. Unsupported package versions,
    compiler/verifier identities, or unsafe governance/scope states are rejected even
    if a caller recomputes a matching digest.
    """
    if not _has_supported_review_contract(package):
        return False

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
    expected = hashlib.sha256(canonical).hexdigest()
    return hmac.compare_digest(expected, package.artifact_sha256)

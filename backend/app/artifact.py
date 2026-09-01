from __future__ import annotations

import hashlib
import hmac
import json

from .schemas import CompilationProvenance, LabResult, ReviewPackage
from .verification import DEFAULT_MAX_POLICY_LATENCY_MS

COMPILER_ID = "compact-grid-search-v1"
VERIFIER_ID = "z3-business-guardrails-v1"
DEFAULT_MAX_FPR = 0.02
REVIEW_PACKAGE_VERSION = "1.1"


def _canonical_fields(
    package_version: str,
    attack_family: str,
    seed: int,
    provenance: dict,
    policy: dict,
    verification_notes: list[str],
) -> bytes:
    """Return stable bytes for integrity fingerprinting of a review handoff."""
    payload = {
        "package_version": package_version,
        "attack_family": attack_family,
        "seed": seed,
        "provenance": provenance,
        "policy": policy,
        "verification_notes": verification_notes,
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
    )


def build_review_package(
    result: LabResult,
    max_fpr: float = DEFAULT_MAX_FPR,
    max_latency_ms: float = DEFAULT_MAX_POLICY_LATENCY_MS,
) -> ReviewPackage:
    """Package a verified synthetic policy for explicit human approval.

    The SHA-256 digest is an integrity fingerprint, not a cryptographic signature.
    It binds the policy to its compiler/verifier profile and declared safety budgets.
    Deployment remains NOT_DEPLOYED until an external human-governance system acts.
    """
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
        approval_status="HUMAN_APPROVAL_REQUIRED",
        deployment_status="NOT_DEPLOYED",
        synthetic_only=True,
        production_claim=False,
    )


def verify_review_package(package: ReviewPackage) -> bool:
    """Detect modification of policy, evidence, provenance, or declared safety budgets.

    This verifies content integrity only. It does not authenticate an author and is
    deliberately not presented as a digital signature.
    """
    canonical = _canonical_fields(
        package_version=package.package_version,
        attack_family=package.attack_family,
        seed=package.seed,
        provenance=package.provenance.model_dump(mode="json"),
        policy=package.policy.model_dump(mode="json"),
        verification_notes=package.verification_notes,
    )
    expected = hashlib.sha256(canonical).hexdigest()
    return hmac.compare_digest(expected, package.artifact_sha256)

from __future__ import annotations

import hashlib
import hmac
import json

from .schemas import LabResult, ReviewPackage


def _canonical_fields(
    attack_family: str,
    seed: int,
    policy: dict,
    verification_notes: list[str],
) -> bytes:
    """Return stable bytes for integrity fingerprinting of a review handoff."""
    payload = {
        "attack_family": attack_family,
        "seed": seed,
        "policy": policy,
        "verification_notes": verification_notes,
    }
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def _canonical_payload(result: LabResult) -> bytes:
    return _canonical_fields(
        attack_family=result.attack_family,
        seed=result.seed,
        policy=result.final_policy.model_dump(mode="json"),
        verification_notes=result.verification_notes,
    )


def build_review_package(result: LabResult) -> ReviewPackage:
    """Package a verified synthetic policy for explicit human approval.

    The SHA-256 digest is an integrity fingerprint, not a cryptographic signature.
    Deployment remains NOT_DEPLOYED until an external human-governance system acts.
    """
    digest = hashlib.sha256(_canonical_payload(result)).hexdigest()
    return ReviewPackage(
        artifact_sha256=digest,
        attack_family=result.attack_family,
        seed=result.seed,
        policy=result.final_policy,
        verification_notes=result.verification_notes,
        approval_status="HUMAN_APPROVAL_REQUIRED",
        deployment_status="NOT_DEPLOYED",
        synthetic_only=True,
        production_claim=False,
    )


def verify_review_package(package: ReviewPackage) -> bool:
    """Detect accidental or malicious modification of a review package.

    This verifies content integrity only. It does not authenticate an author and is
    deliberately not presented as a digital signature.
    """
    canonical = _canonical_fields(
        attack_family=package.attack_family,
        seed=package.seed,
        policy=package.policy.model_dump(mode="json"),
        verification_notes=package.verification_notes,
    )
    expected = hashlib.sha256(canonical).hexdigest()
    return hmac.compare_digest(expected, package.artifact_sha256)

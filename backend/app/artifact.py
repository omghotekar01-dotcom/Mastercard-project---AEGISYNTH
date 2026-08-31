from __future__ import annotations

import hashlib
import json

from .schemas import LabResult, ReviewPackage


def _canonical_payload(result: LabResult) -> bytes:
    """Return stable bytes for integrity fingerprinting of a compiled result."""
    payload = {
        "attack_family": result.attack_family,
        "seed": result.seed,
        "policy": result.final_policy.model_dump(mode="json"),
        "verification_notes": result.verification_notes,
    }
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


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

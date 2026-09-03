from __future__ import annotations

from decimal import Decimal
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
_METRIC_PRECISION = 4
_METRIC_ULP = Decimal("0.0001")
_COMPILER_AGE_GRID = {48, 72, 96, 120, 168, 240}
_COMPILER_CARD_GRID = {0.50, 0.58, 0.64, 0.70, 0.76}
_COMPILER_SETTLEMENT_GRID = {7, 14, 21, 30, 45}
_COMPILER_BURST_GRID = {0.50, 0.58, 0.64, 0.70, 0.76}
_COMPILER_ACTION = "STEP_UP"
_COMPILER_LATENCY_MS = 0.35


def _metric_delta(observed: float, expected: float) -> Decimal:
    """Compare reported decimal metrics without binary-float boundary ambiguity."""
    return abs(Decimal(str(observed)) - Decimal(str(expected)))


def _percent_code(value: float) -> int:
    """Encode compiler percentage thresholds identically to policy ID generation."""
    return int(Decimal(str(value)) * 100)


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


def _validate_result_consistency(result: LabResult) -> None:
    """Bind judge-facing summary claims to the exact final synthesis iteration.

    A final policy can independently pass formal/business verification while surrounding
    LabResult metrics are stale or internally inconsistent. Refuse packaging unless the
    iteration history, final policy, and summary metrics describe the same run state.
    """
    if not result.iterations:
        raise ValueError("Review package requires at least one synthesis iteration")

    expected_iterations = list(range(1, len(result.iterations) + 1))
    observed_iterations = [item.iteration for item in result.iterations]
    if observed_iterations != expected_iterations:
        raise ValueError("Review package iteration history must be contiguous and ordered")

    final_iteration = result.iterations[-1]
    if result.final_policy != final_iteration.candidate:
        raise ValueError("Review package final policy does not match the final synthesis iteration")
    if result.final_attack_success_rate != final_iteration.attack_success_rate:
        raise ValueError("Review package final attack-success rate is inconsistent with the final iteration")

    observed_metrics = result.metrics.model_dump(mode="python")
    expected_reduction = round(
        result.baseline_attack_success_rate - result.final_attack_success_rate,
        _METRIC_PRECISION,
    )
    # baseline_attack_success_rate is itself serialized at four decimals while the engine
    # computes the reduction from the pre-rounded baseline. Reconstructing from the public
    # LabResult can therefore differ by at most one unit in the last reported decimal.
    # Decimal comparison makes the inclusive 0.0001 boundary deterministic across runtimes.
    if _metric_delta(observed_metrics["attack_success_reduction"], expected_reduction) > _METRIC_ULP:
        raise ValueError("Review package summary metrics are inconsistent with the final policy/run")

    expected_exact_metrics = {
        "final_fraud_coverage": result.final_policy.fraud_coverage,
        "final_false_positive_rate": result.final_policy.false_positive_rate,
        "estimated_policy_latency_ms": result.final_policy.estimated_latency_ms,
        "benign_acceptance_rate": round(
            1 - result.final_policy.false_positive_rate, _METRIC_PRECISION
        ),
    }
    if any(observed_metrics[name] != value for name, value in expected_exact_metrics.items()):
        raise ValueError("Review package summary metrics are inconsistent with the final policy/run")


def _require_supported_review_budgets(max_fpr: float, max_latency_ms: float) -> None:
    """Prevent the builder from emitting a package the pinned review contract rejects."""
    if max_fpr != DEFAULT_MAX_FPR or max_latency_ms != DEFAULT_MAX_POLICY_LATENCY_MS:
        raise ValueError(
            "Review package contract requires the pinned business budgets: "
            f"max_fpr={DEFAULT_MAX_FPR} and "
            f"max_latency_ms={DEFAULT_MAX_POLICY_LATENCY_MS}"
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
    _validate_result_consistency(result)

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
    _require_supported_review_budgets(max_fpr=max_fpr, max_latency_ms=max_latency_ms)
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


def _matches_compiler_profile(package: ReviewPackage) -> bool:
    """Bind claimed compiler provenance to the exact policy shape this compiler can emit.

    The artifact digest is not authentication, so a caller able to recompute it must not be
    able to relabel an arbitrary Z3-safe policy as output of compact-grid-search-v1. Require
    the final generation, threshold grids, action, latency, and semantic policy ID to match
    the compiler profile used by this package contract.
    """
    policy = package.policy
    generation = package.provenance.generation_count
    expected_policy_id = (
        f"ZD-{generation:02d}-{int(policy.merchant_age_max):03d}-"
        f"{_percent_code(policy.first_time_card_ratio_min):02d}-"
        f"{int(policy.settlement_change_days_max):02d}-"
        f"{_percent_code(policy.temporal_burst_score_min):02d}"
    )
    return (
        policy.merchant_age_max in _COMPILER_AGE_GRID
        and policy.first_time_card_ratio_min in _COMPILER_CARD_GRID
        and policy.settlement_change_days_max in _COMPILER_SETTLEMENT_GRID
        and policy.temporal_burst_score_min in _COMPILER_BURST_GRID
        and policy.action == _COMPILER_ACTION
        and policy.estimated_latency_ms == _COMPILER_LATENCY_MS
        and policy.policy_id == expected_policy_id
    )


def _has_supported_review_contract(package: ReviewPackage) -> bool:
    """Fail closed unless the handoff matches the currently supported safe contract."""
    return (
        package.package_version == REVIEW_PACKAGE_VERSION
        and package.provenance.compiler_id == COMPILER_ID
        and package.provenance.verifier_id == VERIFIER_ID
        and package.provenance.max_false_positive_rate == DEFAULT_MAX_FPR
        and package.provenance.max_policy_latency_ms == DEFAULT_MAX_POLICY_LATENCY_MS
        and package.approval_status == APPROVAL_STATUS
        and package.deployment_status == DEPLOYMENT_STATUS
        and package.synthetic_only is SYNTHETIC_ONLY
        and package.production_claim is PRODUCTION_CLAIM
        and _matches_compiler_profile(package)
    )


def _has_current_semantic_evidence(package: ReviewPackage) -> bool:
    """Re-run declared business/formal checks instead of trusting a recomputed digest.

    SHA-256 detects accidental or uncoordinated modification, but it is not an author
    signature: a caller that changes protected fields can also recompute the fingerprint.
    The review verifier therefore independently re-evaluates the exact policy against the
    budgets recorded in provenance and requires the stored notes to match fresh verifier
    output. Because the declared verifier identity is Z3-specific, absence of Z3 fails closed.
    """
    if not HAS_Z3 or not package.policy.verified:
        return False
    verified, current_notes = verify_policy(
        package.policy,
        max_fpr=package.provenance.max_false_positive_rate,
        max_latency_ms=package.provenance.max_policy_latency_ms,
    )
    return verified and package.verification_notes == current_notes


def verify_review_package(package: ReviewPackage) -> bool:
    """Validate contract, protected-field integrity, and current semantic evidence.

    The fingerprint is intentionally not treated as authentication. Even when a caller can
    recompute SHA-256 after modifying an artifact, the exact policy must still pass the
    declared Z3/business guardrails and reproduce the stored verification evidence.
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
    if not hmac.compare_digest(expected, package.artifact_sha256):
        return False
    return _has_current_semantic_evidence(package)

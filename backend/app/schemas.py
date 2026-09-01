from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Action = Literal["PASS", "STEP_UP", "REVIEW"]
ApprovalStatus = Literal["HUMAN_APPROVAL_REQUIRED", "APPROVED", "REJECTED"]
DeploymentStatus = Literal["NOT_DEPLOYED", "CANARY", "ROLLED_BACK"]


class Transaction(BaseModel):
    """Synthetic transaction features used by the defensive laboratory."""

    tx_id: str = Field(min_length=1, max_length=64)
    amount: float = Field(ge=0)
    merchant_age_hours: float = Field(ge=0)
    first_time_card_ratio: float = Field(ge=0, le=1)
    settlement_change_days: float = Field(ge=0)
    temporal_burst_score: float = Field(ge=0, le=1)
    device_entropy: float = Field(ge=0, le=1)
    geo_velocity: float = Field(ge=0)
    label: int = Field(ge=0, le=1)
    attack_family: str = Field(default="benign", min_length=1, max_length=64)


class Policy(BaseModel):
    """Compact human-reviewable policy emitted by the defence compiler."""

    policy_id: str = Field(min_length=1, max_length=80)
    merchant_age_max: float = Field(ge=0, le=24 * 365 * 20)
    first_time_card_ratio_min: float = Field(ge=0, le=1)
    settlement_change_days_max: float = Field(ge=0, le=3650)
    temporal_burst_score_min: float = Field(ge=0, le=1)
    action: Action = "STEP_UP"
    fraud_coverage: float = Field(default=0.0, ge=0, le=1)
    false_positive_rate: float = Field(default=0.0, ge=0, le=1)
    estimated_latency_ms: float = Field(default=0.0, ge=0)
    counterexamples_remaining: int = Field(default=0, ge=0)
    verified: bool = False
    explanation: str = Field(default="", max_length=1000)


class CounterexampleTrace(BaseModel):
    """Audit-friendly summary of escaped synthetic variants for one generation."""

    training_attack_count: int = Field(ge=1)
    redteam_attack_count: int = Field(ge=1)
    escaped_count: int = Field(ge=0)
    escaped_rate: float = Field(ge=0, le=1)
    sample_tx_ids: list[str] = Field(default_factory=list, max_length=5)


class IterationResult(BaseModel):
    iteration: int = Field(ge=1)
    candidate: Policy
    counterexamples: int = Field(ge=0)
    attack_success_rate: float = Field(ge=0, le=1)
    trace: CounterexampleTrace


class LabMetrics(BaseModel):
    attack_success_reduction: float = Field(ge=-1, le=1)
    final_fraud_coverage: float = Field(ge=0, le=1)
    final_false_positive_rate: float = Field(ge=0, le=1)
    estimated_policy_latency_ms: float = Field(ge=0)
    benign_acceptance_rate: float = Field(ge=0, le=1)


class LabResult(BaseModel):
    attack_family: str = Field(min_length=1, max_length=64)
    seed: int = Field(ge=0)
    baseline_attack_success_rate: float = Field(ge=0, le=1)
    final_attack_success_rate: float = Field(ge=0, le=1)
    iterations: list[IterationResult]
    final_policy: Policy
    verification_notes: list[str]
    metrics: LabMetrics


class CompilationProvenance(BaseModel):
    """Deterministic metadata describing how a review artifact was produced."""

    compiler_id: str = Field(min_length=1, max_length=80)
    verifier_id: str = Field(min_length=1, max_length=80)
    generation_count: int = Field(ge=1, le=8)
    max_false_positive_rate: float = Field(ge=0, le=1)
    max_policy_latency_ms: float = Field(gt=0)


class ReviewPackage(BaseModel):
    """Immutable review handoff generated after synthesis and verification."""

    package_version: str = "1.1"
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    attack_family: str = Field(min_length=1, max_length=64)
    seed: int = Field(ge=0)
    provenance: CompilationProvenance
    policy: Policy
    verification_notes: list[str]
    approval_status: ApprovalStatus = "HUMAN_APPROVAL_REQUIRED"
    deployment_status: DeploymentStatus = "NOT_DEPLOYED"
    synthetic_only: bool = True
    production_claim: bool = False

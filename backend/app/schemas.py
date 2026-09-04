from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, StrictBool, field_validator, model_validator

Action = Literal["PASS", "STEP_UP", "REVIEW"]
ApprovalStatus = Literal["HUMAN_APPROVAL_REQUIRED", "APPROVED", "REJECTED"]
DeploymentStatus = Literal["NOT_DEPLOYED", "CANARY", "ROLLED_BACK"]


def _reject_boolean_numeric_input(value: object) -> object:
    """Prevent bool-as-number coercion at safety-critical schema boundaries."""
    if isinstance(value, bool):
        raise ValueError("boolean values are not valid numeric evidence")
    return value


class Transaction(BaseModel):
    """Synthetic transaction features used by the defensive laboratory."""

    tx_id: str = Field(min_length=1, max_length=64)
    amount: float = Field(ge=0, allow_inf_nan=False)
    merchant_age_hours: float = Field(ge=0, allow_inf_nan=False)
    first_time_card_ratio: float = Field(ge=0, le=1, allow_inf_nan=False)
    settlement_change_days: float = Field(ge=0, allow_inf_nan=False)
    temporal_burst_score: float = Field(ge=0, le=1, allow_inf_nan=False)
    device_entropy: float = Field(ge=0, le=1, allow_inf_nan=False)
    geo_velocity: float = Field(ge=0, allow_inf_nan=False)
    label: int = Field(ge=0, le=1, strict=True)
    attack_family: str = Field(default="benign", min_length=1, max_length=64)

    @field_validator(
        "amount",
        "merchant_age_hours",
        "first_time_card_ratio",
        "settlement_change_days",
        "temporal_burst_score",
        "device_entropy",
        "geo_velocity",
        mode="before",
    )
    @classmethod
    def reject_boolean_numeric_features(cls, value: object) -> object:
        return _reject_boolean_numeric_input(value)


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
    estimated_latency_ms: float = Field(default=0.0, ge=0, allow_inf_nan=False)
    counterexamples_remaining: int = Field(default=0, ge=0, strict=True)
    verified: StrictBool = False
    explanation: str = Field(default="", max_length=1000)

    @field_validator("policy_id")
    @classmethod
    def require_canonical_policy_id(cls, value: str) -> str:
        """Keep policy identity canonical before it reaches provenance or verification."""
        if value != value.strip():
            raise ValueError("policy_id must not contain surrounding whitespace")
        return value

    @field_validator(
        "merchant_age_max",
        "first_time_card_ratio_min",
        "settlement_change_days_max",
        "temporal_burst_score_min",
        "fraud_coverage",
        "false_positive_rate",
        "estimated_latency_ms",
        mode="before",
    )
    @classmethod
    def reject_boolean_numeric_fields(cls, value: object) -> object:
        return _reject_boolean_numeric_input(value)


class CounterexampleTrace(BaseModel):
    """Audit-friendly summary of escaped synthetic variants for one generation."""

    training_attack_count: int = Field(ge=1, strict=True)
    redteam_attack_count: int = Field(ge=1, strict=True)
    escaped_count: int = Field(ge=0, strict=True)
    escaped_rate: float = Field(ge=0, le=1)
    sample_tx_ids: list[str] = Field(default_factory=list, max_length=5)

    @field_validator("escaped_rate", mode="before")
    @classmethod
    def reject_boolean_escaped_rate(cls, value: object) -> object:
        return _reject_boolean_numeric_input(value)

    @field_validator("sample_tx_ids")
    @classmethod
    def require_valid_sample_identities(cls, value: list[str]) -> list[str]:
        if any(not tx_id.strip() or len(tx_id) > 64 for tx_id in value):
            raise ValueError("sample_tx_ids must contain non-blank transaction IDs of at most 64 characters")
        if len(set(value)) != len(value):
            raise ValueError("sample_tx_ids must not contain duplicate transaction IDs")
        return value

    @model_validator(mode="after")
    def require_consistent_escape_evidence(self) -> "CounterexampleTrace":
        if self.escaped_count > self.redteam_attack_count:
            raise ValueError("escaped_count cannot exceed redteam_attack_count")
        expected_rate = round(self.escaped_count / self.redteam_attack_count, 4)
        if self.escaped_rate != expected_rate:
            raise ValueError("escaped_rate must equal escaped_count / redteam_attack_count rounded to 4 decimals")
        if len(self.sample_tx_ids) > self.escaped_count:
            raise ValueError("sample_tx_ids cannot contain more entries than escaped_count")
        return self


class IterationResult(BaseModel):
    iteration: int = Field(ge=1, strict=True)
    candidate: Policy
    counterexamples: int = Field(ge=0, strict=True)
    attack_success_rate: float = Field(ge=0, le=1)
    trace: CounterexampleTrace

    @field_validator("attack_success_rate", mode="before")
    @classmethod
    def reject_boolean_attack_success_rate(cls, value: object) -> object:
        return _reject_boolean_numeric_input(value)

    @model_validator(mode="after")
    def require_trace_counterexample_consistency(self) -> "IterationResult":
        if self.counterexamples != self.trace.escaped_count:
            raise ValueError("counterexamples must equal trace.escaped_count")
        if self.candidate.counterexamples_remaining != self.counterexamples:
            raise ValueError("candidate.counterexamples_remaining must equal counterexamples")
        return self


class LabMetrics(BaseModel):
    attack_success_reduction: float = Field(ge=-1, le=1)
    final_fraud_coverage: float = Field(ge=0, le=1)
    final_false_positive_rate: float = Field(ge=0, le=1)
    estimated_policy_latency_ms: float = Field(ge=0, allow_inf_nan=False)
    benign_acceptance_rate: float = Field(ge=0, le=1)

    @field_validator(
        "attack_success_reduction",
        "final_fraud_coverage",
        "final_false_positive_rate",
        "estimated_policy_latency_ms",
        "benign_acceptance_rate",
        mode="before",
    )
    @classmethod
    def reject_boolean_metric_fields(cls, value: object) -> object:
        return _reject_boolean_numeric_input(value)


class LabResult(BaseModel):
    attack_family: str = Field(min_length=1, max_length=64)
    seed: int = Field(ge=0, strict=True)
    baseline_attack_success_rate: float = Field(ge=0, le=1)
    final_attack_success_rate: float = Field(ge=0, le=1)
    iterations: list[IterationResult]
    final_policy: Policy
    verification_notes: list[str]
    metrics: LabMetrics

    @field_validator(
        "baseline_attack_success_rate",
        "final_attack_success_rate",
        mode="before",
    )
    @classmethod
    def reject_boolean_result_rates(cls, value: object) -> object:
        return _reject_boolean_numeric_input(value)

    @model_validator(mode="after")
    def require_consistent_final_evidence(self) -> "LabResult":
        if not self.iterations:
            raise ValueError("iterations must contain at least one result")
        expected_iterations = list(range(1, len(self.iterations) + 1))
        observed_iterations = [item.iteration for item in self.iterations]
        if observed_iterations != expected_iterations:
            raise ValueError("iterations must be contiguous and ordered starting at 1")
        last = self.iterations[-1]
        if self.final_policy != last.candidate:
            raise ValueError("final_policy must equal the last iteration candidate")
        if self.final_attack_success_rate != last.attack_success_rate:
            raise ValueError("final_attack_success_rate must equal the last iteration attack_success_rate")
        if self.metrics.final_fraud_coverage != self.final_policy.fraud_coverage:
            raise ValueError("metrics.final_fraud_coverage must equal final_policy.fraud_coverage")
        if self.metrics.final_false_positive_rate != self.final_policy.false_positive_rate:
            raise ValueError("metrics.final_false_positive_rate must equal final_policy.false_positive_rate")
        if self.metrics.estimated_policy_latency_ms != self.final_policy.estimated_latency_ms:
            raise ValueError("metrics.estimated_policy_latency_ms must equal final_policy.estimated_latency_ms")
        expected_reduction = round(self.baseline_attack_success_rate - self.final_attack_success_rate, 4)
        if self.metrics.attack_success_reduction != expected_reduction:
            raise ValueError("metrics.attack_success_reduction must equal baseline minus final attack success rate")
        expected_acceptance = round(1 - self.final_policy.false_positive_rate, 4)
        if self.metrics.benign_acceptance_rate != expected_acceptance:
            raise ValueError("metrics.benign_acceptance_rate must equal one minus final false positive rate")
        return self


class CompilationProvenance(BaseModel):
    """Deterministic metadata describing how a review artifact was produced."""

    compiler_id: str = Field(min_length=1, max_length=80)
    verifier_id: str = Field(min_length=1, max_length=80)
    generation_count: int = Field(ge=1, le=8, strict=True)
    max_false_positive_rate: float = Field(ge=0, le=1)
    max_policy_latency_ms: float = Field(gt=0, allow_inf_nan=False)

    @field_validator(
        "max_false_positive_rate",
        "max_policy_latency_ms",
        mode="before",
    )
    @classmethod
    def reject_boolean_budget_fields(cls, value: object) -> object:
        return _reject_boolean_numeric_input(value)


class ReviewPackage(BaseModel):
    """Immutable review handoff generated after synthesis and verification."""

    package_version: Literal["1.2"] = "1.2"
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    attack_family: str = Field(min_length=1, max_length=64)
    seed: int = Field(ge=0, strict=True)
    provenance: CompilationProvenance
    policy: Policy
    verification_notes: list[str]
    approval_status: Literal["HUMAN_APPROVAL_REQUIRED"] = "HUMAN_APPROVAL_REQUIRED"
    deployment_status: Literal["NOT_DEPLOYED"] = "NOT_DEPLOYED"
    synthetic_only: Literal[True] = True
    production_claim: Literal[False] = False

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal

Action = Literal["PASS", "STEP_UP", "REVIEW"]

class Transaction(BaseModel):
    tx_id: str
    amount: float = Field(ge=0)
    merchant_age_hours: float = Field(ge=0)
    first_time_card_ratio: float = Field(ge=0, le=1)
    settlement_change_days: float = Field(ge=0)
    temporal_burst_score: float = Field(ge=0, le=1)
    device_entropy: float = Field(ge=0, le=1)
    geo_velocity: float = Field(ge=0)
    label: int = Field(ge=0, le=1)
    attack_family: str = "benign"

class Policy(BaseModel):
    policy_id: str
    merchant_age_max: float
    first_time_card_ratio_min: float
    settlement_change_days_max: float
    temporal_burst_score_min: float
    action: Action = "STEP_UP"
    fraud_coverage: float = 0.0
    false_positive_rate: float = 0.0
    estimated_latency_ms: float = 0.0
    counterexamples_remaining: int = 0
    verified: bool = False
    explanation: str = ""

class IterationResult(BaseModel):
    iteration: int
    candidate: Policy
    counterexamples: int
    attack_success_rate: float

class LabResult(BaseModel):
    attack_family: str
    seed: int
    baseline_attack_success_rate: float
    final_attack_success_rate: float
    iterations: list[IterationResult]
    final_policy: Policy
    verification_notes: list[str]
    metrics: dict[str, float]

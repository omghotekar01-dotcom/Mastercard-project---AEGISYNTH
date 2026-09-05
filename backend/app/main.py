from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .artifact import build_review_package, verify_review_package
from .engine import AegisynthEngine
from .schemas import LabResult, Policy, ReviewPackage
from .verification import HAS_Z3, verify_policy

APP_VERSION = "1.4.0"
BENCHMARK_SEED = 42
BENCHMARK_GENERATIONS = 4
ATTACK_FAMILY = "ghost_merchant_swarm"
BENCHMARK_CONTRACT = {
    "baseline_attack_success_rate": 0.5383,
    "final_attack_success_rate": 0.0743,
    "final_fraud_coverage": 0.9257,
    "benign_acceptance_rate": 0.9943,
}

app = FastAPI(
    title="AEGISYNTH API",
    version=APP_VERSION,
    description="Autonomous Payment Defence Compiler - safe synthetic red-team/blue-team lab.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent / "static"


def _benchmark() -> LabResult:
    return AegisynthEngine(seed=BENCHMARK_SEED).run(
        generations=BENCHMARK_GENERATIONS,
        attack_family=ATTACK_FAMILY,
    )


def _formal_verifier_operational() -> bool:
    """Exercise the real verifier, not merely the Z3 import path, for runtime readiness."""
    if not HAS_Z3:
        return False
    canary = Policy(
        policy_id="readiness-canary",
        merchant_age_max=720.0,
        first_time_card_ratio_min=0.5,
        settlement_change_days_max=30.0,
        temporal_burst_score_min=0.5,
        action="STEP_UP",
        fraud_coverage=0.9,
        false_positive_rate=0.01,
        estimated_latency_ms=1.0,
        counterexamples_remaining=0,
    )
    ok, _notes = verify_policy(canary)
    return ok


@app.get("/health")
def health():
    """Liveness only: confirms the API process is running."""
    return {"status": "ok", "service": "aegisynth", "version": APP_VERSION}


@app.get("/ready")
def ready(response: Response):
    """Fail-closed readiness gate for capabilities promised by the demo."""
    verifier_operational = _formal_verifier_operational()
    checks = {
        "dashboard_present": (STATIC_DIR / "index.html").exists(),
        "z3_formal_verifier_available": HAS_Z3,
        "z3_formal_verifier_operational": verifier_operational,
    }
    is_ready = all(checks.values())
    if not is_ready:
        response.status_code = 503
    return {
        "status": "ready" if is_ready else "not_ready",
        "service": "aegisynth",
        "version": APP_VERSION,
        "checks": checks,
        "formal_verifier": "z3" if verifier_operational else "unavailable",
        "scope": "synthetic defensive payment-security laboratory",
    }


@app.get("/api/v1/meta")
def meta():
    return {
        "name": "AEGISYNTH",
        "version": APP_VERSION,
        "attack_family": ATTACK_FAMILY,
        "benchmark_seed": BENCHMARK_SEED,
        "benchmark_generations": BENCHMARK_GENERATIONS,
        "responsible_actions": ["STEP_UP", "REVIEW"],
        "production_claim": False,
        "scope": "synthetic prototype; not production traffic",
    }


@app.get("/api/v1/demo", response_model=LabResult)
def run_reproducible_demo():
    return _benchmark()


@app.get("/api/v1/review-package", response_model=ReviewPackage)
def review_package():
    return build_review_package(_benchmark())


@app.get("/api/v1/self-check")
def self_check(response: Response):
    """Return a non-success status when any runtime contract check fails."""
    result = _benchmark()
    package = build_review_package(result)
    verifier_operational = _formal_verifier_operational()
    checks = {
        "benchmark_seed": result.seed == BENCHMARK_SEED,
        "attack_family": result.attack_family == ATTACK_FAMILY,
        "generation_count": len(result.iterations) == BENCHMARK_GENERATIONS,
        "baseline_attack_success": result.baseline_attack_success_rate == BENCHMARK_CONTRACT["baseline_attack_success_rate"],
        "final_attack_success": result.final_attack_success_rate == BENCHMARK_CONTRACT["final_attack_success_rate"],
        "fraud_coverage": result.metrics.final_fraud_coverage == BENCHMARK_CONTRACT["final_fraud_coverage"],
        "benign_acceptance": result.metrics.benign_acceptance_rate == BENCHMARK_CONTRACT["benign_acceptance_rate"],
        "policy_verified": result.final_policy.verified is True,
        "responsible_action": result.final_policy.action in {"STEP_UP", "REVIEW"},
        "false_positive_budget": result.final_policy.false_positive_rate <= 0.02,
        "human_approval_required": package.approval_status == "HUMAN_APPROVAL_REQUIRED",
        "not_auto_deployed": package.deployment_status == "NOT_DEPLOYED",
        "artifact_seed": package.seed == BENCHMARK_SEED,
        "artifact_attack_family": package.attack_family == ATTACK_FAMILY,
        "artifact_generation_count": package.provenance.generation_count == BENCHMARK_GENERATIONS,
        "artifact_fingerprint": len(package.artifact_sha256) == 64,
        "artifact_integrity": verify_review_package(package),
        "dashboard_present": (STATIC_DIR / "index.html").exists(),
        "z3_formal_verifier_available": HAS_Z3,
        "z3_formal_verifier_operational": verifier_operational,
    }
    checks_pass = all(checks.values())
    if not checks_pass:
        response.status_code = 503
    return {
        "status": "pass" if checks_pass else "fail",
        "version": APP_VERSION,
        "checks": checks,
        "scope": "synthetic prototype runtime self-check",
    }


@app.get("/api/v1/lab/run", response_model=LabResult)
def run_lab(
    seed: int = Query(42, ge=0, le=10_000_000),
    generations: int = Query(4, ge=1, le=8),
):
    return AegisynthEngine(seed=seed).run(
        generations=generations,
        attack_family=ATTACK_FAMILY,
    )


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="dashboard")
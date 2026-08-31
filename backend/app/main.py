from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .engine import AegisynthEngine
from .schemas import LabResult
from .verification import HAS_Z3

APP_VERSION = "1.1.0"
BENCHMARK_SEED = 42
BENCHMARK_GENERATIONS = 4
ATTACK_FAMILY = "ghost_merchant_swarm"

app = FastAPI(
    title="AEGISYNTH API",
    version=APP_VERSION,
    description=(
        "Autonomous Payment Defence Compiler - safe synthetic red-team/blue-team lab. "
        "The public demo is defensive-only and uses no real payment credentials or customer data."
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "aegisynth",
        "version": APP_VERSION,
    }


@app.get("/ready")
def ready():
    return {
        "status": "ready",
        "service": "aegisynth",
        "version": APP_VERSION,
        "dashboard": (STATIC_DIR / "index.html").exists(),
        "formal_verifier": "z3" if HAS_Z3 else "domain-fallback",
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
        "scope": "synthetic prototype; not Mastercard production traffic",
    }


@app.get("/api/v1/demo", response_model=LabResult)
def run_reproducible_demo():
    """Run the exact deterministic scenario referenced in the public benchmark."""
    return AegisynthEngine(seed=BENCHMARK_SEED).run(
        generations=BENCHMARK_GENERATIONS,
        attack_family=ATTACK_FAMILY,
    )


@app.get("/api/v1/lab/run", response_model=LabResult)
def run_lab(
    seed: int = Query(42, ge=0, le=10_000_000),
    generations: int = Query(4, ge=1, le=8),
):
    """Run a new deterministic synthetic scenario for the supplied seed."""
    return AegisynthEngine(seed=seed).run(
        generations=generations,
        attack_family=ATTACK_FAMILY,
    )


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="dashboard")

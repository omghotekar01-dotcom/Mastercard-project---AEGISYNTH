from __future__ import annotations
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from .engine import AegisynthEngine
from .schemas import LabResult

app = FastAPI(
    title="AEGISYNTH API",
    version="1.0.0",
    description="Autonomous Payment Defence Compiler - safe synthetic red-team/blue-team lab.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "service": "aegisynth", "version": "1.0.0"}

@app.get("/api/v1/lab/run", response_model=LabResult)
def run_lab(
    seed: int = Query(42, ge=0, le=10_000_000),
    generations: int = Query(4, ge=1, le=8),
):
    return AegisynthEngine(seed=seed).run(generations=generations)

from __future__ import annotations

import json
import math
from pathlib import Path

from app.engine import AegisynthEngine
from app.simulator import SUPPORTED_ATTACK_FAMILIES


BENCHMARK_PATH = Path(__file__).resolve().parents[2] / "submission" / "benchmark_seed42.json"
EXPECTED_KEYS = {
    "scope",
    "seed",
    "generations",
    "attack_family",
    "baseline_attack_success_rate",
    "final_attack_success_rate",
    "final_fraud_family_coverage",
    "final_false_positive_rate",
    "benign_acceptance_rate",
    "notes",
}
RATE_KEYS = (
    "baseline_attack_success_rate",
    "final_attack_success_rate",
    "final_fraud_family_coverage",
    "final_false_positive_rate",
    "benign_acceptance_rate",
)


def _load_claim() -> dict[str, object]:
    return json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))


def test_submitted_benchmark_artifact_has_closed_claim_surface() -> None:
    claim = _load_claim()

    assert set(claim) == EXPECTED_KEYS
    assert claim["scope"] == "synthetic prototype benchmark; not Mastercard production traffic"
    assert isinstance(claim["notes"], str)
    assert "need not be monotonic" in claim["notes"]

    seed = claim["seed"]
    generations = claim["generations"]
    attack_family = claim["attack_family"]
    assert type(seed) is int and seed >= 0
    assert type(generations) is int and 1 <= generations <= 8
    assert isinstance(attack_family, str) and attack_family in SUPPORTED_ATTACK_FAMILIES

    for key in RATE_KEYS:
        value = claim[key]
        assert not isinstance(value, bool) and isinstance(value, (int, float))
        assert math.isfinite(value) and 0 <= value <= 1
        assert value == round(value, 4)


def test_submitted_benchmark_claims_are_internally_consistent() -> None:
    claim = _load_claim()

    assert claim["final_attack_success_rate"] == round(
        1 - claim["final_fraud_family_coverage"], 4
    )
    assert claim["benign_acceptance_rate"] == round(
        1 - claim["final_false_positive_rate"], 4
    )
    assert claim["baseline_attack_success_rate"] >= claim["final_attack_success_rate"]


def test_submitted_benchmark_claims_reproduce_from_engine() -> None:
    claim = _load_claim()
    result = AegisynthEngine(seed=claim["seed"]).run(generations=claim["generations"])

    assert result.seed == claim["seed"]
    assert result.attack_family == claim["attack_family"]
    assert result.baseline_attack_success_rate == claim["baseline_attack_success_rate"]
    assert result.final_attack_success_rate == claim["final_attack_success_rate"]
    assert result.metrics.final_fraud_coverage == claim["final_fraud_family_coverage"]
    assert result.metrics.final_false_positive_rate == claim["final_false_positive_rate"]
    assert result.metrics.benign_acceptance_rate == claim["benign_acceptance_rate"]
    assert result.final_policy.verified is True
    assert result.final_policy.action in {"STEP_UP", "REVIEW"}

import json
from pathlib import Path

from app.main import ATTACK_FAMILY, BENCHMARK_CONTRACT, BENCHMARK_GENERATIONS, BENCHMARK_SEED


SUBMITTED_BENCHMARK = Path(__file__).resolve().parents[2] / "submission" / "benchmark_seed42.json"


def test_runtime_benchmark_contract_matches_submitted_artifact():
    expected = json.loads(SUBMITTED_BENCHMARK.read_text(encoding="utf-8"))

    assert BENCHMARK_SEED == expected["seed"]
    assert BENCHMARK_GENERATIONS == expected["generations"]
    assert ATTACK_FAMILY == expected["attack_family"]
    assert BENCHMARK_CONTRACT == {
        "baseline_attack_success_rate": expected["baseline_attack_success_rate"],
        "final_attack_success_rate": expected["final_attack_success_rate"],
        "final_fraud_coverage": expected["final_fraud_family_coverage"],
        "benign_acceptance_rate": expected["benign_acceptance_rate"],
    }

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
README_PATH = REPO_ROOT / "README.md"
BENCHMARK_PATH = REPO_ROOT / "submission" / "benchmark_seed42.json"


def _percent(value: float) -> str:
    return f"{value:.2%}"


def test_readme_benchmark_claims_match_submitted_artifact():
    readme = README_PATH.read_text(encoding="utf-8")
    benchmark = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))

    assert f"Synthetic prototype benchmark — seed {benchmark['seed']}" in readme
    assert f"`{benchmark['attack_family']}` attack family" in readme
    assert (
        f"| Attack success before defence | **{_percent(benchmark['baseline_attack_success_rate'])}** |"
        in readme
    )
    assert (
        f"| Attack success after compilation | **{_percent(benchmark['final_attack_success_rate'])}** |"
        in readme
    )
    assert (
        f"| Attack-family coverage | **{_percent(benchmark['final_fraud_family_coverage'])}** |"
        in readme
    )
    assert (
        f"| Benign acceptance | **{_percent(benchmark['benign_acceptance_rate'])}** |"
        in readme
    )
    assert "synthetic prototype results" in readme.lower()
    assert "not Mastercard production claims" in readme

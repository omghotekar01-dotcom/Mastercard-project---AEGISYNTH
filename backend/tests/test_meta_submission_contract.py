import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
SUBMITTED_BENCHMARK = (
    Path(__file__).resolve().parents[2] / "submission" / "benchmark_seed42.json"
)


def test_meta_contract_matches_submitted_benchmark_scenario():
    """Keep the judge-facing runtime metadata bound to the submitted replay scenario."""
    expected = json.loads(SUBMITTED_BENCHMARK.read_text(encoding="utf-8"))

    response = client.get("/api/v1/meta")

    assert response.status_code == 200
    meta = response.json()
    assert meta["benchmark_seed"] == expected["seed"]
    assert meta["benchmark_generations"] == expected["generations"]
    assert meta["attack_family"] == expected["attack_family"]
    assert meta["production_claim"] is False
    assert "not production traffic" in meta["scope"]
    assert set(meta["responsible_actions"]) == {"STEP_UP", "REVIEW"}

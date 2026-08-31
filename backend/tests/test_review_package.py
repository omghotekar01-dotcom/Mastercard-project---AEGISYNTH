from app.artifact import build_review_package
from app.engine import AegisynthEngine
from app.main import app
from fastapi.testclient import TestClient


def test_review_package_is_deterministic_for_same_result():
    result_a = AegisynthEngine(seed=42).run(generations=4)
    result_b = AegisynthEngine(seed=42).run(generations=4)
    package_a = build_review_package(result_a)
    package_b = build_review_package(result_b)

    assert package_a.artifact_sha256 == package_b.artifact_sha256
    assert len(package_a.artifact_sha256) == 64
    assert package_a.policy == package_b.policy


def test_review_package_changes_when_policy_result_changes():
    package_a = build_review_package(AegisynthEngine(seed=42).run(generations=4))
    package_b = build_review_package(AegisynthEngine(seed=43).run(generations=4))

    assert package_a.artifact_sha256 != package_b.artifact_sha256


def test_review_package_requires_human_approval_and_starts_undeployed():
    package = build_review_package(AegisynthEngine(seed=42).run(generations=4))

    assert package.approval_status == "HUMAN_APPROVAL_REQUIRED"
    assert package.deployment_status == "NOT_DEPLOYED"
    assert package.synthetic_only is True
    assert package.production_claim is False
    assert package.policy.verified is True
    assert package.policy.action in {"STEP_UP", "REVIEW"}


def test_review_package_endpoint_matches_benchmark_contract():
    client = TestClient(app)
    response = client.get("/api/v1/review-package")

    assert response.status_code == 200
    payload = response.json()
    assert payload["seed"] == 42
    assert payload["approval_status"] == "HUMAN_APPROVAL_REQUIRED"
    assert payload["deployment_status"] == "NOT_DEPLOYED"
    assert payload["policy"]["verified"] is True
    assert len(payload["artifact_sha256"]) == 64


def test_self_check_includes_governance_handoff_checks():
    client = TestClient(app)
    response = client.get("/api/v1/self-check")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "pass"
    assert payload["checks"]["human_approval_required"] is True
    assert payload["checks"]["not_auto_deployed"] is True
    assert payload["checks"]["artifact_fingerprint"] is True

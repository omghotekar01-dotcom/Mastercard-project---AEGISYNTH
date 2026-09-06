from app.artifact import build_review_package
from app.engine import AegisynthEngine


def test_same_seed_reproduces_full_lab_result_and_review_fingerprint():
    """A pinned seed must reproduce both benchmark evidence and the judge-facing handoff."""
    first_result = AegisynthEngine(seed=42).run(generations=1)
    second_result = AegisynthEngine(seed=42).run(generations=1)

    assert first_result.model_dump(mode="json") == second_result.model_dump(mode="json")

    first_package = build_review_package(first_result)
    second_package = build_review_package(second_result)

    assert first_package.model_dump(mode="json") == second_package.model_dump(mode="json")
    assert first_package.artifact_sha256 == second_package.artifact_sha256

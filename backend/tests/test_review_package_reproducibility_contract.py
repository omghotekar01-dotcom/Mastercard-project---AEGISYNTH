from app.artifact import build_review_package, verify_review_package
from app.engine import AegisynthEngine


def test_review_package_is_reproducible_for_identical_lab_evidence():
    """Identical verified lab evidence must produce the exact same judge-facing handoff."""
    result = AegisynthEngine(seed=42, max_fpr=0.02).run(generations=2)

    first = build_review_package(result)
    second = build_review_package(result)

    assert first.artifact_sha256 == second.artifact_sha256
    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    assert verify_review_package(first) is True
    assert verify_review_package(second) is True

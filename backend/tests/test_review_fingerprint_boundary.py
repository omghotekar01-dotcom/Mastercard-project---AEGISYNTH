import pytest

from app.artifact import build_review_package, verify_review_package
from app.engine import AegisynthEngine


@pytest.mark.parametrize(
    "malformed_digest",
    [
        None,
        123,
        "",
        "0" * 63,
        "0" * 65,
        "g" * 64,
        "A" * 64,
    ],
)
def test_review_verifier_fails_closed_on_schema_bypassed_fingerprint(malformed_digest) -> None:
    package = build_review_package(AegisynthEngine(seed=42).run(generations=4))
    tampered = package.model_copy(update={"artifact_sha256": malformed_digest})

    assert verify_review_package(tampered) is False


def test_review_verifier_accepts_canonical_generated_fingerprint() -> None:
    package = build_review_package(AegisynthEngine(seed=42).run(generations=4))

    assert len(package.artifact_sha256) == 64
    assert package.artifact_sha256 == package.artifact_sha256.lower()
    assert verify_review_package(package) is True

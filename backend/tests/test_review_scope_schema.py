import pytest
from pydantic import ValidationError

from app.artifact import build_review_package
from app.engine import AegisynthEngine
from app.schemas import ReviewPackage


def _review_payload() -> dict:
    package = build_review_package(AegisynthEngine(seed=42).run(generations=4))
    return package.model_dump(mode="json")


@pytest.mark.parametrize(
    ("field", "unsafe_value"),
    [
        ("synthetic_only", False),
        ("production_claim", True),
    ],
)
def test_review_package_rejects_unsafe_scope_flags_at_schema_boundary(field, unsafe_value):
    payload = _review_payload()
    payload[field] = unsafe_value

    with pytest.raises(ValidationError):
        ReviewPackage(**payload)

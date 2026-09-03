import pytest
from pydantic import ValidationError

from app.artifact import build_review_package
from app.engine import AegisynthEngine
from app.schemas import ReviewPackage


def _package_payload() -> dict:
    return build_review_package(AegisynthEngine(seed=42).run(generations=2)).model_dump()


def test_review_package_schema_accepts_current_safe_contract():
    package = ReviewPackage.model_validate(_package_payload())

    assert package.package_version == "1.2"
    assert package.approval_status == "HUMAN_APPROVAL_REQUIRED"
    assert package.deployment_status == "NOT_DEPLOYED"


@pytest.mark.parametrize("package_version", ["1.1", "9.9", "latest"])
def test_review_package_schema_rejects_unsupported_contract_versions(package_version):
    payload = _package_payload()
    payload["package_version"] = package_version

    with pytest.raises(ValidationError):
        ReviewPackage.model_validate(payload)


@pytest.mark.parametrize("approval_status", ["APPROVED", "REJECTED"])
def test_review_package_schema_rejects_terminal_approval_states(approval_status):
    payload = _package_payload()
    payload["approval_status"] = approval_status

    with pytest.raises(ValidationError):
        ReviewPackage.model_validate(payload)


@pytest.mark.parametrize("deployment_status", ["CANARY", "ROLLED_BACK"])
def test_review_package_schema_rejects_deployment_states(deployment_status):
    payload = _package_payload()
    payload["deployment_status"] = deployment_status

    with pytest.raises(ValidationError):
        ReviewPackage.model_validate(payload)

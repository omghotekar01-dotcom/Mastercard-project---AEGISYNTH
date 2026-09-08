import pytest
from pydantic import ValidationError

from app.schemas import ReviewPackage


def _review_package_payload() -> dict:
    return {
        "artifact_sha256": "0" * 64,
        "attack_family": "ghost_merchant_swarm",
        "seed": 42,
        "provenance": {
            "compiler_id": "AEGISYNTH-compiler",
            "verifier_id": "AEGISYNTH-verifier",
            "generation_count": 4,
            "max_false_positive_rate": 0.02,
            "max_policy_latency_ms": 5.0,
        },
        "policy": {
            "policy_id": "external-review-policy",
            "merchant_age_max": 96,
            "first_time_card_ratio_min": 0.64,
            "settlement_change_days_max": 21,
            "temporal_burst_score_min": 0.64,
            "action": "STEP_UP",
            "verified": True,
        },
        "verification_notes": ["Z3 and business-budget checks passed."],
    }


def test_review_package_requires_at_least_one_verification_note() -> None:
    payload = _review_package_payload()
    payload["verification_notes"] = []

    with pytest.raises(ValidationError, match="List should have at least 1 item"):
        ReviewPackage.model_validate(payload)


@pytest.mark.parametrize("note", ["", "   ", "\t\n"])
def test_review_package_rejects_blank_verification_notes(note: str) -> None:
    payload = _review_package_payload()
    payload["verification_notes"] = [note]

    with pytest.raises(
        ValidationError,
        match="verification_notes must contain only non-empty evidence strings",
    ):
        ReviewPackage.model_validate(payload)

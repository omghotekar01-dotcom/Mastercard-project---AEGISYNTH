from __future__ import annotations

import pytest

from app.artifact import build_review_package, verify_review_package
from app.engine import AegisynthEngine


@pytest.fixture(scope="module")
def review_package():
    result = AegisynthEngine(seed=42).run(
        generations=4,
        attack_family="ghost_merchant_swarm",
    )
    return build_review_package(result)


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("merchant_age_max", float("nan")),
        ("merchant_age_max", float("inf")),
        ("merchant_age_max", float("-inf")),
        ("first_time_card_ratio_min", float("nan")),
        ("first_time_card_ratio_min", float("inf")),
        ("first_time_card_ratio_min", float("-inf")),
        ("settlement_change_days_max", float("nan")),
        ("settlement_change_days_max", float("inf")),
        ("settlement_change_days_max", float("-inf")),
        ("temporal_burst_score_min", float("nan")),
        ("temporal_burst_score_min", float("inf")),
        ("temporal_burst_score_min", float("-inf")),
    ],
)
def test_review_verifier_rejects_schema_bypassed_nonfinite_compiler_thresholds(
    review_package,
    field: str,
    invalid_value: float,
):
    tampered_policy = review_package.policy.model_copy(update={field: invalid_value})
    tampered_package = review_package.model_copy(update={"policy": tampered_policy})

    assert verify_review_package(tampered_package) is False

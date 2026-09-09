import math

import pytest

from app.contracts import (
    POLICY_FIRST_TIME_CARD_RATIO_MAX,
    POLICY_FIRST_TIME_CARD_RATIO_MIN,
    POLICY_MERCHANT_AGE_HOURS_MAX,
    POLICY_MERCHANT_AGE_HOURS_MIN,
    POLICY_SETTLEMENT_CHANGE_DAYS_MAX,
    POLICY_SETTLEMENT_CHANGE_DAYS_MIN,
    POLICY_TEMPORAL_BURST_SCORE_MAX,
    POLICY_TEMPORAL_BURST_SCORE_MIN,
)
from app.schemas import Policy
from app.verification import _validate_policy_numeric_fields


FEATURE_DOMAINS = (
    ("merchant_age_max", POLICY_MERCHANT_AGE_HOURS_MIN, POLICY_MERCHANT_AGE_HOURS_MAX),
    (
        "first_time_card_ratio_min",
        POLICY_FIRST_TIME_CARD_RATIO_MIN,
        POLICY_FIRST_TIME_CARD_RATIO_MAX,
    ),
    (
        "settlement_change_days_max",
        POLICY_SETTLEMENT_CHANGE_DAYS_MIN,
        POLICY_SETTLEMENT_CHANGE_DAYS_MAX,
    ),
    (
        "temporal_burst_score_min",
        POLICY_TEMPORAL_BURST_SCORE_MIN,
        POLICY_TEMPORAL_BURST_SCORE_MAX,
    ),
)


def _schema_constraint(field_name: str, attribute: str) -> float:
    values = [
        getattr(metadata, attribute)
        for metadata in Policy.model_fields[field_name].metadata
        if getattr(metadata, attribute, None) is not None
    ]
    assert len(values) == 1
    return float(values[0])


def _policy_with(**overrides: float) -> Policy:
    values = {
        "policy_id": "domain-contract-test",
        "merchant_age_max": 24.0,
        "first_time_card_ratio_min": 0.5,
        "settlement_change_days_max": 7.0,
        "temporal_burst_score_min": 0.5,
        "action": "STEP_UP",
        "fraud_coverage": 0.9,
        "false_positive_rate": 0.01,
        "estimated_latency_ms": 1.0,
        "counterexamples_remaining": 0,
        "verified": True,
    }
    values.update(overrides)
    return Policy.model_construct(**values)


@pytest.mark.parametrize(("field_name", "lower", "upper"), FEATURE_DOMAINS)
def test_schema_policy_feature_domains_match_shared_contract(
    field_name: str,
    lower: float,
    upper: float,
) -> None:
    assert _schema_constraint(field_name, "ge") == lower
    assert _schema_constraint(field_name, "le") == upper


@pytest.mark.parametrize(("field_name", "lower", "upper"), FEATURE_DOMAINS)
def test_verifier_accepts_shared_domain_boundaries(
    field_name: str,
    lower: float,
    upper: float,
) -> None:
    for boundary in (lower, upper):
        ok, notes = _validate_policy_numeric_fields(_policy_with(**{field_name: boundary}))
        assert ok is True
        assert notes == []


@pytest.mark.parametrize(("field_name", "lower", "upper"), FEATURE_DOMAINS)
def test_verifier_rejects_values_just_outside_shared_domain(
    field_name: str,
    lower: float,
    upper: float,
) -> None:
    below = math.nextafter(lower, -math.inf)
    above = math.nextafter(upper, math.inf)

    for invalid in (below, above):
        ok, notes = _validate_policy_numeric_fields(_policy_with(**{field_name: invalid}))
        assert ok is False
        assert notes == [
            f"Policy numeric field invalid: {field_name} must be finite and within [{lower:g}, {upper:g}]"
        ]

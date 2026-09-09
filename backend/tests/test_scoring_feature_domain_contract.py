import math
from types import SimpleNamespace

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
from app.policy import _validate_policy_definition, _validate_policy_features
from app.schemas import Policy


FEATURE_DOMAINS = (
    (
        "merchant_age_max",
        "merchant_age_hours",
        POLICY_MERCHANT_AGE_HOURS_MIN,
        POLICY_MERCHANT_AGE_HOURS_MAX,
    ),
    (
        "first_time_card_ratio_min",
        "first_time_card_ratio",
        POLICY_FIRST_TIME_CARD_RATIO_MIN,
        POLICY_FIRST_TIME_CARD_RATIO_MAX,
    ),
    (
        "settlement_change_days_max",
        "settlement_change_days",
        POLICY_SETTLEMENT_CHANGE_DAYS_MIN,
        POLICY_SETTLEMENT_CHANGE_DAYS_MAX,
    ),
    (
        "temporal_burst_score_min",
        "temporal_burst_score",
        POLICY_TEMPORAL_BURST_SCORE_MIN,
        POLICY_TEMPORAL_BURST_SCORE_MAX,
    ),
)


def _policy_with(**overrides: float) -> Policy:
    values = {
        "policy_id": "scoring-domain-contract",
        "merchant_age_max": 24.0,
        "first_time_card_ratio_min": 0.5,
        "settlement_change_days_max": 7.0,
        "temporal_burst_score_min": 0.5,
        "action": "STEP_UP",
        "estimated_latency_ms": 1.0,
    }
    values.update(overrides)
    return Policy.model_construct(**values)


def _transaction_with(**overrides: float) -> SimpleNamespace:
    values = {
        "tx_id": "scoring-domain-tx",
        "merchant_age_hours": 24.0,
        "first_time_card_ratio": 0.5,
        "settlement_change_days": 7.0,
        "temporal_burst_score": 0.5,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.mark.parametrize(
    ("policy_field", "transaction_field", "lower", "upper"),
    FEATURE_DOMAINS,
)
def test_scoring_accepts_shared_feature_domain_boundaries(
    policy_field: str,
    transaction_field: str,
    lower: float,
    upper: float,
) -> None:
    for boundary in (lower, upper):
        _validate_policy_definition(_policy_with(**{policy_field: boundary}))
        _validate_policy_features(
            _transaction_with(**{transaction_field: boundary}),
            "contract",
        )


@pytest.mark.parametrize(
    ("policy_field", "transaction_field", "lower", "upper"),
    FEATURE_DOMAINS,
)
def test_scoring_rejects_values_just_outside_shared_feature_domain(
    policy_field: str,
    transaction_field: str,
    lower: float,
    upper: float,
) -> None:
    for invalid in (math.nextafter(lower, -math.inf), math.nextafter(upper, math.inf)):
        with pytest.raises(
            ValueError,
            match=rf"scored policy has out-of-range {policy_field}; expected \\[{lower:g}, {upper:g}\\]",
        ):
            _validate_policy_definition(_policy_with(**{policy_field: invalid}))

        with pytest.raises(
            ValueError,
            match=rf"contract transaction 'scoring-domain-tx' has out-of-range {transaction_field}; expected \\[{lower:g}, {upper:g}\\]",
        ):
            _validate_policy_features(
                _transaction_with(**{transaction_field: invalid}),
                "contract",
            )

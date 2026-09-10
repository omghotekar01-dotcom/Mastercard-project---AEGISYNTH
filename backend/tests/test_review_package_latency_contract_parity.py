import inspect

import pytest

from app.artifact import _require_supported_review_budgets, build_review_package
from app.contracts import DEFAULT_MAX_FALSE_POSITIVE_RATE, DEFAULT_MAX_POLICY_LATENCY_MS


def test_review_package_latency_budget_matches_shared_safety_contract():
    assert DEFAULT_MAX_POLICY_LATENCY_MS == 5.0
    assert (
        inspect.signature(build_review_package).parameters["max_latency_ms"].default
        == DEFAULT_MAX_POLICY_LATENCY_MS
    )


def test_review_package_rejects_looser_latency_budget():
    with pytest.raises(ValueError, match="pinned business budgets"):
        _require_supported_review_budgets(
            max_fpr=DEFAULT_MAX_FALSE_POSITIVE_RATE,
            max_latency_ms=DEFAULT_MAX_POLICY_LATENCY_MS + 0.01,
        )

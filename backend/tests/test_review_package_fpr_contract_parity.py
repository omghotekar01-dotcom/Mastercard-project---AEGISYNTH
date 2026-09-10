import inspect

import pytest

from app.artifact import (
    DEFAULT_MAX_FPR,
    _require_supported_review_budgets,
    build_review_package,
)
from app.contracts import (
    DEFAULT_MAX_FALSE_POSITIVE_RATE,
    DEFAULT_MAX_POLICY_LATENCY_MS,
)


def test_review_package_fpr_budget_matches_shared_safety_contract():
    assert DEFAULT_MAX_FALSE_POSITIVE_RATE == 0.02
    assert DEFAULT_MAX_FPR == DEFAULT_MAX_FALSE_POSITIVE_RATE
    assert (
        inspect.signature(build_review_package).parameters["max_fpr"].default
        == DEFAULT_MAX_FALSE_POSITIVE_RATE
    )


def test_review_package_rejects_looser_fpr_budget():
    with pytest.raises(ValueError, match="pinned business budgets"):
        _require_supported_review_budgets(
            max_fpr=DEFAULT_MAX_FALSE_POSITIVE_RATE + 0.0001,
            max_latency_ms=DEFAULT_MAX_POLICY_LATENCY_MS,
        )

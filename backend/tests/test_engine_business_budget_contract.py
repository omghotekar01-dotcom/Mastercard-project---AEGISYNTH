import math

import pytest

from app.engine import AegisynthEngine


@pytest.mark.parametrize(
    "invalid_budget",
    [True, False, -0.0001, 1.0001, math.nan, math.inf, -math.inf, "0.02", None],
)
def test_engine_constructor_fails_closed_on_invalid_false_positive_budget(invalid_budget):
    """Reject invalid business budgets before an engine instance can enter the benchmark lifecycle."""
    with pytest.raises(ValueError, match="max_fpr"):
        AegisynthEngine(seed=42, max_fpr=invalid_budget)


def test_engine_revalidates_false_positive_budget_after_live_mutation():
    """A mutated engine budget must be rejected before it can authorize a synthesized policy."""
    engine = AegisynthEngine(seed=42, max_fpr=0.02)
    engine.max_fpr = math.nan

    with pytest.raises(ValueError, match="max_fpr"):
        engine.run(generations=1)

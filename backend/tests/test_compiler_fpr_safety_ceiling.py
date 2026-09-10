import pytest

from app.contracts import DEFAULT_MAX_FALSE_POSITIVE_RATE
from app.policy import DefenceCompiler


def test_compiler_rejects_budget_above_shared_fpr_safety_ceiling():
    with pytest.raises(ValueError, match=r"max_fpr must be finite and within \[0, 0\.02\]"):
        DefenceCompiler(max_fpr=DEFAULT_MAX_FALSE_POSITIVE_RATE + 0.0001)


def test_compiler_allows_stricter_budget_than_shared_fpr_safety_ceiling():
    compiler = DefenceCompiler(max_fpr=0.01)

    assert compiler.max_fpr == 0.01


def test_compiler_revalidates_mutated_budget_before_synthesis():
    compiler = DefenceCompiler()
    compiler.max_fpr = DEFAULT_MAX_FALSE_POSITIVE_RATE + 0.0001

    with pytest.raises(ValueError, match=r"max_fpr must be finite and within \[0, 0\.02\]"):
        compiler.synthesize([], [], generation=1)

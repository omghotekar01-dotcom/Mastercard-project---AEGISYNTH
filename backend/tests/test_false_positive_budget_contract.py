import inspect

from app.contracts import DEFAULT_MAX_FALSE_POSITIVE_RATE
from app.policy import DefenceCompiler
from app.verification import verify_policy


def test_default_false_positive_budget_is_identical_across_compiler_and_verifier():
    compiler_default = inspect.signature(DefenceCompiler).parameters["max_fpr"].default
    verifier_default = inspect.signature(verify_policy).parameters["max_fpr"].default

    assert DEFAULT_MAX_FALSE_POSITIVE_RATE == 0.02
    assert compiler_default == DEFAULT_MAX_FALSE_POSITIVE_RATE
    assert verifier_default == DEFAULT_MAX_FALSE_POSITIVE_RATE


def test_default_false_positive_budget_stays_inside_probability_domain():
    assert 0.0 <= DEFAULT_MAX_FALSE_POSITIVE_RATE <= 1.0

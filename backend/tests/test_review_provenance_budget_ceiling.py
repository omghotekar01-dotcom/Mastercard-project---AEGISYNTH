import pytest
from pydantic import ValidationError

from app.contracts import (
    DEFAULT_MAX_FALSE_POSITIVE_RATE,
    DEFAULT_MAX_POLICY_LATENCY_MS,
)
from app.schemas import CompilationProvenance


def _provenance(**overrides):
    values = {
        "compiler_id": "AEGISYNTH-Compiler",
        "verifier_id": "AEGISYNTH-Z3",
        "generation_count": 4,
        "max_false_positive_rate": DEFAULT_MAX_FALSE_POSITIVE_RATE,
        "max_policy_latency_ms": DEFAULT_MAX_POLICY_LATENCY_MS,
    }
    values.update(overrides)
    return CompilationProvenance(**values)


def test_review_provenance_accepts_shared_business_ceiling():
    provenance = _provenance()
    assert provenance.max_false_positive_rate == DEFAULT_MAX_FALSE_POSITIVE_RATE
    assert provenance.max_policy_latency_ms == DEFAULT_MAX_POLICY_LATENCY_MS


@pytest.mark.parametrize(
    "field,value",
    [
        ("max_false_positive_rate", DEFAULT_MAX_FALSE_POSITIVE_RATE + 0.0001),
        ("max_policy_latency_ms", DEFAULT_MAX_POLICY_LATENCY_MS + 0.01),
    ],
)
def test_review_provenance_rejects_relaxed_business_budget(field, value):
    with pytest.raises(ValidationError):
        _provenance(**{field: value})

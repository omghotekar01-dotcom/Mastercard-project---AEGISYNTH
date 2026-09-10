from app import policy as policy_module
from app.contracts import DEFAULT_MAX_POLICY_LATENCY_MS


def test_compiler_estimated_latency_stays_within_shared_runtime_budget():
    """Compiler-emitted latency evidence must remain admissible under runtime verification."""
    assert isinstance(policy_module._COMPILER_ESTIMATED_LATENCY_MS, (int, float))
    assert not isinstance(policy_module._COMPILER_ESTIMATED_LATENCY_MS, bool)
    assert 0 <= policy_module._COMPILER_ESTIMATED_LATENCY_MS <= DEFAULT_MAX_POLICY_LATENCY_MS

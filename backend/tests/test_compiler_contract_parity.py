from app import policy as policy_module
from app import verification as verification_module


def test_compiler_provenance_contract_is_shared_across_scoring_and_verification():
    """Keep compiler search, scoring provenance, and Z3 provenance on one contract."""
    assert frozenset(policy_module._COMPILER_AGE_GRID) == verification_module._COMPILER_AGE_CODES
    assert (
        frozenset(policy_module._COMPILER_CARD_PERCENT_CODES)
        == verification_module._COMPILER_CARD_PERCENT_CODES
    )
    assert (
        frozenset(policy_module._COMPILER_SETTLEMENT_GRID)
        == verification_module._COMPILER_SETTLEMENT_CODES
    )
    assert (
        frozenset(policy_module._COMPILER_BURST_PERCENT_CODES)
        == verification_module._COMPILER_BURST_PERCENT_CODES
    )
    assert (
        policy_module._COMPILER_ESTIMATED_LATENCY_MS
        == verification_module._COMPILER_ESTIMATED_LATENCY_MS
    )

from app import artifact as artifact_module
from app import policy as policy_module
from app import verification as verification_module


def test_compiler_provenance_contract_is_shared_across_scoring_verification_and_review():
    """Keep compiler search, Z3 provenance, and judge review provenance on one contract."""
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

    assert frozenset(policy_module._COMPILER_AGE_GRID) == frozenset(artifact_module._COMPILER_AGE_GRID)
    assert frozenset(policy_module._COMPILER_CARD_GRID) == frozenset(artifact_module._COMPILER_CARD_GRID)
    assert frozenset(policy_module._COMPILER_SETTLEMENT_GRID) == frozenset(
        artifact_module._COMPILER_SETTLEMENT_GRID
    )
    assert frozenset(policy_module._COMPILER_BURST_GRID) == frozenset(
        artifact_module._COMPILER_BURST_GRID
    )
    assert policy_module._COMPILER_ESTIMATED_LATENCY_MS == artifact_module._COMPILER_LATENCY_MS

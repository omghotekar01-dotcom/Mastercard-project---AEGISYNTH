import pytest

from app.engine import AegisynthEngine
from app.policy import _validate_compiler_identity_binding as validate_scoring_identity
from app.schemas import Policy
from app.verification import _validate_compiler_identity_binding as validate_verifier_identity


def _compiled_policy(generation: int) -> Policy:
    return Policy(
        policy_id=f"ZD-{generation:02d}-048-50-07-50",
        merchant_age_max=48,
        first_time_card_ratio_min=0.50,
        settlement_change_days_max=7,
        temporal_burst_score_min=0.50,
        action="STEP_UP",
        fraud_coverage=0.90,
        false_positive_rate=0.01,
        estimated_latency_ms=0.35,
    )


@pytest.mark.parametrize("generation", [1, 8])
def test_supported_generation_domain_is_accepted_at_all_contract_boundaries(generation):
    policy = _compiled_policy(generation)

    assert AegisynthEngine._validate_generations(generation) == generation
    validate_scoring_identity(policy)
    assert validate_verifier_identity(policy) == (True, [])


@pytest.mark.parametrize("generation", [0, 9, 99])
def test_out_of_domain_generation_is_rejected_at_all_contract_boundaries(generation):
    policy = _compiled_policy(generation)

    with pytest.raises(ValueError, match=r"generations must be an integer within \[1, 8\]"):
        AegisynthEngine._validate_generations(generation)

    with pytest.raises(
        ValueError,
        match=r"scored compiler policy generation must be within \[1, 8\]",
    ):
        validate_scoring_identity(policy)

    assert validate_verifier_identity(policy) == (
        False,
        ["Compiler policy identity invalid: generation must be within [1, 8]"],
    )

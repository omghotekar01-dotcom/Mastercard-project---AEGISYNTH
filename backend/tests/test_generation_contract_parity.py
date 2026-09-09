import pytest

from app.contracts import COMPILER_GENERATION_MAX, COMPILER_GENERATION_MIN
from app.engine import AegisynthEngine
from app.policy import _validate_compiler_identity_binding as validate_scoring_identity
from app.schemas import CompilationProvenance, Policy
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


def _provenance(generation: int) -> CompilationProvenance:
    return CompilationProvenance(
        compiler_id="aegisynth-defence-compiler-v1",
        verifier_id="aegisynth-z3-verifier-v1",
        generation_count=generation,
        max_false_positive_rate=0.02,
        max_policy_latency_ms=5.0,
    )


@pytest.mark.parametrize("generation", [COMPILER_GENERATION_MIN, COMPILER_GENERATION_MAX])
def test_supported_generation_domain_is_accepted_at_all_contract_boundaries(generation):
    policy = _compiled_policy(generation)

    assert AegisynthEngine._validate_generations(generation) == generation
    validate_scoring_identity(policy)
    assert validate_verifier_identity(policy) == (True, [])
    assert _provenance(generation).generation_count == generation


@pytest.mark.parametrize(
    "generation",
    [COMPILER_GENERATION_MIN - 1, COMPILER_GENERATION_MAX + 1, 99],
)
def test_out_of_domain_generation_is_rejected_at_all_contract_boundaries(generation):
    policy = _compiled_policy(generation)
    domain = rf"\[{COMPILER_GENERATION_MIN}, {COMPILER_GENERATION_MAX}\]"

    with pytest.raises(ValueError, match=rf"generations must be an integer within {domain}"):
        AegisynthEngine._validate_generations(generation)

    with pytest.raises(
        ValueError,
        match=rf"scored compiler policy generation must be within {domain}",
    ):
        validate_scoring_identity(policy)

    assert validate_verifier_identity(policy) == (
        False,
        [
            "Compiler policy identity invalid: generation must be within "
            f"[{COMPILER_GENERATION_MIN}, {COMPILER_GENERATION_MAX}]"
        ],
    )

    with pytest.raises(ValueError):
        _provenance(generation)


def test_generation_contract_rejects_boolean_schema_bypass_values():
    with pytest.raises(ValueError):
        AegisynthEngine._validate_generations(True)

    with pytest.raises(ValueError):
        _provenance(True)

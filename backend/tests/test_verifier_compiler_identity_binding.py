import pytest

from app.schemas import Policy
from app.verification import verify_policy


def _compiled_policy() -> Policy:
    return Policy(
        policy_id="ZD-01-048-50-07-50",
        merchant_age_max=48,
        first_time_card_ratio_min=0.50,
        settlement_change_days_max=7,
        temporal_burst_score_min=0.50,
        action="STEP_UP",
        fraud_coverage=0.90,
        false_positive_rate=0.01,
        estimated_latency_ms=0.35,
    )


def test_verifier_accepts_compiler_identity_when_encoded_semantics_match():
    verified, notes = verify_policy(_compiled_policy())

    assert verified is True
    assert any("Z3:" in note for note in notes)


@pytest.mark.parametrize(
    ("field", "tampered_value"),
    [
        ("merchant_age_max", 72),
        ("first_time_card_ratio_min", 0.58),
        ("settlement_change_days_max", 14),
        ("temporal_burst_score_min", 0.58),
    ],
)
def test_verifier_rejects_mutated_thresholds_under_stale_compiler_identity(field, tampered_value):
    policy = _compiled_policy().model_copy(update={field: tampered_value})

    verified, notes = verify_policy(policy)

    assert verified is False
    assert notes == [
        "Compiler policy identity mismatch: ZD policy_id does not encode the verified thresholds"
    ]


def test_verifier_rejects_malformed_identity_that_claims_compiler_lineage():
    policy = _compiled_policy().model_copy(update={"policy_id": "ZD-01-48-50-07-50"})

    verified, notes = verify_policy(policy)

    assert verified is False
    assert notes == ["Compiler policy identity invalid: malformed ZD policy_id"]


def test_verifier_rejects_out_of_range_generation_encoded_in_compiler_identity():
    policy = _compiled_policy().model_copy(update={"policy_id": "ZD-09-048-50-07-50"})

    verified, notes = verify_policy(policy)

    assert verified is False
    assert notes == ["Compiler policy identity invalid: generation must be within [1, 8]"]

import pytest
from pydantic import ValidationError

from app.schemas import CompilationProvenance, CounterexampleTrace, Policy, Transaction


def _transaction(tx_id: str) -> Transaction:
    return Transaction(
        tx_id=tx_id,
        amount=100.0,
        merchant_age_hours=24.0,
        first_time_card_ratio=0.25,
        settlement_change_days=30.0,
        temporal_burst_score=0.20,
        device_entropy=0.50,
        geo_velocity=10.0,
        label=0,
        attack_family="benign",
    )


def _policy(policy_id: str) -> Policy:
    return Policy(
        policy_id=policy_id,
        merchant_age_max=48,
        first_time_card_ratio_min=0.50,
        settlement_change_days_max=7,
        temporal_burst_score_min=0.50,
        action="STEP_UP",
        estimated_latency_ms=0.35,
    )


def _provenance(**updates) -> CompilationProvenance:
    values = {
        "compiler_id": "compact-grid-search-v1",
        "verifier_id": "z3-business-guardrails-v1",
        "generation_count": 1,
        "max_false_positive_rate": 0.02,
        "max_policy_latency_ms": 1.0,
    }
    values.update(updates)
    return CompilationProvenance(**values)


@pytest.mark.parametrize("bad_id", ["tx-💳", "tx/001", "tx:001", "tx@001", "é-tx-1"])
def test_transaction_schema_rejects_noncanonical_identity_characters(bad_id):
    with pytest.raises(ValidationError, match="tx_id may contain only ASCII letters"):
        _transaction(bad_id)


@pytest.mark.parametrize("bad_id", ["policy-💳", "policy/001", "policy:001", "policy@001", "é-policy-1"])
def test_policy_schema_rejects_noncanonical_identity_characters(bad_id):
    with pytest.raises(ValidationError, match="policy_id may contain only ASCII letters"):
        _policy(bad_id)


@pytest.mark.parametrize("field_name", ["compiler_id", "verifier_id"])
@pytest.mark.parametrize("bad_id", ["tool-💳", "tool/001", "tool:001", "tool@001", "é-tool-1"])
def test_provenance_schema_rejects_noncanonical_tool_identity_characters(field_name, bad_id):
    with pytest.raises(ValidationError, match=f"{field_name} may contain only ASCII letters"):
        _provenance(**{field_name: bad_id})


@pytest.mark.parametrize("field_name", ["compiler_id", "verifier_id"])
def test_provenance_schema_rejects_punctuation_only_tool_identity(field_name):
    with pytest.raises(ValidationError, match=f"{field_name} must contain at least one ASCII letter or digit"):
        _provenance(**{field_name: "._-"})


def test_counterexample_trace_rejects_noncanonical_sample_identity():
    with pytest.raises(ValidationError, match="canonical ASCII transaction IDs"):
        CounterexampleTrace(
            training_attack_count=1,
            redteam_attack_count=1,
            escaped_count=1,
            escaped_rate=1.0,
            sample_tx_ids=["attack-💳"],
        )


def test_schema_accepts_existing_canonical_identity_shape():
    assert _transaction("B-000001").tx_id == "B-000001"
    assert _policy("ZD-01-048-50-07-50").policy_id == "ZD-01-048-50-07-50"
    provenance = _provenance()
    assert provenance.compiler_id == "compact-grid-search-v1"
    assert provenance.verifier_id == "z3-business-guardrails-v1"

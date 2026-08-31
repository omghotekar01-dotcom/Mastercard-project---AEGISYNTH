import pytest
from pydantic import ValidationError

from app.engine import AegisynthEngine
from app.policy import DefenceCompiler, matches
from app.schemas import Policy
from app.simulator import PaymentWorld
from app.verification import DEFAULT_MAX_POLICY_LATENCY_MS, verify_policy


def test_compiler_never_emits_hard_decline():
    result = AegisynthEngine(seed=42).run(generations=4)
    assert result.final_policy.action in {"STEP_UP", "REVIEW"}
    assert "DECLINE" not in result.final_policy.model_dump_json()


def test_policy_schema_contains_only_approved_features():
    fields = set(Policy.model_fields)
    forbidden = {
        "race",
        "religion",
        "gender",
        "sex",
        "political_affiliation",
        "health_status",
        "nationality",
    }
    assert fields.isdisjoint(forbidden)
    assert {
        "merchant_age_max",
        "first_time_card_ratio_min",
        "settlement_change_days_max",
        "temporal_burst_score_min",
    }.issubset(fields)


def test_schema_rejects_invalid_policy_domain():
    with pytest.raises(ValidationError):
        Policy(
            policy_id="INVALID",
            merchant_age_max=-1,
            first_time_card_ratio_min=0.5,
            settlement_change_days_max=10,
            temporal_burst_score_min=0.7,
            action="STEP_UP",
            false_positive_rate=0.0,
        )


def test_verifier_rejects_pass_as_triggered_defence():
    policy = Policy(
        policy_id="INVALID-PASS",
        merchant_age_max=96,
        first_time_card_ratio_min=0.64,
        settlement_change_days_max=14,
        temporal_burst_score_min=0.64,
        action="PASS",
        false_positive_rate=0.0,
    )
    ok, notes = verify_policy(policy)
    assert ok is False
    assert any("PASS" in note for note in notes)


def test_verifier_rejects_policy_above_latency_budget():
    policy = Policy(
        policy_id="LATENCY-FAIL",
        merchant_age_max=96,
        first_time_card_ratio_min=0.64,
        settlement_change_days_max=14,
        temporal_burst_score_min=0.64,
        action="STEP_UP",
        false_positive_rate=0.005,
        estimated_latency_ms=DEFAULT_MAX_POLICY_LATENCY_MS + 0.01,
    )
    ok, notes = verify_policy(policy)
    assert ok is False
    assert any("latency" in note.lower() and "exceeds" in note.lower() for note in notes)


def test_compiler_output_satisfies_latency_budget():
    result = AegisynthEngine(seed=42).run(generations=4)
    assert result.final_policy.estimated_latency_ms <= DEFAULT_MAX_POLICY_LATENCY_MS
    ok, notes = verify_policy(result.final_policy)
    assert ok is True
    assert any("latency" in note.lower() and "within" in note.lower() for note in notes)


def test_counterexamples_are_escaped_attack_variants():
    world = PaymentWorld(seed=9)
    benign = world.benign(500)
    attacks = world.attack(300, hardness=0.05)
    policy = DefenceCompiler(max_fpr=0.02).synthesize(benign, attacks, generation=1)
    harder = world.attack(300, hardness=0.45)
    counterexamples = [tx for tx in harder if not matches(policy, tx)]
    assert counterexamples
    assert all(tx.label == 1 for tx in counterexamples)
    assert all(tx.attack_family == "ghost_merchant_swarm" for tx in counterexamples)
    assert all(not matches(policy, tx) for tx in counterexamples)


def test_synthetic_world_contains_no_real_identifiers():
    rows = PaymentWorld(seed=1).benign(20) + PaymentWorld(seed=2).attack(20)
    for tx in rows:
        dumped = tx.model_dump()
        assert set(dumped) == {
            "tx_id",
            "amount",
            "merchant_age_hours",
            "first_time_card_ratio",
            "settlement_change_days",
            "temporal_burst_score",
            "device_entropy",
            "geo_velocity",
            "label",
            "attack_family",
        }
        assert tx.tx_id.startswith(("B-", "A-"))

import pytest
from pydantic import ValidationError

from app.policy import DefenceCompiler
from app.schemas import Policy, Transaction


def _tx(tx_id: str, *, label: int) -> Transaction:
    return Transaction(
        tx_id=tx_id,
        amount=100.0,
        merchant_age_hours=400.0 if label == 0 else 20.0,
        first_time_card_ratio=0.10 if label == 0 else 0.90,
        settlement_change_days=100.0 if label == 0 else 2.0,
        temporal_burst_score=0.10 if label == 0 else 0.90,
        device_entropy=0.50,
        geo_velocity=0.0,
        label=label,
        attack_family="benign" if label == 0 else "ghost_merchant_swarm",
    )


def _policy() -> Policy:
    return Policy(
        policy_id="ZD-01-048-50-07-50",
        merchant_age_max=48.0,
        first_time_card_ratio_min=0.50,
        settlement_change_days_max=7.0,
        temporal_burst_score_min=0.50,
        action="STEP_UP",
        fraud_coverage=0.90,
        false_positive_rate=0.01,
        estimated_latency_ms=0.35,
    )


def _populations() -> tuple[list[Transaction], list[Transaction]]:
    return [_tx("B-1", label=0)], [_tx("A-1", label=1)]


@pytest.mark.parametrize("bad_label", [False, True])
def test_transaction_schema_rejects_boolean_labels_before_compiler_boundary(bad_label):
    payload = _tx("SCHEMA-BASE", label=0).model_dump()
    payload["label"] = bad_label

    with pytest.raises(ValidationError, match=r"label"):
        Transaction(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "amount",
        "merchant_age_hours",
        "first_time_card_ratio",
        "settlement_change_days",
        "temporal_burst_score",
        "device_entropy",
        "geo_velocity",
    ],
)
def test_transaction_schema_rejects_boolean_numeric_features(field):
    payload = _tx("SCHEMA-NUMERIC", label=0).model_dump()
    payload[field] = True

    with pytest.raises(ValidationError, match=field):
        Transaction(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "merchant_age_max",
        "first_time_card_ratio_min",
        "settlement_change_days_max",
        "temporal_burst_score_min",
        "fraud_coverage",
        "false_positive_rate",
        "estimated_latency_ms",
    ],
)
def test_policy_schema_rejects_boolean_numeric_fields(field):
    payload = _policy().model_dump()
    payload[field] = False

    with pytest.raises(ValidationError, match=field):
        Policy(**payload)


@pytest.mark.parametrize(
    "population,bad_label",
    [
        ("benign", False),
        ("attack", True),
    ],
)
def test_compiler_rejects_boolean_labels_when_schema_is_bypassed(population, bad_label):
    benign, attacks = _populations()
    row = benign[0] if population == "benign" else attacks[0]
    row.__dict__["label"] = bad_label

    with pytest.raises(
        ValueError,
        match=rf"{population} evaluation population must contain only label=.* integer transactions",
    ):
        DefenceCompiler().synthesize(benign, attacks, generation=1)


@pytest.mark.parametrize("bad_tx_id", ["", "   ", None, 123, []])
def test_compiler_rejects_malformed_transaction_ids_before_identity_set_logic(bad_tx_id):
    benign, attacks = _populations()
    benign[0].__dict__["tx_id"] = bad_tx_id

    with pytest.raises(
        ValueError,
        match=r"benign evaluation transaction must have a non-empty string tx_id",
    ):
        DefenceCompiler().synthesize(benign, attacks, generation=1)

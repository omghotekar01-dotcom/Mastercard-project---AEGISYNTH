import pytest

from app.policy import score_policy
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
        policy_id="score-boundary",
        merchant_age_max=48.0,
        first_time_card_ratio_min=0.50,
        settlement_change_days_max=7.0,
        temporal_burst_score_min=0.50,
        action="STEP_UP",
    )


def _populations() -> tuple[list[Transaction], list[Transaction]]:
    return [_tx("B-1", label=0)], [_tx("A-1", label=1)]


def test_score_policy_accepts_valid_independent_populations():
    benign, attacks = _populations()

    score = score_policy(_policy(), benign, attacks)

    assert score.coverage == 1.0
    assert score.fpr == 0.0
    assert score.blocked_attacks == 1
    assert score.benign_hits == 0


def test_score_policy_rejects_schema_bypassed_wrong_labels():
    benign, attacks = _populations()
    attacks[0].__dict__["label"] = 0

    with pytest.raises(ValueError, match=r"attack evaluation population must contain only label=1"):
        score_policy(_policy(), benign, attacks)


def test_score_policy_rejects_duplicate_weighting():
    benign, attacks = _populations()
    benign.append(benign[0].model_copy())

    with pytest.raises(ValueError, match=r"benign evaluation population contains duplicate tx_id"):
        score_policy(_policy(), benign, attacks)


def test_score_policy_rejects_cross_population_identity_contamination():
    benign, attacks = _populations()
    attacks[0].__dict__["tx_id"] = benign[0].tx_id

    with pytest.raises(ValueError, match=r"benign and attack evaluation populations share tx_id"):
        score_policy(_policy(), benign, attacks)


def test_score_policy_rejects_schema_bypassed_nonfinite_policy_feature():
    benign, attacks = _populations()
    attacks[0].__dict__["merchant_age_hours"] = float("nan")

    with pytest.raises(ValueError, match=r"attack transaction .* has non-finite merchant_age_hours"):
        score_policy(_policy(), benign, attacks)


def test_score_policy_rejects_schema_bypassed_nonfinite_policy_threshold():
    benign, attacks = _populations()
    policy = _policy()
    policy.__dict__["merchant_age_max"] = float("inf")

    with pytest.raises(ValueError, match=r"scored policy has non-finite merchant_age_max"):
        score_policy(policy, benign, attacks)


def test_score_policy_rejects_schema_bypassed_out_of_range_policy_threshold():
    benign, attacks = _populations()
    policy = _policy()
    policy.__dict__["first_time_card_ratio_min"] = 1.5

    with pytest.raises(ValueError, match=r"scored policy has out-of-range first_time_card_ratio_min"):
        score_policy(policy, benign, attacks)


def test_score_policy_rejects_schema_bypassed_unsupported_action():
    benign, attacks = _populations()
    policy = _policy()
    policy.__dict__["action"] = "DECLINE"

    with pytest.raises(ValueError, match=r"scored policy action must be one of PASS, STEP_UP, or REVIEW"):
        score_policy(policy, benign, attacks)

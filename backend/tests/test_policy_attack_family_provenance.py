import pytest

from app.policy import score_policy
from app.schemas import Policy, Transaction


def _policy() -> Policy:
    return Policy(
        policy_id="ZD-01-048-50-07-50",
        merchant_age_max=48.0,
        first_time_card_ratio_min=0.50,
        settlement_change_days_max=7.0,
        temporal_burst_score_min=0.50,
        action="STEP_UP",
    )


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


def _populations() -> tuple[list[Transaction], list[Transaction]]:
    return [_tx("B-1", label=0)], [_tx("A-1", label=1)]


@pytest.mark.parametrize("bad_family", [None, 123, "", "A" * 65])
def test_scoring_rejects_malformed_schema_bypassed_attack_family(bad_family):
    benign, attacks = _populations()
    attacks[0].__dict__["attack_family"] = bad_family

    with pytest.raises(
        ValueError,
        match=r"attack evaluation transaction attack_family must be a non-empty string of at most 64 characters",
    ):
        score_policy(_policy(), benign, attacks)


@pytest.mark.parametrize("bad_family", [" ghost", "ghost ", "ghost family", "ghost\tfamily", "ghost\nfamily"])
def test_scoring_rejects_whitespace_in_schema_bypassed_attack_family(bad_family):
    benign, attacks = _populations()
    attacks[0].__dict__["attack_family"] = bad_family

    with pytest.raises(ValueError, match=r"attack evaluation transaction attack_family must not contain whitespace"):
        score_policy(_policy(), benign, attacks)


def test_scoring_rejects_attack_row_with_benign_provenance():
    benign, attacks = _populations()
    attacks[0].__dict__["attack_family"] = "benign"

    with pytest.raises(ValueError, match=r"attack evaluation population must not use the benign attack_family provenance label"):
        score_policy(_policy(), benign, attacks)


def test_scoring_rejects_benign_row_with_attack_provenance():
    benign, attacks = _populations()
    benign[0].__dict__["attack_family"] = "ghost_merchant_swarm"

    with pytest.raises(ValueError, match=r"benign evaluation population must use the benign attack_family provenance label"):
        score_policy(_policy(), benign, attacks)


def test_scoring_accepts_canonical_population_provenance():
    benign, attacks = _populations()

    score = score_policy(_policy(), benign, attacks)

    assert score.coverage == 1.0
    assert score.fpr == 0.0

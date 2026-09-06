import pytest

from app.policy import DefenceCompiler
from app.schemas import Transaction


def _transaction(
    tx_id: str,
    *,
    label: int,
    attack_family: str,
    matches_all_candidates: bool,
) -> Transaction:
    return Transaction(
        tx_id=tx_id,
        amount=100.0,
        merchant_age_hours=24.0 if matches_all_candidates else 1000.0,
        first_time_card_ratio=0.90,
        settlement_change_days=1.0,
        temporal_burst_score=0.90,
        device_entropy=0.50,
        geo_velocity=10.0,
        label=label,
        attack_family=attack_family,
    )


def _evidence() -> tuple[list[Transaction], list[Transaction]]:
    benign = [
        _transaction(
            "benign-hit",
            label=0,
            attack_family="benign",
            matches_all_candidates=True,
        )
    ]
    benign.extend(
        _transaction(
            f"benign-miss-{index}",
            label=0,
            attack_family="benign",
            matches_all_candidates=False,
        )
        for index in range(5)
    )
    attacks = [
        _transaction(
            "attack-hit",
            label=1,
            attack_family="ghost_merchant_swarm",
            matches_all_candidates=True,
        )
    ]
    return benign, attacks


def test_compiler_fails_closed_when_reported_rounding_would_exceed_budget():
    benign, attacks = _evidence()

    # Raw FPR is 1/6 ~= 0.1666667, which is within 0.16667, but the
    # judge-visible four-decimal metric is 0.1667 and would violate that budget.
    with pytest.raises(RuntimeError, match="No policy satisfies"):
        DefenceCompiler(max_fpr=0.16667).synthesize(benign, attacks, generation=1)


def test_compiler_emits_policy_when_reported_fpr_itself_is_within_budget():
    benign, attacks = _evidence()

    policy = DefenceCompiler(max_fpr=0.1667).synthesize(benign, attacks, generation=1)

    assert policy.false_positive_rate == 0.1667
    assert policy.false_positive_rate <= 0.1667

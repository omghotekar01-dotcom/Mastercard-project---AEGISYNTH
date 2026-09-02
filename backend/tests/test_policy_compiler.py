import pytest

from app.policy import DefenceCompiler, _policy_id, score_policy
from app.schemas import Transaction


def tx(tx_id: str, *, age: float, card: float, settle: float, burst: float, fraud: bool) -> Transaction:
    """Build a minimal synthetic transaction using the canonical API schema.

    Compiler tests intentionally keep non-policy features at deterministic neutral values so
    failures reflect compiler behaviour rather than fixture/schema drift.
    """
    return Transaction(
        tx_id=tx_id,
        amount=100.0,
        merchant_age_hours=age,
        first_time_card_ratio=card,
        settlement_change_days=settle,
        temporal_burst_score=burst,
        device_entropy=0.50,
        geo_velocity=0.0,
        label=int(fraud),
        attack_family="ghost_merchant_swarm" if fraud else "benign",
    )


def fixture_world():
    benign = [
        tx("B-1", age=400, card=0.10, settle=100, burst=0.10, fraud=False),
        tx("B-2", age=300, card=0.20, settle=90, burst=0.20, fraud=False),
        tx("B-3", age=220, card=0.30, settle=80, burst=0.30, fraud=False),
    ]
    attacks = [
        tx("A-1", age=20, card=0.90, settle=2, burst=0.90, fraud=True),
        tx("A-2", age=30, card=0.85, settle=3, burst=0.85, fraud=True),
        tx("A-3", age=40, card=0.80, settle=4, burst=0.80, fraud=True),
    ]
    assert all(row.label == 0 and row.attack_family == "benign" for row in benign)
    assert all(row.label == 1 and row.attack_family == "ghost_merchant_swarm" for row in attacks)
    return benign, attacks


def test_compiler_is_deterministic_for_identical_inputs():
    benign, attacks = fixture_world()
    compiler = DefenceCompiler(max_fpr=0.02)

    first = compiler.synthesize(benign, attacks, generation=1)
    second = compiler.synthesize(benign, attacks, generation=1)

    assert first.model_dump() == second.model_dump()


def test_compiler_output_respects_configured_false_positive_budget():
    benign, attacks = fixture_world()
    compiler = DefenceCompiler(max_fpr=0.02)
    policy = compiler.synthesize(benign, attacks, generation=2)
    score = score_policy(policy, benign, attacks)

    assert score.fpr <= compiler.max_fpr
    assert policy.false_positive_rate == round(score.fpr, 4)
    assert policy.fraud_coverage == round(score.coverage, 4)
    assert policy.action == "STEP_UP"


@pytest.mark.parametrize("missing_side", ["benign", "attacks"])
def test_score_policy_rejects_empty_evidence_populations(missing_side):
    benign, attacks = fixture_world()
    policy = DefenceCompiler(max_fpr=0.02).synthesize(benign, attacks, generation=3)
    if missing_side == "benign":
        benign = []
        expected_population = "benign"
    else:
        attacks = []
        expected_population = "attack"

    with pytest.raises(ValueError, match=rf"{expected_population} scoring population must not be empty"):
        score_policy(policy, benign, attacks)


@pytest.mark.parametrize("missing_side", ["benign", "attacks"])
def test_compiler_rejects_empty_evaluation_populations(missing_side):
    benign, attacks = fixture_world()
    if missing_side == "benign":
        benign = []
    else:
        attacks = []

    expected_population = "attack" if missing_side == "attacks" else "benign"
    with pytest.raises(ValueError, match=rf"{expected_population} evaluation population must not be empty"):
        DefenceCompiler(max_fpr=0.02).synthesize(benign, attacks, generation=3)


def test_compiler_rejects_mislabeled_benign_population():
    benign, attacks = fixture_world()
    benign[0] = benign[0].model_copy(update={"label": 1})

    with pytest.raises(ValueError, match="benign evaluation population must contain only label=0"):
        DefenceCompiler(max_fpr=0.02).synthesize(benign, attacks, generation=3)


def test_compiler_rejects_mislabeled_attack_population():
    benign, attacks = fixture_world()
    attacks[0] = attacks[0].model_copy(update={"label": 0})

    with pytest.raises(ValueError, match="attack evaluation population must contain only label=1"):
        DefenceCompiler(max_fpr=0.02).synthesize(benign, attacks, generation=3)


@pytest.mark.parametrize("population", ["benign", "attack"])
def test_compiler_rejects_duplicate_transaction_ids_within_population(population):
    benign, attacks = fixture_world()
    rows = benign if population == "benign" else attacks
    rows[1] = rows[1].model_copy(update={"tx_id": rows[0].tx_id})

    with pytest.raises(ValueError, match=rf"{population} evaluation population contains duplicate tx_id"):
        DefenceCompiler(max_fpr=0.02).synthesize(benign, attacks, generation=3)


def test_compiler_rejects_transaction_id_overlap_between_populations():
    benign, attacks = fixture_world()
    attacks[0] = attacks[0].model_copy(update={"tx_id": benign[0].tx_id})

    with pytest.raises(ValueError, match="benign and attack evaluation populations share tx_id"):
        DefenceCompiler(max_fpr=0.02).synthesize(benign, attacks, generation=3)


@pytest.mark.parametrize(
    "population,feature,value",
    [
        ("benign", "merchant_age_hours", float("nan")),
        ("benign", "first_time_card_ratio", float("inf")),
        ("attack", "settlement_change_days", float("-inf")),
        ("attack", "temporal_burst_score", float("nan")),
    ],
)
def test_compiler_rejects_non_finite_policy_features(population, feature, value):
    benign, attacks = fixture_world()
    rows = benign if population == "benign" else attacks
    rows[0] = rows[0].model_copy(update={feature: value})

    with pytest.raises(ValueError, match=rf"{population} transaction .* has non-finite {feature}"):
        DefenceCompiler(max_fpr=0.02).synthesize(benign, attacks, generation=3)


@pytest.mark.parametrize(
    "population,feature,value",
    [
        ("benign", "merchant_age_hours", True),
        ("benign", "first_time_card_ratio", "0.7"),
        ("attack", "settlement_change_days", None),
        ("attack", "temporal_burst_score", False),
    ],
)
def test_compiler_rejects_schema_bypassed_non_numeric_policy_features(population, feature, value):
    benign, attacks = fixture_world()
    rows = benign if population == "benign" else attacks
    rows[0].__dict__[feature] = value

    with pytest.raises(ValueError, match=rf"{population} transaction .* has non-numeric {feature}"):
        DefenceCompiler(max_fpr=0.02).synthesize(benign, attacks, generation=3)


@pytest.mark.parametrize(
    "population,feature,value",
    [
        ("benign", "merchant_age_hours", -1.0),
        ("benign", "first_time_card_ratio", 1.01),
        ("attack", "settlement_change_days", -0.1),
        ("attack", "temporal_burst_score", -0.01),
    ],
)
def test_compiler_rejects_out_of_range_policy_features(population, feature, value):
    benign, attacks = fixture_world()
    rows = benign if population == "benign" else attacks
    rows[0] = rows[0].model_copy(update={feature: value})

    with pytest.raises(ValueError, match=rf"{population} transaction .* has out-of-range {feature}"):
        DefenceCompiler(max_fpr=0.02).synthesize(benign, attacks, generation=3)


@pytest.mark.parametrize("invalid_budget", [-0.01, 1.01, float("nan"), float("inf"), float("-inf")])
def test_compiler_rejects_malformed_false_positive_budgets(invalid_budget):
    with pytest.raises(ValueError, match=r"max_fpr must be finite and within \[0, 1\]"):
        DefenceCompiler(max_fpr=invalid_budget)


@pytest.mark.parametrize("invalid_budget", [True, False, "0.02", None])
def test_compiler_rejects_non_numeric_false_positive_budgets(invalid_budget):
    with pytest.raises(ValueError, match=r"max_fpr must be a real numeric value"):
        DefenceCompiler(max_fpr=invalid_budget)


@pytest.mark.parametrize("invalid_generation", [True, False, -1, 1.0, "1", None])
def test_compiler_rejects_malformed_policy_generations(invalid_generation):
    benign, attacks = fixture_world()

    with pytest.raises(ValueError, match=r"generation must be a non-negative integer"):
        DefenceCompiler(max_fpr=0.02).synthesize(benign, attacks, generation=invalid_generation)


def test_compiler_accepts_zero_generation_with_stable_policy_identity():
    benign, attacks = fixture_world()

    policy = DefenceCompiler(max_fpr=0.02).synthesize(benign, attacks, generation=0)

    assert policy.policy_id.startswith("ZD-00-")


def test_policy_identity_changes_when_any_semantic_threshold_changes():
    baseline = _policy_id(3, 96, 0.64, 14, 0.64)

    variants = {
        _policy_id(3, 120, 0.64, 14, 0.64),
        _policy_id(3, 96, 0.70, 14, 0.64),
        _policy_id(3, 96, 0.64, 21, 0.64),
        _policy_id(3, 96, 0.64, 14, 0.70),
    }

    assert baseline not in variants
    assert len(variants) == 4

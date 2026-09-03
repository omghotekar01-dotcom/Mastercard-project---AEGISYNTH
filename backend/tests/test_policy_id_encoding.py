import pytest

from app.policy import _policy_id


@pytest.mark.parametrize(
    "threshold,expected_code",
    [
        (0.50, "50"),
        (0.58, "58"),
        (0.64, "64"),
        (0.70, "70"),
        (0.76, "76"),
    ],
)
def test_policy_id_encodes_compiler_percentage_grid_without_float_truncation(
    threshold: float, expected_code: str
):
    policy_id = _policy_id(3, 96, threshold, 14, threshold)

    assert policy_id == f"ZD-03-096-{expected_code}-14-{expected_code}"

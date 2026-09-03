import pytest

from app.policy import DefenceCompiler


@pytest.mark.parametrize("generation", [0, 9, 10, 999, True])
def test_compiler_rejects_generations_outside_review_domain(generation):
    with pytest.raises(ValueError, match=r"generation must be an integer within \[1, 8\]"):
        DefenceCompiler(max_fpr=0.02).synthesize([], [], generation=generation)

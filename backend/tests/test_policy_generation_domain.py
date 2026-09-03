import pytest

from app.policy import DefenceCompiler


@pytest.mark.parametrize("generation", [9, 10, 999])
def test_compiler_rejects_generations_beyond_review_domain(generation):
    with pytest.raises(ValueError, match=r"generation must be a non-negative integer within \[0, 8\]"):
        DefenceCompiler(max_fpr=0.02).synthesize([], [], generation=generation)

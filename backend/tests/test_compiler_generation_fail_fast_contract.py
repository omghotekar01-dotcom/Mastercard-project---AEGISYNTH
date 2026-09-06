import pytest

import app.policy as policy_module
from app.policy import DefenceCompiler


@pytest.mark.parametrize("generation", [True, False, 0, 9, -1, 1.0, "1", None])
def test_invalid_generation_fails_before_evidence_evaluation(monkeypatch, generation):
    """Invalid compiler provenance must fail before benchmark evidence is touched."""

    def unexpected_evaluation(*_args, **_kwargs):
        raise AssertionError("evaluation must not run for an invalid generation")

    monkeypatch.setattr(
        policy_module,
        "_validate_evaluation_populations",
        unexpected_evaluation,
    )

    compiler = DefenceCompiler(max_fpr=0.02)

    with pytest.raises(ValueError, match=r"generation must be an integer within \[1, 8\]"):
        compiler.synthesize([], [], generation=generation)

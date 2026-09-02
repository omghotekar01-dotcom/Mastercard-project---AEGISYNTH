import app.verification as verification
from app.engine import AegisynthEngine


def test_verifier_fails_closed_on_z3_runtime_error(monkeypatch):
    policy = AegisynthEngine(seed=42).run(generations=1).final_policy

    class BrokenSolver:
        def __init__(self):
            raise RuntimeError("simulated solver initialization failure")

    monkeypatch.setattr(verification, "Solver", BrokenSolver)

    ok, notes = verification.verify_policy(policy)

    assert ok is False
    assert notes == ["Formal verification failed closed: Z3 runtime error"]

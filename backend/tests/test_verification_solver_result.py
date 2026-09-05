import app.verification as verification_module
from app.schemas import Policy


def _valid_policy() -> Policy:
    return Policy(
        policy_id="policy-z3-result-contract",
        merchant_age_max=720.0,
        first_time_card_ratio_min=0.5,
        settlement_change_days_max=30.0,
        temporal_burst_score_min=0.5,
        action="STEP_UP",
        fraud_coverage=0.9,
        false_positive_rate=0.01,
        estimated_latency_ms=1.0,
        counterexamples_remaining=0,
    )


def test_verify_policy_reports_unsat_only_for_explicit_unsat(monkeypatch):
    class UnsatSolver:
        configured_timeout = None

        def set(self, *, timeout):
            type(self).configured_timeout = timeout

        def add(self, *_args):
            return None

        def check(self):
            return verification_module.unsat

    monkeypatch.setattr(verification_module, "Solver", UnsatSolver)

    ok, notes = verification_module.verify_policy(_valid_policy())

    assert ok is False
    assert notes == ["Policy conditions are unsatisfiable"]
    assert UnsatSolver.configured_timeout == verification_module.DEFAULT_Z3_TIMEOUT_MS


def test_verify_policy_fails_closed_and_distinguishes_inconclusive_z3_result(monkeypatch):
    class InconclusiveResult:
        pass

    class InconclusiveSolver:
        configured_timeout = None

        def set(self, *, timeout):
            type(self).configured_timeout = timeout

        def add(self, *_args):
            return None

        def check(self):
            return InconclusiveResult()

    monkeypatch.setattr(verification_module, "Solver", InconclusiveSolver)

    ok, notes = verification_module.verify_policy(_valid_policy())

    assert ok is False
    assert notes == ["Formal verification inconclusive: Z3 did not return sat or unsat"]
    assert "unsatisfiable" not in notes[0].lower()
    assert InconclusiveSolver.configured_timeout == verification_module.DEFAULT_Z3_TIMEOUT_MS


def test_verify_policy_fails_closed_if_solver_timeout_configuration_errors(monkeypatch):
    class TimeoutConfigurationFailureSolver:
        def set(self, *, timeout):
            raise RuntimeError(f"cannot configure timeout {timeout}")

    monkeypatch.setattr(verification_module, "Solver", TimeoutConfigurationFailureSolver)

    ok, notes = verification_module.verify_policy(_valid_policy())

    assert ok is False
    assert notes == ["Formal verification failed closed: Z3 runtime error"]

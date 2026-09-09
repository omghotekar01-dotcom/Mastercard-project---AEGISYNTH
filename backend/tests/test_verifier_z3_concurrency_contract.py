from concurrent.futures import ThreadPoolExecutor
import threading
import time

from app import verification
from app.schemas import Policy


def _valid_policy() -> Policy:
    return Policy(
        policy_id="concurrency-guardrail",
        merchant_age_max=24.0,
        first_time_card_ratio_min=0.5,
        settlement_change_days_max=7.0,
        temporal_burst_score_min=0.7,
        action="STEP_UP",
        fraud_coverage=0.9,
        false_positive_rate=0.01,
        estimated_latency_ms=1.0,
        counterexamples_remaining=0,
    )


def test_verify_policy_serializes_z3_context_access(monkeypatch):
    """Concurrent verifier calls must never overlap access to the shared Z3 context."""
    worker_count = 8
    start = threading.Barrier(worker_count)
    state_lock = threading.Lock()
    active_checks = 0
    max_active_checks = 0
    sat_sentinel = object()
    unsat_sentinel = object()

    class FakeSolver:
        def set(self, **_kwargs):
            return None

        def add(self, *_args):
            return None

        def check(self):
            nonlocal active_checks, max_active_checks
            with state_lock:
                active_checks += 1
                max_active_checks = max(max_active_checks, active_checks)
            try:
                time.sleep(0.02)
                return sat_sentinel
            finally:
                with state_lock:
                    active_checks -= 1

    monkeypatch.setattr(verification, "HAS_Z3", True)
    monkeypatch.setattr(verification, "Real", lambda name: name)
    monkeypatch.setattr(verification, "And", lambda *args: args)
    monkeypatch.setattr(verification, "Solver", FakeSolver)
    monkeypatch.setattr(verification, "sat", sat_sentinel)
    monkeypatch.setattr(verification, "unsat", unsat_sentinel)

    def verify_once():
        start.wait()
        return verification.verify_policy(_valid_policy())

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        results = list(executor.map(lambda _index: verify_once(), range(worker_count)))

    assert all(ok for ok, _notes in results)
    assert max_active_checks == 1

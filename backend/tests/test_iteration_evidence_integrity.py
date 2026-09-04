import pytest
from pydantic import ValidationError

from app.engine import AegisynthEngine
from app.schemas import CounterexampleTrace, IterationResult


def _iteration_payload() -> dict:
    return AegisynthEngine(seed=42).run(generations=1).iterations[0].model_dump()


def test_iteration_rejects_counterexample_count_mismatch():
    payload = _iteration_payload()
    payload["counterexamples"] += 1

    with pytest.raises(ValidationError, match="counterexamples must equal trace.escaped_count"):
        IterationResult.model_validate(payload)


def test_iteration_rejects_candidate_counterexample_mismatch():
    payload = _iteration_payload()
    payload["candidate"]["counterexamples_remaining"] += 1

    with pytest.raises(ValidationError, match="candidate.counterexamples_remaining must equal counterexamples"):
        IterationResult.model_validate(payload)


def test_trace_rejects_inconsistent_escape_evidence():
    payload = _iteration_payload()["trace"]

    too_many = {**payload, "escaped_count": payload["redteam_attack_count"] + 1, "escaped_rate": 1.0}
    with pytest.raises(ValidationError, match="escaped_count cannot exceed redteam_attack_count"):
        CounterexampleTrace.model_validate(too_many)

    wrong_rate = {**payload, "escaped_rate": 0.0 if payload["escaped_rate"] != 0.0 else 1.0}
    with pytest.raises(ValidationError, match="escaped_rate must equal"):
        CounterexampleTrace.model_validate(wrong_rate)

    extra_samples = {
        **payload,
        "escaped_count": 0,
        "escaped_rate": 0.0,
        "sample_tx_ids": ["impossible-sample"],
    }
    with pytest.raises(ValidationError, match="sample_tx_ids cannot contain more entries than escaped_count"):
        CounterexampleTrace.model_validate(extra_samples)


def test_trace_rejects_invalid_sample_identities():
    payload = _iteration_payload()["trace"]
    escaped_count = max(2, payload["escaped_count"])
    payload = {
        **payload,
        "escaped_count": escaped_count,
        "escaped_rate": round(escaped_count / payload["redteam_attack_count"], 4),
    }

    for bad_id in ["", "   ", " rt-001", "rt-001 ", "rt 001", "rt\t001", "rt\n001", "x" * 65]:
        with pytest.raises(ValidationError, match="canonical transaction IDs"):
            CounterexampleTrace.model_validate({**payload, "sample_tx_ids": [bad_id]})

    with pytest.raises(ValidationError, match="must not contain duplicate transaction IDs"):
        CounterexampleTrace.model_validate({**payload, "sample_tx_ids": ["rt-001", "rt-001"]})


def test_trace_accepts_current_canonical_sample_identities():
    payload = _iteration_payload()["trace"]
    if payload["escaped_count"] == 0:
        payload = {
            **payload,
            "escaped_count": 1,
            "escaped_rate": round(1 / payload["redteam_attack_count"], 4),
            "sample_tx_ids": ["A-000001"],
        }

    trace = CounterexampleTrace.model_validate(payload)
    assert all(tx_id and len(tx_id) <= 64 and not any(char.isspace() for char in tx_id) for tx_id in trace.sample_tx_ids)


def test_current_engine_iteration_evidence_remains_valid():
    iteration = AegisynthEngine(seed=42).run(generations=1).iterations[0]
    assert IterationResult.model_validate(iteration.model_dump()) == iteration

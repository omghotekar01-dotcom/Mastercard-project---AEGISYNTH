from app.engine import AegisynthEngine
from app.verification import verify_policy


def test_verifier_rejects_boolean_business_budgets():
    policy = AegisynthEngine(seed=42).run(generations=1).final_policy

    invalid_configs = [
        {"max_fpr": True, "max_latency_ms": 5.0},
        {"max_fpr": False, "max_latency_ms": 5.0},
        {"max_fpr": 0.02, "max_latency_ms": True},
        {"max_fpr": 0.02, "max_latency_ms": False},
    ]

    for config in invalid_configs:
        ok, notes = verify_policy(policy, **config)
        assert ok is False
        assert notes
        assert "configuration invalid" in notes[0].lower()
        assert "numeric value" in notes[0].lower()

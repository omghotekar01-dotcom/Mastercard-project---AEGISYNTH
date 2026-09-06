from app.engine import AegisynthEngine


def test_engine_repeated_runs_are_reproducible_for_same_seed_and_inputs():
    """Repeated benchmark runs must emit identical evidence for identical inputs."""
    engine = AegisynthEngine(seed=42, max_fpr=0.02)

    first = engine.run(generations=2)
    second = engine.run(generations=2)

    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_independent_engines_are_reproducible_for_same_seed_and_inputs():
    """Fresh engine instances must agree so benchmark evidence is portable across runs."""
    first = AegisynthEngine(seed=42, max_fpr=0.02).run(generations=2)
    second = AegisynthEngine(seed=42, max_fpr=0.02).run(generations=2)

    assert first.model_dump(mode="json") == second.model_dump(mode="json")

from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app

client = TestClient(app)


def test_review_package_refuses_finished_handoff_that_fails_independent_verification(monkeypatch):
    benchmark = object()
    package = object()
    verified_candidates = []

    monkeypatch.setattr(main_module, '_benchmark', lambda: benchmark)

    def package_builder(result):
        assert result is benchmark
        return package

    def package_verifier(candidate):
        verified_candidates.append(candidate)
        return False

    monkeypatch.setattr(main_module, 'build_review_package', package_builder)
    monkeypatch.setattr(main_module, 'verify_review_package', package_verifier)

    res = client.get('/api/v1/review-package')

    assert res.status_code == 503
    assert res.json()['detail'] == {
        'status': 'unavailable',
        'reason': 'review_package_verification_failed',
        'scope': 'synthetic defensive payment-security laboratory',
    }
    assert verified_candidates == [package]

from pathlib import Path


DOCKERFILE = Path(__file__).resolve().parents[1] / "Dockerfile"


def test_backend_container_process_and_healthcheck_share_runtime_port_contract():
    """Hosted PORT overrides must reach both uvicorn and the readiness probe."""
    content = DOCKERFILE.read_text(encoding="utf-8")

    assert "os.getenv('PORT', '8000')" in content
    assert "${PORT:-8000}" in content
    assert "--port" in content
    assert "/ready" in content

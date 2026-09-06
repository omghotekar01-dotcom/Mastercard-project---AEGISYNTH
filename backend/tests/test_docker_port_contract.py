from pathlib import Path


BACKEND_DOCKERFILE = Path(__file__).resolve().parents[1] / "Dockerfile"
FRONTEND_DOCKERFILE = Path(__file__).resolve().parents[2] / "frontend" / "Dockerfile"


def test_backend_container_process_and_healthcheck_share_runtime_port_contract():
    """Hosted PORT overrides must reach both uvicorn and the readiness probe."""
    content = BACKEND_DOCKERFILE.read_text(encoding="utf-8")

    assert "os.getenv('PORT', '8000')" in content
    assert "${PORT:-8000}" in content
    assert "--port" in content
    assert "/ready" in content


def test_frontend_container_process_and_healthcheck_share_runtime_port_contract():
    """Hosted PORT overrides must reach both Next.js and its health probe."""
    content = FRONTEND_DOCKERFILE.read_text(encoding="utf-8")

    assert "PORT=3000" in content
    assert "${PORT:-3000}" in content
    assert "CMD [\"node\",\"server.js\"]" in content

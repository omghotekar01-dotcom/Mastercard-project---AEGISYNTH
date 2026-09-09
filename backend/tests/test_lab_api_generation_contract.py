from fastapi.testclient import TestClient

from app.contracts import COMPILER_GENERATION_MAX, COMPILER_GENERATION_MIN
from app.main import app

client = TestClient(app)


def _generation_parameter_schema() -> dict:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    parameters = response.json()["paths"]["/api/v1/lab/run"]["get"]["parameters"]
    return next(parameter["schema"] for parameter in parameters if parameter["name"] == "generations")


def test_lab_api_generation_schema_matches_shared_compiler_contract():
    schema = _generation_parameter_schema()

    assert schema["minimum"] == COMPILER_GENERATION_MIN
    assert schema["maximum"] == COMPILER_GENERATION_MAX
    assert COMPILER_GENERATION_MIN <= schema["default"] <= COMPILER_GENERATION_MAX


def test_lab_api_rejects_generations_immediately_outside_shared_contract():
    below = client.get(
        "/api/v1/lab/run",
        params={"seed": 42, "generations": COMPILER_GENERATION_MIN - 1},
    )
    above = client.get(
        "/api/v1/lab/run",
        params={"seed": 42, "generations": COMPILER_GENERATION_MAX + 1},
    )

    assert below.status_code == 422
    assert above.status_code == 422

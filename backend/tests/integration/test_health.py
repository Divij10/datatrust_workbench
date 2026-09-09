from fastapi.testclient import TestClient


def test_health_returns_liveness_summary(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "datatrust-workbench",
        "environment": "test",
    }
    assert response.headers["x-request-id"]

from fastapi.testclient import TestClient


def test_cors_allows_rule_approval_patch_from_the_frontend(client: TestClient) -> None:
    response = client.options(
        "/api/v1/rules/example-rule",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "PATCH",
        },
    )

    assert response.status_code == 200
    assert "PATCH" in response.headers["access-control-allow-methods"]

import asyncio

from fastapi.testclient import TestClient

from app.adapters.llm.base import RuleGenerator
from app.services.rule_service import RuleService
from app.services.rule_validator import RuleSemanticValidator


def create_dataset(client: TestClient) -> str:
    response = client.post(
        "/api/v1/datasets",
        files={
            "file": (
                "customers.csv",
                b"customer_id,email,age,state\n1001,a@example.com,34,AZ\n1002,,140,ZZ\n",
                "text/csv",
            )
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_fake_provider_creates_proposed_ai_candidates(client: TestClient) -> None:
    dataset_id = create_dataset(client)

    response = client.post(f"/api/v1/datasets/{dataset_id}/rules/suggest")

    assert response.status_code == 200, response.text
    candidates = response.json()
    assert {candidate["rule"]["rule_type"] for candidate in candidates} >= {
        "required",
        "email",
        "range",
        "pattern",
    }
    assert all(candidate["status"] == "proposed" for candidate in candidates)
    assert all(candidate["source"] == "ai" for candidate in candidates)
    assert all(len(candidate["audit_events"]) == 1 for candidate in candidates)

    evaluation = client.post(f"/api/v1/datasets/{dataset_id}/evaluate")
    assert evaluation.status_code == 200
    assert evaluation.json()["evaluated_rule_count"] == 0
    assert evaluation.json()["quality_score"] is None


def test_duplicate_suggestions_are_rejected_before_persistence(client: TestClient) -> None:
    dataset_id = create_dataset(client)
    assert client.post(f"/api/v1/datasets/{dataset_id}/rules/suggest").status_code == 200

    response = client.post(f"/api/v1/datasets/{dataset_id}/rules/suggest")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "DUPLICATE_RULE"


class MalformedGenerator(RuleGenerator):
    async def generate_rules(self, profile: object) -> object:
        return {
            "rules": [
                {
                    "rule_type": "pattern",
                    "column": "email",
                    "pattern": ".*",
                    "description": "Unsafe raw pattern",
                }
            ],
            "explanation": "Invalid output fixture.",
        }


class TimeoutGenerator(RuleGenerator):
    async def generate_rules(self, profile: object) -> object:
        await asyncio.sleep(0.01)
        return {"rules": [], "explanation": "Never reached"}


def replace_generator(client: TestClient, generator: RuleGenerator, timeout: float) -> None:
    current = client.app.state.rule_service
    client.app.state.rule_service = RuleService(
        current._repository,
        RuleSemanticValidator(),
        generator,
        timeout,
    )


def test_malformed_provider_output_is_rejected(client: TestClient) -> None:
    dataset_id = create_dataset(client)
    replace_generator(client, MalformedGenerator(), timeout=1)

    response = client.post(f"/api/v1/datasets/{dataset_id}/rules/suggest")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "LLM_OUTPUT_VALIDATION_FAILED"
    assert client.get(f"/api/v1/datasets/{dataset_id}/rules").json() == []


def test_provider_timeout_returns_service_unavailable(client: TestClient) -> None:
    dataset_id = create_dataset(client)
    replace_generator(client, TimeoutGenerator(), timeout=0.001)

    response = client.post(f"/api/v1/datasets/{dataset_id}/rules/suggest")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "LLM_PROVIDER_UNAVAILABLE"

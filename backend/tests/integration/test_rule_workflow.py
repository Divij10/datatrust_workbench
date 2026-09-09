from fastapi.testclient import TestClient


def create_dataset(client: TestClient) -> str:
    response = client.post(
        "/api/v1/datasets",
        files={"file": ("people.csv", b"email,age\na@example.com,20\nbad,150\n", "text/csv")},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_human_rule_requires_approval_and_tracks_audit(client: TestClient) -> None:
    dataset_id = create_dataset(client)
    payload = {
        "rule_type": "range",
        "column": "age",
        "min_value": 0,
        "max_value": 120,
        "severity": "warning",
        "description": "Age must be plausible.",
    }

    created = client.post(f"/api/v1/datasets/{dataset_id}/rules", json=payload)
    assert created.status_code == 201, created.text
    created_body = created.json()
    assert created_body["status"] == "proposed"
    assert created_body["source"] == "human"
    rule_id = created_body["id"]

    approved = client.patch(
        f"/api/v1/rules/{rule_id}", json={"status": "approved", "rationale": "Reviewed"}
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"
    assert len(approved.json()["audit_events"]) == 2

    listed = client.get(f"/api/v1/datasets/{dataset_id}/rules", params={"status": "approved"})
    assert listed.status_code == 200
    assert [rule["id"] for rule in listed.json()] == [rule_id]

    evaluation = client.post(f"/api/v1/datasets/{dataset_id}/evaluate")
    assert evaluation.status_code == 200, evaluation.text
    report = evaluation.json()
    assert report["evaluated_rule_count"] == 1
    assert report["total_violation_count"] == 1
    assert report["quality_score"] == 50.0
    assert report["dimensions"]["validity"]["score"] == 50.0
    assert report["results"][0]["violations"][0]["observed_value"] == 150

    fetched = client.get(f"/api/v1/reports/{report['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == report["id"]

    exported = client.get(f"/api/v1/reports/{report['id']}/export")
    assert exported.status_code == 200
    assert exported.headers["content-disposition"].endswith(f'quality-report-{report["id"]}.json"')
    assert exported.json() == report


def test_rule_rejects_unknown_column_and_duplicate_equivalent_rule(client: TestClient) -> None:
    dataset_id = create_dataset(client)
    unknown = client.post(
        f"/api/v1/datasets/{dataset_id}/rules",
        json={"rule_type": "required", "column": "missing", "description": "Must exist"},
    )
    assert unknown.status_code == 400
    assert unknown.json()["error"]["code"] == "RULE_SEMANTIC_VALIDATION_FAILED"

    payload = {"rule_type": "email", "column": "email", "description": "Use email syntax"}
    assert client.post(f"/api/v1/datasets/{dataset_id}/rules", json=payload).status_code == 201
    duplicate = client.post(
        f"/api/v1/datasets/{dataset_id}/rules",
        json={**payload, "description": "Different text, same rule"},
    )
    assert duplicate.status_code == 400
    assert duplicate.json()["error"]["code"] == "DUPLICATE_RULE"


def test_rule_rejects_structurally_invalid_payload(client: TestClient) -> None:
    dataset_id = create_dataset(client)
    response = client.post(
        f"/api/v1/datasets/{dataset_id}/rules",
        json={"rule_type": "pattern", "column": "email", "pattern": ".*", "description": "Unsafe"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "REQUEST_VALIDATION_FAILED"

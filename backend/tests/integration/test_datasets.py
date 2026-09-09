from fastapi.testclient import TestClient


def upload(
    client: TestClient, name: str, body: bytes, content_type: str = "text/csv"
) -> dict[str, object]:
    response = client.post("/api/v1/datasets", files={"file": (name, body, content_type)})
    assert response.status_code == 201, response.text
    return response.json()


def test_upload_csv_and_fetch_profile(client: TestClient) -> None:
    dataset = upload(
        client, "customers.csv", b"id,email,age\n1,a@example.com,20\n2,,40\n2,b@example.com,20\n"
    )

    assert dataset["filename"] == "customers.csv"
    assert dataset["file_type"] == "csv"
    assert dataset["row_count"] == 3
    profile = client.get(f"/api/v1/datasets/{dataset['id']}/profile")

    assert profile.status_code == 200
    profile_body = profile.json()
    assert profile_body["duplicate_row_count"] == 0
    email = next(column for column in profile_body["columns"] if column["name"] == "email")
    assert email["null_count"] == 1
    assert email["inferred_type"] == "string"


def test_upload_json(client: TestClient) -> None:
    dataset = upload(
        client,
        "events.json",
        b'[{"event_id": 1, "active": true}, {"event_id": 2, "active": false}]',
        "application/json",
    )

    assert dataset["file_type"] == "json"
    detail = client.get(f"/api/v1/datasets/{dataset['id']}")
    assert detail.status_code == 200
    assert detail.json()["column_count"] == 2


def test_rejects_unsupported_upload(client: TestClient) -> None:
    response = client.post(
        "/api/v1/datasets", files={"file": ("notes.txt", b"hello", "text/plain")}
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"
    assert response.json()["error"]["request_id"]


def test_rejects_malformed_json(client: TestClient) -> None:
    response = client.post(
        "/api/v1/datasets", files={"file": ("bad.json", b"{not-json}", "application/json")}
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MALFORMED_DATASET"


def test_rejects_oversized_upload(client: TestClient) -> None:
    response = client.post(
        "/api/v1/datasets", files={"file": ("large.csv", b"a\n" + (b"1\n" * 600), "text/csv")}
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"


def test_rejects_header_only_csv(client: TestClient) -> None:
    response = client.post(
        "/api/v1/datasets", files={"file": ("empty.csv", b"id,email\n", "text/csv")}
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "EMPTY_DATASET"


def test_returns_not_found_envelope(client: TestClient) -> None:
    response = client.get("/api/v1/datasets/not-a-real-id")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DATASET_NOT_FOUND"

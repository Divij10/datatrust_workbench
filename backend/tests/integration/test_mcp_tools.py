import asyncio

from fastapi.testclient import TestClient
from mcp import Client


def create_dataset(client: TestClient) -> str:
    response = client.post(
        "/api/v1/datasets",
        files={
            "file": (
                "people.csv",
                b"email,age\na@example.com,20\nbad,150\n",
                "text/csv",
            )
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_mcp_tools_delegate_to_the_running_application_services(client: TestClient) -> None:
    dataset_id = create_dataset(client)
    created = client.post(
        f"/api/v1/datasets/{dataset_id}/rules",
        json={"rule_type": "required", "column": "email", "description": "Email is required."},
    )
    assert created.status_code == 201, created.text
    approved = client.patch(f"/api/v1/rules/{created.json()['id']}", json={"status": "approved"})
    assert approved.status_code == 200, approved.text
    report = client.post(f"/api/v1/datasets/{dataset_id}/evaluate")
    assert report.status_code == 200, report.text

    async def call_tools() -> None:
        async with Client(client.app.state.mcp, raise_exceptions=True) as mcp_client:
            tools = await mcp_client.list_tools()
            assert {tool.name for tool in tools.tools} == {
                "profile_dataset",
                "get_quality_report",
                "validate_record",
                "suggest_quality_rules",
                "list_rules",
            }

            profile = await mcp_client.call_tool("profile_dataset", {"dataset_id": dataset_id})
            assert profile.is_error is False
            assert profile.structured_content == {
                "row_count": 2,
                "column_count": 2,
                "duplicate_row_count": 0,
                "columns": profile.structured_content["columns"],
            }

            validation = await mcp_client.call_tool(
                "validate_record", {"dataset_id": dataset_id, "record": {"email": None, "age": 24}}
            )
            assert validation.is_error is False
            assert validation.structured_content["total_violation_count"] == 1

            listed = await mcp_client.call_tool("list_rules", {"dataset_id": dataset_id})
            assert listed.is_error is False
            assert listed.structured_content["result"][0]["status"] == "approved"

            fetched = await mcp_client.call_tool(
                "get_quality_report", {"report_id": report.json()["id"]}
            )
            assert fetched.is_error is False
            assert fetched.structured_content["id"] == report.json()["id"]

            suggested = await mcp_client.call_tool(
                "suggest_quality_rules", {"dataset_id": dataset_id}
            )
            assert suggested.is_error is False
            suggestions = suggested.structured_content["result"]
            assert suggestions
            assert all(rule["status"] == "proposed" for rule in suggestions)

    asyncio.run(call_tools())

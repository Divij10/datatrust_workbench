from __future__ import annotations

from dataclasses import dataclass

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from starlette.applications import Starlette

from app.core.errors import DomainError
from app.domain.dataset import DatasetProfile
from app.domain.reports import QualityReport
from app.domain.rules import RuleEvaluationResult, RuleRecord
from app.services.dataset_service import DatasetService
from app.services.report_service import ReportService
from app.services.rule_service import RuleService


@dataclass(frozen=True)
class WorkbenchServices:
    """Explicit service bundle shared by REST handlers and MCP tools."""

    datasets: DatasetService
    rules: RuleService
    reports: ReportService


class WorkbenchServiceRegistry:
    """Holds the services for one running application instance."""

    def __init__(self) -> None:
        self._services: WorkbenchServices | None = None

    def configure(self, services: WorkbenchServices) -> None:
        self._services = services

    def require(self) -> WorkbenchServices:
        if self._services is None:
            raise ToolError("DataTrust Workbench is not ready. Start the application first.")
        return self._services


def _tool_error(error: DomainError) -> ToolError:
    return ToolError(f"{error.code}: {error.message}")


def create_mcp_server(registry: WorkbenchServiceRegistry) -> tuple[MCPServer, Starlette]:
    """Create an app-scoped MCP server and its ASGI transport.

    The MCP SDK's session manager is deliberately single-use. Creating one server per FastAPI
    application keeps startup/shutdown correct for development reloads and isolated tests.
    """
    mcp = MCPServer(
        "DataTrust Workbench",
        instructions=(
            "Use these tools to inspect datasets and deterministic data-quality results. "
            "AI suggestions remain proposed until a human approves them."
        ),
    )

    @mcp.tool(title="Profile dataset")
    def profile_dataset(dataset_id: str) -> DatasetProfile:
        """Return the deterministic schema and quality profile for one uploaded dataset."""
        try:
            return registry.require().datasets.get_profile(dataset_id)
        except DomainError as error:
            raise _tool_error(error) from error

    @mcp.tool(title="Get quality report")
    def get_quality_report(report_id: str) -> QualityReport:
        """Return one already-generated deterministic quality report."""
        try:
            return registry.require().reports.get_report(report_id)
        except DomainError as error:
            raise _tool_error(error) from error

    @mcp.tool(title="Validate record")
    def validate_record(
        dataset_id: str, record: dict[str, str | int | float | bool | None]
    ) -> RuleEvaluationResult:
        """Check a candidate record against approved rules and existing unique values."""
        try:
            return registry.require().reports.validate_record(dataset_id, record)
        except DomainError as error:
            raise _tool_error(error) from error

    @mcp.tool(title="Suggest quality rules")
    async def suggest_quality_rules(dataset_id: str) -> list[RuleRecord]:
        """Create validated AI-style candidates that still require human approval."""
        try:
            return await registry.require().rules.suggest_rules(dataset_id)
        except DomainError as error:
            raise _tool_error(error) from error

    @mcp.tool(title="List rules")
    def list_rules(dataset_id: str) -> list[RuleRecord]:
        """List the proposed, approved, rejected, or disabled rules for one dataset."""
        try:
            return registry.require().rules.list_rules(dataset_id)
        except DomainError as error:
            raise _tool_error(error) from error

    return mcp, mcp.streamable_http_app(streamable_http_path="/")

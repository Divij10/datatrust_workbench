import logging
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.adapters.llm.fake import FakeRuleGenerator
from app.adapters.repositories.memory import InMemoryDatasetRepository
from app.api.routes import datasets, health, reports, rules
from app.core.config import get_settings
from app.core.errors import DomainError
from app.core.logging import configure_logging
from app.domain.dataset import ErrorBody, ErrorResponse
from app.mcp.server import WorkbenchServiceRegistry, WorkbenchServices, create_mcp_server
from app.services.dataset_service import DatasetService
from app.services.profiler import DatasetProfiler
from app.services.quality_scorer import QualityScorer
from app.services.report_service import ReportService
from app.services.rule_engine import DeterministicRuleEngine
from app.services.rule_service import RuleService
from app.services.rule_validator import RuleSemanticValidator

logger = logging.getLogger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Any]]
    ) -> Any:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


def error_response(
    request: Request,
    code: str,
    message: str,
    status_code: int,
    details: dict[str, object] | None = None,
) -> JSONResponse:
    payload = ErrorResponse(
        error=ErrorBody(
            code=code,
            message=message,
            details=details or {},
            request_id=getattr(request.state, "request_id", "unknown"),
        )
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    app.state.settings = settings
    repository = InMemoryDatasetRepository()
    app.state.dataset_service = DatasetService(repository, DatasetProfiler(), settings)
    app.state.rule_service = RuleService(
        repository,
        RuleSemanticValidator(),
        FakeRuleGenerator(),
        settings.rule_generator_timeout_seconds,
    )
    app.state.report_service = ReportService(repository, DeterministicRuleEngine(), QualityScorer())
    app.state.mcp_registry.configure(
        WorkbenchServices(
            datasets=app.state.dataset_service,
            rules=app.state.rule_service,
            reports=app.state.report_service,
        )
    )
    async with app.state.mcp.session_manager.run():
        yield


def create_app() -> FastAPI:
    app = FastAPI(title="DataTrust Workbench", version="0.1.0", lifespan=lifespan)
    app.state.mcp_registry = WorkbenchServiceRegistry()
    app.state.mcp, mcp_app = create_mcp_server(app.state.mcp_registry)
    settings = get_settings()
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )
    app.include_router(health.router)
    app.include_router(datasets.router)
    app.include_router(rules.dataset_router)
    app.include_router(rules.rule_router)
    app.include_router(reports.evaluation_router)
    app.include_router(reports.report_router)
    app.mount("/mcp", mcp_app)

    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, error: DomainError) -> JSONResponse:
        return error_response(request, error.code, error.message, error.status_code, error.details)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        return error_response(
            request,
            "REQUEST_VALIDATION_FAILED",
            "The request is invalid.",
            422,
            {"errors": error.errors()},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, error: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled application error",
            extra={"request_id": getattr(request.state, "request_id", "unknown")},
        )
        return error_response(request, "INTERNAL_ERROR", "An unexpected error occurred.", 500)

    return app


app = create_app()

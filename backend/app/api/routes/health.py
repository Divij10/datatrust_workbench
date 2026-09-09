from fastapi import APIRouter, Request

from app.domain.dataset import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="datatrust-workbench",
        environment=request.app.state.settings.environment,
    )

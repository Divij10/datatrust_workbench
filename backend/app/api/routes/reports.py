from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.deps import get_report_service
from app.domain.reports import QualityReport
from app.services.report_service import ReportService

evaluation_router = APIRouter(prefix="/api/v1/datasets", tags=["reports"])
report_router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@evaluation_router.post("/{dataset_id}/evaluate", response_model=QualityReport)
def evaluate_dataset(
    dataset_id: str,
    service: ReportService = Depends(get_report_service),
) -> QualityReport:
    return service.evaluate_dataset(dataset_id)


@report_router.get("/{report_id}", response_model=QualityReport)
def get_report(
    report_id: str, service: ReportService = Depends(get_report_service)
) -> QualityReport:
    return service.get_report(report_id)


@report_router.get("/{report_id}/export")
def export_report(
    report_id: str, service: ReportService = Depends(get_report_service)
) -> JSONResponse:
    report = service.get_report(report_id)
    return JSONResponse(
        content=report.model_dump(mode="json"),
        headers={"Content-Disposition": f'attachment; filename="quality-report-{report.id}.json"'},
    )

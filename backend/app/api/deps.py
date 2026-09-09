from typing import cast

from fastapi import Request

from app.services.dataset_service import DatasetService
from app.services.report_service import ReportService
from app.services.rule_service import RuleService


def get_dataset_service(request: Request) -> DatasetService:
    return cast(DatasetService, request.app.state.dataset_service)


def get_rule_service(request: Request) -> RuleService:
    return cast(RuleService, request.app.state.rule_service)


def get_report_service(request: Request) -> ReportService:
    return cast(ReportService, request.app.state.report_service)

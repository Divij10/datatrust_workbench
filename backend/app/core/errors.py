from typing import Any


class DomainError(Exception):
    """Expected error that can be returned as a stable API error envelope."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class DatasetNotFoundError(DomainError):
    def __init__(self, dataset_id: str) -> None:
        super().__init__(
            "DATASET_NOT_FOUND",
            "The requested dataset does not exist.",
            404,
            {"dataset_id": dataset_id},
        )


class RuleNotFoundError(DomainError):
    def __init__(self, rule_id: str) -> None:
        super().__init__(
            "RULE_NOT_FOUND",
            "The requested rule does not exist.",
            404,
            {"rule_id": rule_id},
        )


class ReportNotFoundError(DomainError):
    def __init__(self, report_id: str) -> None:
        super().__init__(
            "REPORT_NOT_FOUND",
            "The requested report does not exist.",
            404,
            {"report_id": report_id},
        )

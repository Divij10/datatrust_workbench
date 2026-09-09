from dataclasses import dataclass

import pandas as pd

from app.core.errors import DatasetNotFoundError, ReportNotFoundError, RuleNotFoundError
from app.domain.dataset import DatasetDetail, DatasetMetadata
from app.domain.reports import QualityReport
from app.domain.rules import RuleRecord


@dataclass
class StoredDataset:
    detail: DatasetDetail
    frame: pd.DataFrame


class InMemoryDatasetRepository:
    """Development-only repository boundary; SQLite is introduced with rule persistence."""

    def __init__(self) -> None:
        self._datasets: dict[str, StoredDataset] = {}
        self._rules: dict[str, RuleRecord] = {}
        self._reports: dict[str, QualityReport] = {}

    def add(self, dataset: StoredDataset) -> None:
        self._datasets[dataset.detail.id] = dataset

    def get(self, dataset_id: str) -> StoredDataset:
        try:
            return self._datasets[dataset_id]
        except KeyError as error:
            raise DatasetNotFoundError(dataset_id) from error

    def metadata(self, dataset_id: str) -> DatasetMetadata:
        return DatasetMetadata.model_validate(
            self.get(dataset_id).detail.model_dump(exclude={"profile"})
        )

    def add_rule(self, rule: RuleRecord) -> None:
        self._rules[rule.id] = rule

    def get_rule(self, rule_id: str) -> RuleRecord:
        try:
            return self._rules[rule_id]
        except KeyError as error:
            raise RuleNotFoundError(rule_id) from error

    def update_rule(self, rule: RuleRecord) -> None:
        self.get_rule(rule.id)
        self._rules[rule.id] = rule

    def list_rules(self, dataset_id: str) -> list[RuleRecord]:
        self.get(dataset_id)
        return [rule for rule in self._rules.values() if rule.dataset_id == dataset_id]

    def add_report(self, report: QualityReport) -> None:
        self._reports[report.id] = report

    def get_report(self, report_id: str) -> QualityReport:
        try:
            return self._reports[report_id]
        except KeyError as error:
            raise ReportNotFoundError(report_id) from error

from datetime import UTC, datetime
from uuid import uuid4

from app.adapters.repositories.memory import InMemoryDatasetRepository
from app.core.errors import DomainError
from app.domain.enums import RuleStatus
from app.domain.reports import QualityReport
from app.domain.rules import (
    RuleEvaluationResult,
    RuleExecutionSummary,
    RuleValue,
    UniqueRule,
)
from app.services.quality_scorer import QualityScorer
from app.services.rule_engine import DeterministicRuleEngine


class ReportService:
    """Creates reproducible reports from approved rules and deterministic evaluations."""

    def __init__(
        self,
        repository: InMemoryDatasetRepository,
        engine: DeterministicRuleEngine,
        scorer: QualityScorer,
    ) -> None:
        self._repository = repository
        self._engine = engine
        self._scorer = scorer

    def evaluate_dataset(self, dataset_id: str) -> QualityReport:
        dataset = self._repository.get(dataset_id)
        approved = [
            rule
            for rule in self._repository.list_rules(dataset_id)
            if rule.status == RuleStatus.APPROVED
        ]
        results = self._engine.evaluate(dataset.frame, approved)
        score, dimensions = self._scorer.score(results, approved)
        report = QualityReport(
            id=str(uuid4()),
            dataset_id=dataset_id,
            created_at=datetime.now(UTC),
            evaluated_rule_count=len(results),
            total_violation_count=sum(result.violation_count for result in results),
            results=results,
            quality_score=score,
            dimensions=dimensions,
        )
        self._repository.add_report(report)
        return report

    def get_report(self, report_id: str) -> QualityReport:
        return self._repository.get_report(report_id)

    def validate_record(
        self, dataset_id: str, record: dict[str, RuleValue | None]
    ) -> RuleEvaluationResult:
        """Evaluate an incoming record with the same engine used for full-dataset reports.

        Unique rules compare the candidate to the existing dataset. Other rule types are evaluated
        against a one-row frame, so every returned violation belongs to the candidate record.
        """
        dataset = self._repository.get(dataset_id)
        unknown_columns = sorted(set(record).difference(dataset.frame.columns))
        if unknown_columns:
            raise DomainError(
                "UNKNOWN_RECORD_COLUMNS",
                "The record contains columns that are not present in the dataset.",
                400,
                {"columns": unknown_columns},
            )
        candidate = dataset.frame.iloc[0:0].copy()
        candidate.loc[0] = {column: record.get(str(column)) for column in candidate.columns}
        approved = [
            rule
            for rule in self._repository.list_rules(dataset_id)
            if rule.status == RuleStatus.APPROVED
        ]
        results: list[RuleExecutionSummary] = []
        for rule in approved:
            if isinstance(rule.rule, UniqueRule):
                augmented = dataset.frame.copy()
                candidate_index = len(augmented.index)
                augmented.loc[candidate_index] = candidate.loc[0]
                summary = self._engine.evaluate_rule(augmented, rule)
                violations = [
                    violation.model_copy(update={"row_index": 0})
                    for violation in summary.violations
                    if violation.row_index == candidate_index
                ]
                results.append(
                    RuleExecutionSummary(
                        rule_id=summary.rule_id,
                        rule_type=summary.rule_type,
                        checked_count=1,
                        violation_count=len(violations),
                        violations=violations,
                    )
                )
            else:
                results.append(self._engine.evaluate_rule(candidate, rule))
        return RuleEvaluationResult(
            dataset_id=dataset_id,
            evaluated_rule_count=len(results),
            total_violation_count=sum(result.violation_count for result in results),
            results=results,
        )

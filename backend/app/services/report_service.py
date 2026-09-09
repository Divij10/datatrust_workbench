from datetime import UTC, datetime
from uuid import uuid4

from app.adapters.repositories.memory import InMemoryDatasetRepository
from app.domain.enums import RuleStatus
from app.domain.reports import QualityReport
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

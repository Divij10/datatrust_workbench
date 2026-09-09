from collections.abc import Iterable

from app.domain.reports import QualityDimension, QualityDimensions
from app.domain.rules import RuleExecutionSummary, RuleRecord

WEIGHTS = {
    "completeness": 0.35,
    "validity": 0.30,
    "uniqueness": 0.20,
    "consistency": 0.15,
}


class QualityScorer:
    """Calculates a documented portfolio metric, not an industry-standard universal score."""

    def score(
        self,
        results: Iterable[RuleExecutionSummary],
        rules: Iterable[RuleRecord],
    ) -> tuple[float | None, QualityDimensions]:
        records_by_id = {record.id: record for record in rules}
        grouped: dict[str, list[RuleExecutionSummary]] = {
            "completeness": [],
            "validity": [],
            "uniqueness": [],
            "consistency": [],
        }
        for result in results:
            rule_type = records_by_id[result.rule_id].rule.rule_type
            grouped[self._dimension_for(rule_type)].append(result)

        dimensions = QualityDimensions(
            **{name: self._dimension(items) for name, items in grouped.items()}
        )
        applicable_weights = {
            name: weight for name, weight in WEIGHTS.items() if getattr(dimensions, name).applicable
        }
        if not applicable_weights:
            return None, dimensions
        total_weight = sum(applicable_weights.values())
        value = sum(
            (getattr(dimensions, name).score or 0) * (weight / total_weight)
            for name, weight in applicable_weights.items()
        )
        return round(value, 2), dimensions

    @staticmethod
    def _dimension(results: list[RuleExecutionSummary]) -> QualityDimension:
        checked = sum(result.checked_count for result in results)
        passed = sum(result.checked_count - result.violation_count for result in results)
        return QualityDimension(
            score=round((passed / checked) * 100, 2) if checked else None,
            applicable=checked > 0,
            checks_evaluated=checked,
            checks_passing=passed,
        )

    @staticmethod
    def _dimension_for(rule_type: str) -> str:
        if rule_type == "required":
            return "completeness"
        if rule_type == "unique":
            return "uniqueness"
        if rule_type == "allowed_values":
            return "consistency"
        return "validity"

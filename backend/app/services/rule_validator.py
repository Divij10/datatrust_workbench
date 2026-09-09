from collections.abc import Iterable

from app.core.errors import DomainError
from app.domain.dataset import DatasetProfile, InferredType
from app.domain.rules import (
    EmailRule,
    MaximumRule,
    MinimumRule,
    PatternRule,
    RangeRule,
    Rule,
    RuleRecord,
    StringLengthRule,
)


class RuleSemanticValidator:
    """Rejects valid-shaped rules that do not make sense for this dataset."""

    def validate(
        self, rule: Rule, profile: DatasetProfile, existing_rules: Iterable[RuleRecord]
    ) -> None:
        column = next((item for item in profile.columns if item.name == rule.column), None)
        if column is None:
            raise DomainError(
                "RULE_SEMANTIC_VALIDATION_FAILED",
                "The rule references an unknown column.",
                400,
                {"column": rule.column},
            )
        if not self._compatible(rule, column.inferred_type):
            raise DomainError(
                "RULE_SEMANTIC_VALIDATION_FAILED",
                "The rule is not compatible with the inferred column type.",
                400,
                {
                    "column": rule.column,
                    "inferred_type": column.inferred_type,
                    "rule_type": rule.rule_type,
                },
            )
        signature = self._signature(rule)
        if any(self._signature(record.rule) == signature for record in existing_rules):
            raise DomainError(
                "DUPLICATE_RULE",
                "An equivalent rule already exists for this dataset.",
                400,
                {"column": rule.column, "rule_type": rule.rule_type},
            )

    @staticmethod
    def _compatible(rule: Rule, inferred_type: InferredType) -> bool:
        if isinstance(rule, RangeRule | MinimumRule | MaximumRule):
            return inferred_type in {"integer", "number"}
        if isinstance(rule, PatternRule | EmailRule | StringLengthRule):
            return inferred_type == "string"
        return True

    @staticmethod
    def _signature(rule: Rule) -> tuple[tuple[str, object], ...]:
        fields = rule.model_dump(exclude={"description", "severity"}, mode="json")
        for key, value in list(fields.items()):
            if isinstance(value, list):
                fields[key] = tuple(value)
        return tuple(sorted(fields.items()))

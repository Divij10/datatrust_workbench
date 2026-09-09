from __future__ import annotations

import re
from numbers import Integral, Real
from typing import Any

import pandas as pd

from app.domain.rules import (
    AllowedValuesRule,
    EmailRule,
    MaximumRule,
    MinimumRule,
    PatternRule,
    RangeRule,
    RequiredRule,
    Rule,
    RuleExecutionSummary,
    RuleRecord,
    RuleViolation,
    StringLengthRule,
    UniqueRule,
)

SAFE_PATTERNS: dict[str, re.Pattern[str]] = {
    "alphanumeric_code": re.compile(r"[A-Za-z0-9]+"),
    "us_state_code": re.compile(r"[A-Z]{2}"),
    "zip5": re.compile(r"\d{5}"),
}
EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


class DeterministicRuleEngine:
    """Evaluates finite, validated rules; it never evaluates user/model code or raw patterns."""

    def evaluate(self, frame: pd.DataFrame, rules: list[RuleRecord]) -> list[RuleExecutionSummary]:
        return [self.evaluate_rule(frame, record) for record in rules]

    def evaluate_rule(self, frame: pd.DataFrame, record: RuleRecord) -> RuleExecutionSummary:
        series = frame[record.rule.column]
        failure_mask = self._failure_mask(series, record.rule)
        violations = [
            RuleViolation(
                row_index=int(index),
                column=record.rule.column,
                rule_id=record.id,
                rule_type=record.rule.rule_type,
                severity=record.rule.severity,
                observed_value=self._display_value(series.loc[index]),
                message=self._message(record.rule),
            )
            for index in series.index[failure_mask]
        ]
        return RuleExecutionSummary(
            rule_id=record.id,
            rule_type=record.rule.rule_type,
            checked_count=self._checked_count(series, record.rule),
            violation_count=len(violations),
            violations=violations,
        )

    @staticmethod
    def _checked_count(series: pd.Series[Any], rule: Rule) -> int:
        if isinstance(rule, RequiredRule):
            return len(series.index)
        return int(series.notna().sum())

    def _failure_mask(self, series: pd.Series[Any], rule: Rule) -> pd.Series[bool]:
        missing = series.isna()
        if isinstance(rule, RequiredRule):
            return missing | series.map(lambda value: isinstance(value, str) and not value.strip())
        if isinstance(rule, UniqueRule):
            return series.notna() & series.duplicated(keep=False)
        if isinstance(rule, RangeRule):
            numeric = pd.to_numeric(series, errors="coerce")
            return series.notna() & (~numeric.between(rule.min_value, rule.max_value))
        if isinstance(rule, MinimumRule):
            numeric = pd.to_numeric(series, errors="coerce")
            return series.notna() & (numeric < rule.value)
        if isinstance(rule, MaximumRule):
            numeric = pd.to_numeric(series, errors="coerce")
            return series.notna() & (numeric > rule.value)
        if isinstance(rule, AllowedValuesRule):
            return series.notna() & ~series.isin(rule.values)
        if isinstance(rule, PatternRule):
            return series.notna() & ~series.astype(str).str.fullmatch(
                SAFE_PATTERNS[rule.pattern_id]
            )
        if isinstance(rule, EmailRule):
            return series.notna() & ~series.astype(str).str.fullmatch(EMAIL_PATTERN)
        if isinstance(rule, StringLengthRule):
            lengths = series.astype(str).str.len()
            failures = pd.Series(False, index=series.index)
            if rule.min_length is not None:
                failures |= lengths < rule.min_length
            if rule.max_length is not None:
                failures |= lengths > rule.max_length
            return series.notna() & failures
        raise TypeError(f"Unsupported rule type: {rule.rule_type}")

    @staticmethod
    def _display_value(value: Any) -> str | int | float | bool | None:
        if pd.isna(value):
            return None
        if isinstance(value, bool | str):
            return value
        if isinstance(value, Integral):
            return int(value)
        if isinstance(value, Real):
            return float(value)
        return str(value)

    @staticmethod
    def _message(rule: Rule) -> str:
        return rule.description

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.enums import RuleSource, RuleStatus, Severity

type RuleValue = str | int | float | bool
PatternId = Literal["alphanumeric_code", "us_state_code", "zip5"]


class RuleBase(BaseModel):
    """Fields shared by all finite, non-executable quality rules."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    column: str = Field(min_length=1, max_length=128)
    severity: Severity = Severity.WARNING
    description: str = Field(min_length=1, max_length=240)


class RequiredRule(RuleBase):
    rule_type: Literal["required"]


class UniqueRule(RuleBase):
    rule_type: Literal["unique"]


class RangeRule(RuleBase):
    rule_type: Literal["range"]
    min_value: float
    max_value: float

    @model_validator(mode="after")
    def validate_range(self) -> RangeRule:
        if self.min_value >= self.max_value:
            raise ValueError("min_value must be less than max_value")
        return self


class MinimumRule(RuleBase):
    rule_type: Literal["minimum"]
    value: float


class MaximumRule(RuleBase):
    rule_type: Literal["maximum"]
    value: float


class AllowedValuesRule(RuleBase):
    rule_type: Literal["allowed_values"]
    values: list[RuleValue] = Field(min_length=1, max_length=100)


class PatternRule(RuleBase):
    rule_type: Literal["pattern"]
    pattern_id: PatternId


class EmailRule(RuleBase):
    rule_type: Literal["email"]


class StringLengthRule(RuleBase):
    rule_type: Literal["string_length"]
    min_length: int | None = Field(default=None, ge=0)
    max_length: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_lengths(self) -> StringLengthRule:
        if self.min_length is None and self.max_length is None:
            raise ValueError("at least one of min_length or max_length is required")
        if (
            self.min_length is not None
            and self.max_length is not None
            and self.min_length > self.max_length
        ):
            raise ValueError("min_length must not exceed max_length")
        return self


type Rule = Annotated[
    RequiredRule
    | UniqueRule
    | RangeRule
    | MinimumRule
    | MaximumRule
    | AllowedValuesRule
    | PatternRule
    | EmailRule
    | StringLengthRule,
    Field(discriminator="rule_type"),
]


class RuleAuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    occurred_at: datetime
    from_status: RuleStatus | None
    to_status: RuleStatus
    source: RuleSource
    rationale: str | None = Field(default=None, max_length=240)


class RuleRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    dataset_id: str
    status: RuleStatus
    source: RuleSource
    created_at: datetime
    rule: Rule
    audit_events: list[RuleAuditEvent] = Field(default_factory=list)


class UpdateRuleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    status: Literal["approved", "rejected", "disabled"]
    rationale: str | None = Field(default=None, max_length=240)


class RuleViolation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    row_index: int
    column: str
    rule_id: str
    rule_type: str
    severity: Severity
    observed_value: RuleValue | None
    message: str


class RuleExecutionSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str
    rule_type: str
    checked_count: int = Field(ge=0)
    violation_count: int = Field(ge=0)
    violations: list[RuleViolation]


class RuleEvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    evaluated_rule_count: int = Field(ge=0)
    total_violation_count: int = Field(ge=0)
    results: list[RuleExecutionSummary]

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.rules import RuleEvaluationResult


class QualityDimension(BaseModel):
    """A transparent quality-score component; null means no applicable checks ran."""

    model_config = ConfigDict(extra="forbid")

    score: float | None = Field(default=None, ge=0, le=100)
    applicable: bool
    checks_evaluated: int = Field(ge=0)
    checks_passing: int = Field(ge=0)


class QualityDimensions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    completeness: QualityDimension
    validity: QualityDimension
    uniqueness: QualityDimension
    consistency: QualityDimension


class QualityReport(RuleEvaluationResult):
    id: str
    created_at: datetime
    quality_score: float | None = Field(default=None, ge=0, le=100)
    dimensions: QualityDimensions

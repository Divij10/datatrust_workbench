from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

InferredType = Literal["boolean", "integer", "number", "datetime", "string", "unknown"]


class ColumnProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    inferred_type: InferredType
    null_count: int = Field(ge=0)
    null_rate: float = Field(ge=0, le=1)
    distinct_count: int = Field(ge=0)
    distinct_rate: float = Field(ge=0, le=1)
    is_unique: bool
    sample_values: list[str | int | float | bool] = Field(default_factory=list)
    min_value: float | None = None
    max_value: float | None = None
    mean: float | None = None
    median: float | None = None
    min_length: int | None = None
    max_length: int | None = None
    top_values: list["ValueCount"] = Field(default_factory=list)


class ValueCount(BaseModel):
    value: str | int | float | bool
    count: int = Field(ge=1)


class DatasetProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    row_count: int = Field(ge=0)
    column_count: int = Field(ge=0)
    duplicate_row_count: int = Field(ge=0)
    columns: list[ColumnProfile]


class DatasetMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    filename: str
    file_type: Literal["csv", "json"]
    size_bytes: int = Field(ge=0)
    created_at: datetime
    row_count: int = Field(ge=0)
    column_count: int = Field(ge=0)


class DatasetDetail(DatasetMetadata):
    profile: DatasetProfile


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    environment: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, object] = Field(default_factory=dict)
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorBody

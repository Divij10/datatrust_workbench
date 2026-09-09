from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_float_dtype,
    is_integer_dtype,
    is_numeric_dtype,
)

from app.domain.dataset import ColumnProfile, DatasetProfile, InferredType, ValueCount


class DatasetProfiler:
    """Computes reproducible, bounded summaries without applying business rules."""

    def profile(self, frame: pd.DataFrame) -> DatasetProfile:
        row_count = len(frame.index)
        columns = [
            self._profile_column(str(name), frame.iloc[:, index], row_count)
            for index, name in enumerate(frame.columns)
        ]
        return DatasetProfile(
            row_count=row_count,
            column_count=len(frame.columns),
            duplicate_row_count=int(frame.duplicated().sum()),
            columns=columns,
        )

    def _profile_column(self, name: str, series: pd.Series[Any], row_count: int) -> ColumnProfile:
        non_null = series.dropna()
        null_count = int(series.isna().sum())
        distinct_count = int(non_null.nunique())
        inferred_type = self._infer_type(series, non_null)
        common = non_null.value_counts(dropna=True).head(5)
        profile = ColumnProfile(
            name=name,
            inferred_type=inferred_type,
            null_count=null_count,
            null_rate=self._rate(null_count, row_count),
            distinct_count=distinct_count,
            distinct_rate=self._rate(distinct_count, row_count),
            is_unique=row_count > 0 and null_count == 0 and distinct_count == row_count,
            sample_values=self._display_values(non_null.head(5)),
            top_values=[
                ValueCount(value=self._display_value(value), count=int(count))
                for value, count in common.items()
            ],
        )
        if inferred_type in {"integer", "number"} and not non_null.empty:
            numeric = pd.to_numeric(non_null, errors="coerce").dropna()
            if not numeric.empty:
                profile.min_value = float(numeric.min())
                profile.max_value = float(numeric.max())
                profile.mean = float(numeric.mean())
                profile.median = float(numeric.median())
        if inferred_type == "string" and not non_null.empty:
            lengths = non_null.astype(str).str.len()
            profile.min_length = int(lengths.min())
            profile.max_length = int(lengths.max())
        return profile

    @staticmethod
    def _rate(count: int, total: int) -> float:
        return round(count / total, 6) if total else 0.0

    @staticmethod
    def _infer_type(series: pd.Series[Any], non_null: pd.Series[Any]) -> InferredType:
        if non_null.empty:
            return "unknown"
        if is_bool_dtype(series):
            return "boolean"
        if is_integer_dtype(series):
            return "integer"
        if is_float_dtype(series) or is_numeric_dtype(series):
            return "number"
        if is_datetime64_any_dtype(series):
            return "datetime"
        return "string"

    @classmethod
    def _display_values(cls, values: Iterable[Any]) -> list[str | int | float | bool]:
        return [cls._display_value(value) for value in values]

    @staticmethod
    def _display_value(value: Any) -> str | int | float | bool:
        if isinstance(value, bool | int | float | str):
            return value
        return str(value)

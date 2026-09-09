import pandas as pd

from app.services.profiler import DatasetProfiler


def test_profile_calculates_deterministic_column_summaries() -> None:
    frame = pd.DataFrame(
        {
            "age": [20, None, 40, 20],
            "state": ["AZ", "AZ", "CA", "AZ"],
        }
    )

    profile = DatasetProfiler().profile(frame)

    assert profile.row_count == 4
    assert profile.column_count == 2
    assert profile.duplicate_row_count == 1
    age = profile.columns[0]
    assert age.inferred_type == "number"
    assert age.null_count == 1
    assert age.null_rate == 0.25
    assert age.distinct_count == 2
    assert age.min_value == 20.0
    assert age.max_value == 40.0
    assert age.mean == 26.666666666666668
    state = profile.columns[1]
    assert state.inferred_type == "string"
    assert state.top_values[0].value == "AZ"
    assert state.top_values[0].count == 3


def test_profile_reports_duplicate_rows_and_empty_column_values() -> None:
    frame = pd.DataFrame({"id": [1, 1], "empty": [None, None]})

    profile = DatasetProfiler().profile(frame)

    assert profile.duplicate_row_count == 1
    assert profile.columns[1].inferred_type == "unknown"
    assert profile.columns[1].null_rate == 1.0
    assert profile.columns[1].sample_values == []

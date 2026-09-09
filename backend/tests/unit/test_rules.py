from datetime import UTC, datetime

import pandas as pd
import pytest
from pydantic import TypeAdapter, ValidationError

from app.domain.enums import RuleSource, RuleStatus
from app.domain.rules import Rule, RuleRecord
from app.services.rule_engine import DeterministicRuleEngine

RULE_ADAPTER = TypeAdapter(Rule)


def record(payload: dict[str, object], rule_id: str = "rule-1") -> RuleRecord:
    return RuleRecord(
        id=rule_id,
        dataset_id="dataset-1",
        status=RuleStatus.APPROVED,
        source=RuleSource.HUMAN,
        created_at=datetime.now(UTC),
        rule=RULE_ADAPTER.validate_python(payload),
    )


def failures(frame: pd.DataFrame, payload: dict[str, object]) -> list[int]:
    result = DeterministicRuleEngine().evaluate_rule(frame, record(payload))
    return [item.row_index for item in result.violations]


def test_rule_model_rejects_invalid_range_and_unbounded_length() -> None:
    with pytest.raises(ValidationError, match="min_value must be less"):
        RULE_ADAPTER.validate_python(
            {
                "rule_type": "range",
                "column": "age",
                "min_value": 10,
                "max_value": 10,
                "description": "Age range",
            }
        )
    with pytest.raises(ValidationError, match="at least one"):
        RULE_ADAPTER.validate_python(
            {"rule_type": "string_length", "column": "name", "description": "Name length"}
        )


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (
            {"rule_type": "required", "column": "name", "description": "Name required"},
            [1, 2],
        ),
        (
            {"rule_type": "unique", "column": "customer_id", "description": "ID unique"},
            [0, 1],
        ),
        (
            {
                "rule_type": "range",
                "column": "age",
                "min_value": 0,
                "max_value": 120,
                "description": "Age range",
            },
            [1, 2],
        ),
        (
            {"rule_type": "minimum", "column": "age", "value": 0, "description": "Age minimum"},
            [1],
        ),
        (
            {"rule_type": "maximum", "column": "age", "value": 120, "description": "Age maximum"},
            [2],
        ),
        (
            {
                "rule_type": "allowed_values",
                "column": "state",
                "values": ["AZ", "CA"],
                "description": "Supported state",
            },
            [2],
        ),
        (
            {
                "rule_type": "pattern",
                "column": "code",
                "pattern_id": "alphanumeric_code",
                "description": "Alphanumeric code",
            },
            [1],
        ),
        (
            {"rule_type": "email", "column": "email", "description": "Email address"},
            [1],
        ),
        (
            {
                "rule_type": "string_length",
                "column": "code",
                "min_length": 2,
                "max_length": 3,
                "description": "Code length",
            },
            [1, 2],
        ),
    ],
)
def test_engine_evaluates_every_supported_rule_type(
    payload: dict[str, object], expected: list[int]
) -> None:
    frame = pd.DataFrame(
        {
            "name": ["Ada", "", None, "Lin"],
            "customer_id": [1, 1, 2, None],
            "age": [20, -1, 121, None],
            "state": ["AZ", "CA", "ZZ", None],
            "code": ["A12", "bad code", "X", None],
            "email": ["ada@example.com", "not-email", None, "lin@example.com"],
        }
    )

    assert failures(frame, payload) == expected


def test_engine_returns_human_readable_row_evidence() -> None:
    frame = pd.DataFrame({"age": [20, 140]})
    result = DeterministicRuleEngine().evaluate_rule(
        frame,
        record(
            {
                "rule_type": "maximum",
                "column": "age",
                "value": 120,
                "severity": "critical",
                "description": "Age must be at most 120.",
            },
            rule_id="age-maximum",
        ),
    )

    assert result.violation_count == 1
    assert result.violations[0].model_dump() == {
        "row_index": 1,
        "column": "age",
        "rule_id": "age-maximum",
        "rule_type": "maximum",
        "severity": "critical",
        "observed_value": 140,
        "message": "Age must be at most 120.",
    }

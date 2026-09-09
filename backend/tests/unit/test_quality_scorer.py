from datetime import UTC, datetime

from pydantic import TypeAdapter

from app.domain.enums import RuleSource, RuleStatus
from app.domain.rules import Rule, RuleExecutionSummary, RuleRecord
from app.services.quality_scorer import QualityScorer

RULE_ADAPTER = TypeAdapter(Rule)


def rule_record(rule_id: str, payload: dict[str, object]) -> RuleRecord:
    return RuleRecord(
        id=rule_id,
        dataset_id="dataset-1",
        status=RuleStatus.APPROVED,
        source=RuleSource.HUMAN,
        created_at=datetime.now(UTC),
        rule=RULE_ADAPTER.validate_python(payload),
    )


def result(rule_id: str, rule_type: str, checked: int, violations: int) -> RuleExecutionSummary:
    return RuleExecutionSummary(
        rule_id=rule_id,
        rule_type=rule_type,
        checked_count=checked,
        violation_count=violations,
        violations=[],
    )


def test_quality_score_uses_documented_dimension_weights() -> None:
    rules = [
        rule_record(
            "required", {"rule_type": "required", "column": "name", "description": "Required"}
        ),
        rule_record(
            "range",
            {
                "rule_type": "range",
                "column": "age",
                "min_value": 0,
                "max_value": 120,
                "description": "Range",
            },
        ),
        rule_record("unique", {"rule_type": "unique", "column": "id", "description": "Unique"}),
        rule_record(
            "allowed",
            {
                "rule_type": "allowed_values",
                "column": "state",
                "values": ["AZ", "CA"],
                "description": "Allowed",
            },
        ),
    ]
    results = [
        result("required", "required", 3, 1),
        result("range", "range", 3, 1),
        result("unique", "unique", 3, 2),
        result("allowed", "allowed_values", 3, 1),
    ]

    score, dimensions = QualityScorer().score(results, rules)

    assert score == 60.0
    assert dimensions.completeness.score == 66.67
    assert dimensions.validity.score == 66.67
    assert dimensions.uniqueness.score == 33.33
    assert dimensions.consistency.score == 66.67


def test_quality_score_renormalizes_when_dimensions_are_not_applicable() -> None:
    rules = [
        rule_record(
            "range",
            {
                "rule_type": "range",
                "column": "age",
                "min_value": 0,
                "max_value": 120,
                "description": "Range",
            },
        )
    ]

    score, dimensions = QualityScorer().score([result("range", "range", 2, 1)], rules)

    assert score == 50.0
    assert dimensions.validity.applicable is True
    assert dimensions.completeness.score is None
    assert dimensions.uniqueness.score is None
    assert dimensions.consistency.score is None


def test_quality_score_is_not_perfect_when_no_rules_are_approved() -> None:
    score, dimensions = QualityScorer().score([], [])

    assert score is None
    assert dimensions.validity.applicable is False

from collections.abc import Mapping
from typing import Any

from app.domain.dataset import DatasetProfile


class FakeRuleGenerator:
    """Deterministic demo provider. It never sends dataset contents to a third party."""

    async def generate_rules(self, profile: DatasetProfile) -> Mapping[str, Any]:
        rules: list[dict[str, Any]] = []
        for column in profile.columns:
            lowered = column.name.lower()
            if column.null_count > 0:
                rules.append(
                    {
                        "rule_type": "required",
                        "column": column.name,
                        "severity": "warning",
                        "description": f"{column.name} should be present for every record.",
                    }
                )
            if lowered in {"email", "email_address"} and column.inferred_type == "string":
                rules.append(
                    {
                        "rule_type": "email",
                        "column": column.name,
                        "severity": "warning",
                        "description": f"{column.name} should use email address syntax.",
                    }
                )
            if lowered in {"age", "customer_age"} and column.inferred_type in {"integer", "number"}:
                rules.append(
                    {
                        "rule_type": "range",
                        "column": column.name,
                        "min_value": 0,
                        "max_value": 120,
                        "severity": "warning",
                        "description": f"{column.name} should be between 0 and 120.",
                    }
                )
            if lowered in {"state", "us_state"} and column.inferred_type == "string":
                rules.append(
                    {
                        "rule_type": "pattern",
                        "column": column.name,
                        "pattern_id": "us_state_code",
                        "severity": "warning",
                        "description": f"{column.name} should use a two-letter US state code.",
                    }
                )
            if lowered.endswith("_id") and column.is_unique:
                rules.append(
                    {
                        "rule_type": "unique",
                        "column": column.name,
                        "severity": "warning",
                        "description": f"{column.name} should uniquely identify a record.",
                    }
                )
        return {
            "rules": rules[:12],
            "explanation": "Suggestions use deterministic schema and profile signals.",
        }

from datetime import UTC, datetime
from uuid import uuid4

from app.adapters.repositories.memory import InMemoryDatasetRepository
from app.core.errors import DomainError
from app.domain.enums import RuleSource, RuleStatus
from app.domain.rules import (
    Rule,
    RuleAuditEvent,
    RuleRecord,
    UpdateRuleRequest,
)
from app.services.rule_validator import RuleSemanticValidator


class RuleService:
    """Coordinates rule lifecycle while preserving the human approval gate."""

    def __init__(
        self,
        repository: InMemoryDatasetRepository,
        validator: RuleSemanticValidator,
    ) -> None:
        self._repository = repository
        self._validator = validator

    def create_human_rule(self, dataset_id: str, rule: Rule) -> RuleRecord:
        dataset = self._repository.get(dataset_id)
        self._validator.validate(
            rule, dataset.detail.profile, self._repository.list_rules(dataset_id)
        )
        now = datetime.now(UTC)
        record = RuleRecord(
            id=str(uuid4()),
            dataset_id=dataset_id,
            status=RuleStatus.PROPOSED,
            source=RuleSource.HUMAN,
            created_at=now,
            rule=rule,
            audit_events=[
                RuleAuditEvent(
                    occurred_at=now,
                    from_status=None,
                    to_status=RuleStatus.PROPOSED,
                    source=RuleSource.HUMAN,
                    rationale="Human-authored rule created for review.",
                )
            ],
        )
        self._repository.add_rule(record)
        return record

    def list_rules(
        self,
        dataset_id: str,
        status: RuleStatus | None = None,
        source: RuleSource | None = None,
    ) -> list[RuleRecord]:
        records = self._repository.list_rules(dataset_id)
        return [
            record
            for record in records
            if (status is None or record.status == status)
            and (source is None or record.source == source)
        ]

    def update_rule(self, rule_id: str, update: UpdateRuleRequest) -> RuleRecord:
        record = self._repository.get_rule(rule_id)
        requested_status = RuleStatus(update.status)
        if record.status == requested_status:
            raise DomainError(
                "INVALID_RULE_TRANSITION",
                "The rule is already in the requested status.",
                400,
                {"rule_id": rule_id, "status": requested_status},
            )
        if (
            record.status in {RuleStatus.REJECTED, RuleStatus.DISABLED}
            and requested_status == RuleStatus.APPROVED
        ):
            raise DomainError(
                "INVALID_RULE_TRANSITION",
                "Rejected or disabled rules cannot be approved without creating a new rule.",
                400,
                {"rule_id": rule_id, "from_status": record.status, "to_status": requested_status},
            )
        event = RuleAuditEvent(
            occurred_at=datetime.now(UTC),
            from_status=record.status,
            to_status=requested_status,
            source=record.source,
            rationale=update.rationale,
        )
        updated = record.model_copy(
            update={"status": requested_status, "audit_events": [*record.audit_events, event]}
        )
        self._repository.update_rule(updated)
        return updated

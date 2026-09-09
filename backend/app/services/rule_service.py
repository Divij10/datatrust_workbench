import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from pydantic import ValidationError

from app.adapters.llm.base import RuleGenerator
from app.adapters.repositories.memory import InMemoryDatasetRepository
from app.core.errors import DomainError
from app.domain.dataset import DatasetProfile
from app.domain.enums import RuleSource, RuleStatus
from app.domain.rules import (
    Rule,
    RuleAuditEvent,
    RuleRecord,
    RuleSuggestionBatch,
    UpdateRuleRequest,
)
from app.services.rule_validator import RuleSemanticValidator


class RuleService:
    """Coordinates rule lifecycle while preserving the human approval gate."""

    def __init__(
        self,
        repository: InMemoryDatasetRepository,
        validator: RuleSemanticValidator,
        generator: RuleGenerator,
        generator_timeout_seconds: float,
    ) -> None:
        self._repository = repository
        self._validator = validator
        self._generator = generator
        self._generator_timeout_seconds = generator_timeout_seconds

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

    async def suggest_rules(self, dataset_id: str) -> list[RuleRecord]:
        dataset = self._repository.get(dataset_id)
        raw_response = await self._generate(dataset.detail.profile)
        try:
            batch = RuleSuggestionBatch.model_validate(raw_response)
        except ValidationError as error:
            raise DomainError(
                "LLM_OUTPUT_VALIDATION_FAILED",
                "The rule provider returned an invalid structured response.",
                400,
                {"errors": error.errors()},
            ) from error

        existing = self._repository.list_rules(dataset_id)
        candidates: list[RuleRecord] = []
        now = datetime.now(UTC)
        for rule in batch.rules:
            self._validator.validate(
                rule,
                dataset.detail.profile,
                [*existing, *candidates],
            )
            candidate = RuleRecord(
                id=str(uuid4()),
                dataset_id=dataset_id,
                status=RuleStatus.PROPOSED,
                source=RuleSource.AI,
                created_at=now,
                rule=rule,
                audit_events=[
                    RuleAuditEvent(
                        occurred_at=now,
                        from_status=None,
                        to_status=RuleStatus.PROPOSED,
                        source=RuleSource.AI,
                        rationale=batch.explanation,
                    )
                ],
            )
            candidates.append(candidate)
        for candidate in candidates:
            self._repository.add_rule(candidate)
        return candidates

    async def _generate(self, profile: DatasetProfile) -> object:
        try:
            return await asyncio.wait_for(
                self._generator.generate_rules(profile),
                timeout=self._generator_timeout_seconds,
            )
        except TimeoutError as error:
            raise DomainError(
                "LLM_PROVIDER_UNAVAILABLE",
                "The rule provider timed out. Please try again later.",
                503,
            ) from error
        except Exception as error:
            raise DomainError(
                "LLM_PROVIDER_UNAVAILABLE",
                "The rule provider is temporarily unavailable.",
                503,
            ) from error

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

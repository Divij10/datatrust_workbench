from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_rule_service
from app.domain.enums import RuleSource, RuleStatus
from app.domain.rules import Rule, RuleRecord, UpdateRuleRequest
from app.services.rule_service import RuleService

dataset_router = APIRouter(prefix="/api/v1/datasets/{dataset_id}/rules", tags=["rules"])
rule_router = APIRouter(prefix="/api/v1/rules", tags=["rules"])


@dataset_router.post("", response_model=RuleRecord, status_code=status.HTTP_201_CREATED)
def create_rule(
    dataset_id: str,
    rule: Rule,
    service: RuleService = Depends(get_rule_service),
) -> RuleRecord:
    return service.create_human_rule(dataset_id, rule)


@dataset_router.get("", response_model=list[RuleRecord])
def list_rules(
    dataset_id: str,
    status_filter: RuleStatus | None = Query(default=None, alias="status"),
    source: RuleSource | None = None,
    service: RuleService = Depends(get_rule_service),
) -> list[RuleRecord]:
    return service.list_rules(dataset_id, status_filter, source)


@dataset_router.post("/suggest", response_model=list[RuleRecord])
async def suggest_rules(
    dataset_id: str,
    service: RuleService = Depends(get_rule_service),
) -> list[RuleRecord]:
    return await service.suggest_rules(dataset_id)


@rule_router.patch("/{rule_id}", response_model=RuleRecord)
def update_rule(
    rule_id: str,
    update: UpdateRuleRequest,
    service: RuleService = Depends(get_rule_service),
) -> RuleRecord:
    return service.update_rule(rule_id, update)

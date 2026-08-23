"""REST controller for the Reasoning Workspace (Sprint 12).

GET  /decisions/{decision_id}/reasoning-workspace     - assemble Decision + DecisionContext + originating/active drafts + Assumptions + CaseConditions
POST /decision-drafts/{draft_id}/commit-with-reasoning - commit a draft, optionally creating Assumptions/CaseConditions
GET  /cases/{case_id}/reasoning/active-assumptions      - read model
GET  /cases/{case_id}/reasoning/active-case-conditions  - read model
GET  /reasoning/open-decision-drafts                    - read model (userId query param)

No dedicated `errors.py` for this router, deliberately: every
exception `ReasoningWorkspaceService` can raise originates from
`DecisionDraftService`, `AssumptionService`, or `CaseConditionService`
directly (it introduces none of its own), and each already has an
app-wide handler registered — nothing here needs a new one.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query

from atlas.core.application.assumption.assumption_service import AssumptionContent
from atlas.core.application.case_condition.case_condition_service import CaseConditionContent
from atlas.core.application.reasoning_workspace.read_models import (
    list_active_assumptions,
    list_active_case_conditions,
    list_open_decision_drafts,
)
from atlas.core.application.reasoning_workspace.reasoning_workspace_service import (
    AssumptionWithLinkedConditions,
    ReasoningWorkspaceService,
)
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.value_objects import DecisionId, UserId
from atlas.core.domain.decision_draft.value_objects import DraftId
from atlas.core.infrastructure.api.assumption.dependencies import get_assumption_service
from atlas.core.infrastructure.api.case_condition.dependencies import get_case_condition_service
from atlas.core.infrastructure.api.decision_draft.dependencies import get_decision_draft_service
from atlas.core.infrastructure.api.reasoning_workspace.dependencies import (
    get_reasoning_workspace_service,
)
from atlas.core.infrastructure.api.reasoning_workspace.schemas import (
    ActiveAssumptionRowResponse,
    ActiveCaseConditionRowResponse,
    CommitDraftWithReasoningRequest,
    CommitDraftWithReasoningResponse,
    DecisionReasoningWorkspaceResponse,
    OpenDecisionDraftRowResponse,
)

router = APIRouter(tags=["reasoning-workspace"])


def _condition_content(payload) -> CaseConditionContent:
    return CaseConditionContent(
        predicate_text=payload.predicate_text,
        role=payload.role,
        authorship=payload.authorship,
        structured_kind=payload.structured_kind,
        threshold_date=payload.threshold_date,
        threshold_metric=payload.threshold_metric,
        threshold_operator=payload.threshold_operator,
        threshold_value=payload.threshold_value,
    )


@router.get(
    "/decisions/{decision_id}/reasoning-workspace", response_model=DecisionReasoningWorkspaceResponse
)
def get_decision_reasoning_workspace(
    decision_id: uuid.UUID,
    service: ReasoningWorkspaceService = Depends(get_reasoning_workspace_service),
) -> DecisionReasoningWorkspaceResponse:
    workspace = service.load_workspace(DecisionId(decision_id))
    return DecisionReasoningWorkspaceResponse.from_domain(workspace)


@router.post(
    "/decision-drafts/{draft_id}/commit-with-reasoning",
    response_model=CommitDraftWithReasoningResponse,
)
def commit_draft_with_reasoning(
    draft_id: uuid.UUID,
    payload: CommitDraftWithReasoningRequest,
    service: ReasoningWorkspaceService = Depends(get_reasoning_workspace_service),
) -> CommitDraftWithReasoningResponse:
    assumptions = tuple(
        AssumptionWithLinkedConditions(
            content=AssumptionContent(statement=item.statement, authorship=item.authorship),
            linked_condition_contents=tuple(
                _condition_content(condition) for condition in item.linked_conditions
            ),
        )
        for item in payload.assumptions
    )
    standalone_conditions = tuple(
        _condition_content(condition) for condition in payload.standalone_case_conditions
    )
    result = service.commit_draft_with_reasoning(
        DraftId(draft_id),
        assumptions=assumptions,
        standalone_case_condition_contents=standalone_conditions,
    )
    return CommitDraftWithReasoningResponse.from_domain(result)


@router.get(
    "/cases/{case_id}/reasoning/active-assumptions", response_model=list[ActiveAssumptionRowResponse]
)
def get_active_assumptions(
    case_id: uuid.UUID,
    assumption_service=Depends(get_assumption_service),
) -> list[ActiveAssumptionRowResponse]:
    rows = list_active_assumptions(assumption_service, CaseId(case_id))
    return [ActiveAssumptionRowResponse.from_domain(row) for row in rows]


@router.get(
    "/cases/{case_id}/reasoning/active-case-conditions",
    response_model=list[ActiveCaseConditionRowResponse],
)
def get_active_case_conditions(
    case_id: uuid.UUID,
    case_condition_service=Depends(get_case_condition_service),
) -> list[ActiveCaseConditionRowResponse]:
    rows = list_active_case_conditions(case_condition_service, CaseId(case_id))
    return [ActiveCaseConditionRowResponse.from_domain(row) for row in rows]


@router.get(
    "/reasoning/open-decision-drafts", response_model=list[OpenDecisionDraftRowResponse]
)
def get_open_decision_drafts(
    user_id: uuid.UUID = Query(alias="userId"),
    draft_service=Depends(get_decision_draft_service),
) -> list[OpenDecisionDraftRowResponse]:
    rows = list_open_decision_drafts(draft_service, UserId(user_id))
    return [OpenDecisionDraftRowResponse.from_domain(row) for row in rows]

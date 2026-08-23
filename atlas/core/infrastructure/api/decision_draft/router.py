"""REST controller for DecisionDraft (ADR-DD-001).

POST   /cases/{case_id}/decision-drafts              - create a new draft
GET    /cases/{case_id}/decision-drafts              - list every Active draft for a Case
GET    /decision-drafts/daily-brief-summary           - the narrow Daily Brief projection (ADR-DD-001 §4)
GET    /decision-drafts/{draft_id}                    - read one draft's current state
GET    /decision-drafts/{draft_id}/events              - full event history for one draft
PATCH  /decision-drafts/{draft_id}                    - revise a draft's content
POST   /decision-drafts/{draft_id}/abandon             - abandon/discard a draft (idempotent)
POST   /decision-drafts/{draft_id}/commit              - commit a draft into a real Decision

`/decision-drafts/daily-brief-summary` is registered before
`/decision-drafts/{draft_id}` deliberately — FastAPI matches routes in
registration order, and a static segment must precede a competing
path-parameter route for `"daily-brief-summary"` to never be parsed as
a `draft_id`.

No request body on commit (see `schemas.py`'s own docstring reasoning,
`DecisionDraft-Implementation-Design.md` §6.2): commit uses exactly
whatever the draft's own latest revision already holds.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Response

from atlas.core.application.decision_draft.decision_draft_service import (
    DecisionDraftContent,
    DecisionDraftService,
)
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.value_objects import UserId
from atlas.core.domain.decision_draft.value_objects import DraftId
from atlas.core.infrastructure.api.decision_draft.dependencies import get_decision_draft_service
from atlas.core.infrastructure.api.decision_draft.schemas import (
    CommitDecisionDraftResponse,
    CreateDecisionDraftRequest,
    DecisionDraftResponse,
    DecisionDraftSummaryResponse,
    ReviseDecisionDraftRequest,
)
from atlas.core.infrastructure.api.decision.schemas import DecisionSummary
from atlas.core.infrastructure.api.decision_context.schemas import DecisionContextResponse

router = APIRouter(tags=["decision-drafts"])


def _content_from_create(payload: CreateDecisionDraftRequest) -> DecisionDraftContent:
    return DecisionDraftContent(
        decision_type=payload.decision_type,
        subject=payload.subject,
        reason=payload.reason,
        confidence=payload.confidence,
        decided_at=payload.decided_at,
        source=payload.source,
        situation=payload.situation,
        portfolio_relevance=payload.portfolio_relevance,
        capital_considerations=payload.capital_considerations,
        alternatives_considered=tuple(payload.alternatives_considered),
        uncertainties=tuple(payload.uncertainties),
    )


def _content_from_revise(payload: ReviseDecisionDraftRequest) -> DecisionDraftContent:
    return DecisionDraftContent(
        decision_type=payload.decision_type,
        subject=payload.subject,
        reason=payload.reason,
        confidence=payload.confidence,
        decided_at=payload.decided_at,
        source=payload.source,
        situation=payload.situation,
        portfolio_relevance=payload.portfolio_relevance,
        capital_considerations=payload.capital_considerations,
        alternatives_considered=tuple(payload.alternatives_considered),
        uncertainties=tuple(payload.uncertainties),
    )


@router.post(
    "/cases/{case_id}/decision-drafts", response_model=DecisionDraftResponse, status_code=201
)
def create_decision_draft(
    case_id: uuid.UUID,
    payload: CreateDecisionDraftRequest,
    service: DecisionDraftService = Depends(get_decision_draft_service),
) -> DecisionDraftResponse:
    view = service.create(
        case_id=CaseId(case_id),
        user_id=UserId(payload.user_id),
        content=_content_from_create(payload),
    )
    return DecisionDraftResponse.from_domain(view)


@router.get(
    "/cases/{case_id}/decision-drafts", response_model=list[DecisionDraftResponse]
)
def list_decision_drafts_for_case(
    case_id: uuid.UUID,
    service: DecisionDraftService = Depends(get_decision_draft_service),
) -> list[DecisionDraftResponse]:
    views = service.list_active_for_case(CaseId(case_id))
    return [DecisionDraftResponse.from_domain(view) for view in views]


@router.get(
    "/decision-drafts/daily-brief-summary", response_model=list[DecisionDraftSummaryResponse]
)
def get_daily_brief_draft_summary(
    user_id: uuid.UUID = Query(alias="userId"),
    service: DecisionDraftService = Depends(get_decision_draft_service),
) -> list[DecisionDraftSummaryResponse]:
    summaries = service.daily_brief_summary(UserId(user_id))
    return [
        DecisionDraftSummaryResponse(
            draft_id=summary.draft_id.value,
            case_id=summary.case_id.value,
            subject=summary.subject,
            created_at=summary.created_at,
        )
        for summary in summaries
    ]


@router.get("/decision-drafts/{draft_id}", response_model=DecisionDraftResponse)
def get_decision_draft(
    draft_id: uuid.UUID,
    service: DecisionDraftService = Depends(get_decision_draft_service),
) -> DecisionDraftResponse:
    view = service.get(DraftId(draft_id))
    return DecisionDraftResponse.from_domain(view)


@router.get("/decision-drafts/{draft_id}/events")
def list_decision_draft_events(
    draft_id: uuid.UUID,
    service: DecisionDraftService = Depends(get_decision_draft_service),
) -> list[dict]:
    events = service.list_events(DraftId(draft_id))
    return [
        {
            "id": event.id,
            "eventType": event.event_type,
            "recordedAt": event.recorded_at.isoformat(),
            "committedDecisionId": event.committed_decision_id,
        }
        for event in events
    ]


@router.patch("/decision-drafts/{draft_id}", response_model=DecisionDraftResponse)
def revise_decision_draft(
    draft_id: uuid.UUID,
    payload: ReviseDecisionDraftRequest,
    service: DecisionDraftService = Depends(get_decision_draft_service),
) -> DecisionDraftResponse:
    view = service.revise(
        DraftId(draft_id),
        content=_content_from_revise(payload),
        expected_latest_event_id=payload.expected_latest_event_id,
    )
    return DecisionDraftResponse.from_domain(view)


@router.post("/decision-drafts/{draft_id}/abandon", status_code=204, response_class=Response)
def abandon_decision_draft(
    draft_id: uuid.UUID,
    service: DecisionDraftService = Depends(get_decision_draft_service),
) -> Response:
    service.abandon(DraftId(draft_id))
    return Response(status_code=204)


@router.post("/decision-drafts/{draft_id}/commit", response_model=CommitDecisionDraftResponse)
def commit_decision_draft(
    draft_id: uuid.UUID,
    service: DecisionDraftService = Depends(get_decision_draft_service),
) -> CommitDecisionDraftResponse:
    result = service.commit(DraftId(draft_id))
    return CommitDecisionDraftResponse(
        decision=DecisionSummary.from_domain(result.decision),
        decision_context=(
            DecisionContextResponse.from_domain(result.decision_context)
            if result.decision_context is not None
            else None
        ),
        draft=DecisionDraftResponse.from_domain(result.draft),
    )

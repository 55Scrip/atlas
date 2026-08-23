"""HTTP request/response schemas for DecisionDraft (ADR-DD-001).

CamelCase via the shared `CamelModel` (ADR-004), matching every other
schema module under `atlas/core/infrastructure/api/`.

`DecisionSummary` (`decision/schemas.py`) and `DecisionContextResponse`
(`decision_context/schemas.py`) are reused directly, unmodified, in
`CommitDecisionDraftResponse` — see
`DecisionDraft-Implementation-Design.md` §6.3.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from atlas.core.domain.decision_draft.entity import DecisionDraftView
from atlas.core.infrastructure.api.decision.schemas import DecisionSummary
from atlas.core.infrastructure.api.decision_context.schemas import DecisionContextResponse
from atlas.core.infrastructure.api.serialization import CamelModel


class CreateDecisionDraftRequest(CamelModel):
    user_id: uuid.UUID
    decision_type: str | None = None
    subject: str | None = None
    reason: str | None = None
    confidence: int | None = None
    decided_at: datetime | None = None
    source: str | None = None
    situation: str | None = None
    portfolio_relevance: str | None = None
    capital_considerations: str | None = None
    alternatives_considered: list[str] = []
    uncertainties: list[str] = []


class ReviseDecisionDraftRequest(CamelModel):
    decision_type: str | None = None
    subject: str | None = None
    reason: str | None = None
    confidence: int | None = None
    decided_at: datetime | None = None
    source: str | None = None
    situation: str | None = None
    portfolio_relevance: str | None = None
    capital_considerations: str | None = None
    alternatives_considered: list[str] = []
    uncertainties: list[str] = []
    expected_latest_event_id: str | None = None


class DecisionDraftResponse(CamelModel):
    draft_id: uuid.UUID
    case_id: uuid.UUID
    user_id: uuid.UUID
    status: Literal["active", "abandoned", "committed"]
    decision_type: str | None
    subject: str | None
    reason: str | None
    confidence: int | None
    decided_at: datetime | None
    source: str | None
    situation: str | None
    portfolio_relevance: str | None
    capital_considerations: str | None
    alternatives_considered: list[str]
    uncertainties: list[str]
    committed_decision_id: uuid.UUID | None
    latest_event_id: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, view: DecisionDraftView) -> DecisionDraftResponse:
        return cls(
            draft_id=view.draft_id.value,
            case_id=view.case_id.value,
            user_id=view.user_id.value,
            status=view.status,
            decision_type=view.decision_type,
            subject=view.subject,
            reason=view.reason,
            confidence=view.confidence,
            decided_at=view.decided_at,
            source=view.source,
            situation=view.situation,
            portfolio_relevance=view.portfolio_relevance,
            capital_considerations=view.capital_considerations,
            alternatives_considered=list(view.alternatives_considered),
            uncertainties=list(view.uncertainties),
            committed_decision_id=(
                uuid.UUID(view.committed_decision_id)
                if view.committed_decision_id is not None
                else None
            ),
            latest_event_id=view.latest_event_id,
            created_at=view.created_at,
            updated_at=view.updated_at,
        )


class DecisionDraftSummaryResponse(CamelModel):
    """The narrow, ADR-DD-001 §4-conformant Daily Brief projection —
    never a full-content field."""

    draft_id: uuid.UUID
    case_id: uuid.UUID
    subject: str | None
    created_at: datetime


class CommitDecisionDraftResponse(CamelModel):
    decision: DecisionSummary
    decision_context: DecisionContextResponse | None
    draft: DecisionDraftResponse

"""HTTP request/response schemas for the Reasoning Workspace (Sprint 12).

CamelCase via the shared `CamelModel` (ADR-004). Every response field
reuses an existing, already-shipped response schema directly
(`DecisionSummary`, `DecisionContextResponse`, `DecisionDraftResponse`,
`AssumptionResponse`, `CaseConditionResponse`) rather than redefining
an equivalent shape — the same "reuse existing DTO conventions"
instruction Sprint 12 §4 states explicitly, and the identical choice
`decision_draft/schemas.py`'s own `CommitDecisionDraftResponse` already
made for `Decision`/`DecisionContext` (Sprint 9).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from atlas.core.application.reasoning_workspace.reasoning_workspace_service import (
    DecisionReasoningWorkspace,
    DraftCommitWithReasoningResult,
)
from atlas.core.application.reasoning_workspace.read_models import (
    ActiveAssumptionRow,
    ActiveCaseConditionRow,
    OpenDecisionDraftRow,
)
from atlas.core.infrastructure.api.assumption.schemas import AssumptionResponse
from atlas.core.infrastructure.api.case_condition.schemas import CaseConditionResponse
from atlas.core.infrastructure.api.decision.schemas import DecisionSummary
from atlas.core.infrastructure.api.decision_context.schemas import DecisionContextResponse
from atlas.core.infrastructure.api.decision_draft.schemas import DecisionDraftResponse
from atlas.core.infrastructure.api.serialization import CamelModel


class DecisionReasoningWorkspaceResponse(CamelModel):
    decision: DecisionSummary
    decision_context: DecisionContextResponse | None
    originating_draft: DecisionDraftResponse | None
    active_case_drafts: list[DecisionDraftResponse]
    assumptions: list[AssumptionResponse]
    case_conditions: list[CaseConditionResponse]

    @classmethod
    def from_domain(cls, workspace: DecisionReasoningWorkspace) -> DecisionReasoningWorkspaceResponse:
        return cls(
            decision=DecisionSummary.from_domain(workspace.decision),
            decision_context=(
                DecisionContextResponse.from_domain(workspace.decision_context)
                if workspace.decision_context is not None
                else None
            ),
            originating_draft=(
                DecisionDraftResponse.from_domain(workspace.originating_draft)
                if workspace.originating_draft is not None
                else None
            ),
            active_case_drafts=[
                DecisionDraftResponse.from_domain(draft) for draft in workspace.active_case_drafts
            ],
            assumptions=[AssumptionResponse.from_domain(view) for view in workspace.assumptions],
            case_conditions=[
                CaseConditionResponse.from_domain(view) for view in workspace.case_conditions
            ],
        )


class LinkedCaseConditionRequest(CamelModel):
    predicate_text: str | None = None
    role: Literal["monitoring", "invalidation"] | None = None
    authorship: Literal["atlas", "user", "mixed"] | None = None
    structured_kind: Literal["date", "threshold"] | None = None
    threshold_date: datetime | None = None
    threshold_metric: str | None = None
    threshold_operator: Literal["<", "<=", ">", ">=", "==", "!="] | None = None
    threshold_value: float | None = None


class AssumptionWithLinkedConditionsRequest(CamelModel):
    statement: str | None = None
    authorship: Literal["atlas", "user", "mixed"] | None = None
    linked_conditions: list[LinkedCaseConditionRequest] = []


class CommitDraftWithReasoningRequest(CamelModel):
    assumptions: list[AssumptionWithLinkedConditionsRequest] = []
    standalone_case_conditions: list[LinkedCaseConditionRequest] = []


class CommitDraftWithReasoningResponse(CamelModel):
    decision: DecisionSummary
    decision_context: DecisionContextResponse | None
    draft: DecisionDraftResponse
    assumptions: list[AssumptionResponse]
    case_conditions: list[CaseConditionResponse]

    @classmethod
    def from_domain(
        cls, result: DraftCommitWithReasoningResult
    ) -> CommitDraftWithReasoningResponse:
        return cls(
            decision=DecisionSummary.from_domain(result.decision),
            decision_context=(
                DecisionContextResponse.from_domain(result.decision_context)
                if result.decision_context is not None
                else None
            ),
            draft=DecisionDraftResponse.from_domain(result.draft),
            assumptions=[AssumptionResponse.from_domain(view) for view in result.assumptions],
            case_conditions=[
                CaseConditionResponse.from_domain(view) for view in result.case_conditions
            ],
        )


class ActiveAssumptionRowResponse(CamelModel):
    assumption_id: uuid.UUID
    decision_id: uuid.UUID
    case_id: uuid.UUID
    statement: str | None
    status: Literal["supported", "challenged", "invalidated", "superseded", "retired"]

    @classmethod
    def from_domain(cls, row: ActiveAssumptionRow) -> ActiveAssumptionRowResponse:
        return cls(
            assumption_id=row.assumption_id.value,
            decision_id=row.decision_id.value,
            case_id=row.case_id.value,
            statement=row.statement,
            status=row.status,
        )


class ActiveCaseConditionRowResponse(CamelModel):
    condition_id: uuid.UUID
    case_id: uuid.UUID
    decision_id: uuid.UUID | None
    predicate_text: str | None
    role: Literal["monitoring", "invalidation"] | None
    status: Literal["active", "satisfied", "superseded", "retired"]

    @classmethod
    def from_domain(cls, row: ActiveCaseConditionRow) -> ActiveCaseConditionRowResponse:
        return cls(
            condition_id=row.condition_id.value,
            case_id=row.case_id.value,
            decision_id=row.decision_id.value if row.decision_id is not None else None,
            predicate_text=row.predicate_text,
            role=row.role,
            status=row.status,
        )


class OpenDecisionDraftRowResponse(CamelModel):
    draft_id: uuid.UUID
    case_id: uuid.UUID
    subject: str | None
    created_at: datetime

    @classmethod
    def from_domain(cls, row: OpenDecisionDraftRow) -> OpenDecisionDraftRowResponse:
        return cls(
            draft_id=row.draft_id.value,
            case_id=row.case_id.value,
            subject=row.subject,
            created_at=row.created_at,
        )

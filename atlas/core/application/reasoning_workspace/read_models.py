"""Read projections for the reasoning workspace (Sprint 12 §3).

Every function here is a thin, read-only composition over an existing
application service's own already-shipped listing method — no new
repository query, no new domain logic, no persistence of its own. This
is the read side of CQRS in the narrowest possible sense: a projection
*of* already-derived state, not a second source of it. "Decision
Workspace" itself is not repeated here — that projection is
`ReasoningWorkspaceService.load_workspace`, in
`reasoning_workspace_service.py`; this module covers the three
remaining, Case-or-portfolio-scoped read models Sprint 12 §3 names.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.core.application.assumption.assumption_service import AssumptionService
from atlas.core.application.case_condition.case_condition_service import CaseConditionService
from atlas.core.application.decision_draft.decision_draft_service import DecisionDraftService
from atlas.core.domain.assumption.entity import AssumptionStatus
from atlas.core.domain.assumption.value_objects import AssumptionId
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.case_condition.entity import CaseConditionRole, CaseConditionStatus
from atlas.core.domain.case_condition.value_objects import CaseConditionId
from atlas.core.domain.decision.value_objects import DecisionId, UserId
from atlas.core.domain.decision_draft.value_objects import DraftId


@dataclass(frozen=True)
class ActiveAssumptionRow:
    """A narrow, list-view projection over `AssumptionView` — no full
    challenge history, no linked-condition detail, matching the same
    narrow-projection discipline `ADR-DD-001` §4/`ADR-CC-001` §8
    already establish for their own Daily-Brief-facing projections."""

    assumption_id: AssumptionId
    decision_id: DecisionId
    case_id: CaseId
    statement: str | None
    status: AssumptionStatus
    updated_at: datetime
    """Fix Sprint 4 (Daily Brief Signal Quality) -- `AssumptionView
    .updated_at` was already computed by `reconstruct_current_state`
    (the timestamp of the event that produced this Assumption's
    current `status`) but this projection previously dropped it. Real,
    already-derived data, not a new computation: composed here so
    Daily Brief can honestly distinguish "just became challenged/
    invalidated" from "has stood challenged for weeks," rather than
    inventing a second timestamp source."""


@dataclass(frozen=True)
class ActiveCaseConditionRow:
    condition_id: CaseConditionId
    case_id: CaseId
    decision_id: DecisionId | None
    predicate_text: str | None
    role: CaseConditionRole | None
    status: CaseConditionStatus
    updated_at: datetime
    """Fix Sprint 4 (Daily Brief Signal Quality) -- identical reasoning
    to `ActiveAssumptionRow.updated_at` above, sourced from
    `CaseConditionView.updated_at` (already computed by that module's
    own `reconstruct_current_state`)."""


@dataclass(frozen=True)
class OpenDecisionDraftRow:
    draft_id: DraftId
    case_id: CaseId
    subject: str | None
    created_at: datetime


def list_active_assumptions(
    assumption_service: AssumptionService, case_id: CaseId
) -> list[ActiveAssumptionRow]:
    """Reuses `AssumptionService.list_for_case`, whose own default
    (`include_terminal=False`) already excludes `retired`/`superseded`
    assumptions — "active" here means exactly that default."""
    views = assumption_service.list_for_case(case_id)
    return [
        ActiveAssumptionRow(
            assumption_id=view.assumption_id,
            decision_id=view.decision_id,
            case_id=view.case_id,
            statement=view.statement,
            status=view.status,
            updated_at=view.updated_at,
        )
        for view in views
    ]


def list_active_case_conditions(
    case_condition_service: CaseConditionService, case_id: CaseId
) -> list[ActiveCaseConditionRow]:
    """Reuses `CaseConditionService.list_for_case`, whose own default
    (`include_terminal=False`) already excludes `retired`/`superseded`
    conditions."""
    views = case_condition_service.list_for_case(case_id)
    return [
        ActiveCaseConditionRow(
            condition_id=view.condition_id,
            case_id=view.case_id,
            decision_id=view.decision_id,
            predicate_text=view.predicate_text,
            role=view.role,
            status=view.status,
            updated_at=view.updated_at,
        )
        for view in views
    ]


def list_open_decision_drafts(
    draft_service: DecisionDraftService, user_id: UserId
) -> list[OpenDecisionDraftRow]:
    """Reuses `DecisionDraftService.daily_brief_summary` directly — the
    exact narrow projection ADR-DD-001 §4 already mandates ("existence,
    subject, and a resume link — never full draft content"). This
    function does not recompute that projection; it re-exposes it under
    the reasoning-workspace's own read-model naming."""
    summaries = draft_service.daily_brief_summary(user_id)
    return [
        OpenDecisionDraftRow(
            draft_id=summary.draft_id,
            case_id=summary.case_id,
            subject=summary.subject,
            created_at=summary.created_at,
        )
        for summary in summaries
    ]

"""Composition wiring for the Reasoning Workspace API.

Composes the sibling aggregates' own already-existing dependency
providers directly — one physical `atlas.db` file, no new repository
type. `ReasoningWorkspaceService` itself is new (Sprint 12); every
repository and service it is built from is not.
"""
from __future__ import annotations

from fastapi import Depends

from atlas.core.application.assumption.assumption_service import AssumptionService
from atlas.core.application.case_condition.case_condition_service import CaseConditionService
from atlas.core.application.decision_draft.decision_draft_service import DecisionDraftService
from atlas.core.application.reasoning_workspace.reasoning_workspace_service import (
    ReasoningWorkspaceService,
)
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.decision_context.repository import DecisionContextRepository
from atlas.core.domain.decision_draft.repository import DecisionDraftEventRepository
from atlas.core.infrastructure.api.assumption.dependencies import get_assumption_service
from atlas.core.infrastructure.api.case_condition.dependencies import get_case_condition_service
from atlas.core.infrastructure.api.decision.dependencies import get_decision_repository
from atlas.core.infrastructure.api.decision_context.dependencies import (
    get_decision_context_repository,
)
from atlas.core.infrastructure.api.decision_draft.dependencies import (
    get_decision_draft_repository,
    get_decision_draft_service,
)


def get_reasoning_workspace_service(
    decision_repository: DecisionRepository = Depends(get_decision_repository),
    decision_context_repository: DecisionContextRepository = Depends(
        get_decision_context_repository
    ),
    draft_repository: DecisionDraftEventRepository = Depends(get_decision_draft_repository),
    draft_service: DecisionDraftService = Depends(get_decision_draft_service),
    assumption_service: AssumptionService = Depends(get_assumption_service),
    case_condition_service: CaseConditionService = Depends(get_case_condition_service),
) -> ReasoningWorkspaceService:
    return ReasoningWorkspaceService(
        decision_repository,
        decision_context_repository,
        draft_repository,
        draft_service,
        assumption_service,
        case_condition_service,
    )

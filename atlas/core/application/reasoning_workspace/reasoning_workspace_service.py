"""`ReasoningWorkspaceService` — orchestrates `Decision`,
`DecisionContext`, `DecisionDraft`, `Assumption`, and `CaseCondition`
into two workflows (Sprint 12):

- `load_workspace(decision_id)` — read-only composition of everything
  reachable from one `Decision` ("Decision Commit Integration" and
  "Reasoning Workspace Service" deliverables).
- `commit_draft_with_reasoning(draft_id, ...)` — the extended commit
  flow: commits a `DecisionDraft` via the existing, unmodified
  `DecisionDraftService.commit()`, then optionally creates `Assumption`s
  and `CaseCondition`s (optionally linked to those Assumptions) via the
  existing, unmodified `AssumptionService.create()`/
  `.attach_case_condition()` and `CaseConditionService.create()`.

**No new aggregate ownership.** Every write in this file is a call to
`DecisionDraftService`, `AssumptionService`, or `CaseConditionService`'s
own already-shipped public method — none of their own construction
logic, validation, or event-append code is reimplemented or bypassed
here. This service owns nothing itself; every object it returns is
already owned by, and fully governed by, its own existing aggregate.
Reads that need a shape none of those three services' own methods
directly provide (see `_find_originating_draft`) go through the
sibling repository directly, read-only — the same pattern
`AssumptionService` itself already established for reading
`CaseConditionEventRepository` (Sprint 11).
"""
from __future__ import annotations

from dataclasses import dataclass

from atlas.core.application.assumption.assumption_service import (
    AssumptionContent,
    AssumptionService,
)
from atlas.core.application.case_condition.case_condition_service import (
    CaseConditionContent,
    CaseConditionService,
)
from atlas.core.application.decision_draft.decision_draft_service import DecisionDraftService
from atlas.core.domain.assumption.entity import AssumptionView
from atlas.core.domain.case_condition.entity import CaseConditionView
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.decision_context.entity import DecisionContext
from atlas.core.domain.decision_context.repository import DecisionContextRepository
from atlas.core.domain.decision_context.exceptions import (
    DecisionNotFoundError as DecisionContextDecisionNotFoundError,
)
from atlas.core.domain.decision_draft.entity import DecisionDraftView
from atlas.core.domain.decision_draft.repository import DecisionDraftEventRepository
from atlas.core.domain.decision_draft.value_objects import DraftId


@dataclass(frozen=True)
class DecisionReasoningWorkspace:
    """The complete, read-only reasoning state assembled around one
    `Decision`. Every field is a reference to an already-existing,
    independently-owned object — this dataclass merges nothing and
    persists nowhere; it is recomputed fresh on every `load_workspace`
    call, the same "derive, don't store" discipline every read
    projection in this codebase already follows."""

    decision: Decision
    decision_context: DecisionContext | None
    originating_draft: DecisionDraftView | None
    active_case_drafts: tuple[DecisionDraftView, ...]
    assumptions: tuple[AssumptionView, ...]
    case_conditions: tuple[CaseConditionView, ...]


@dataclass(frozen=True)
class AssumptionWithLinkedConditions:
    """One assumption to create at commit time, plus zero or more
    CaseConditions to create and attach to it — the concrete shape
    "Assumptions [and] linked CaseConditions" (Sprint 12 §1) takes."""

    content: AssumptionContent
    linked_condition_contents: tuple[CaseConditionContent, ...] = ()


@dataclass(frozen=True)
class DraftCommitWithReasoningResult:
    decision: Decision
    decision_context: DecisionContext | None
    draft: DecisionDraftView
    assumptions: tuple[AssumptionView, ...]
    case_conditions: tuple[CaseConditionView, ...]


class ReasoningWorkspaceService:
    def __init__(
        self,
        decision_repository: DecisionRepository,
        decision_context_repository: DecisionContextRepository,
        draft_repository: DecisionDraftEventRepository,
        draft_service: DecisionDraftService,
        assumption_service: AssumptionService,
        case_condition_service: CaseConditionService,
    ) -> None:
        self._decisions = decision_repository
        self._decision_contexts = decision_context_repository
        self._draft_repository = draft_repository
        self._drafts = draft_service
        self._assumptions = assumption_service
        self._case_conditions = case_condition_service

    def load_workspace(self, decision_id: DecisionId) -> DecisionReasoningWorkspace:
        decision = self._decisions.get(decision_id)
        if decision is None:
            raise DecisionContextDecisionNotFoundError(f"No Decision found with id {decision_id}")

        decision_context = self._decision_contexts.get_by_decision_id(decision_id)
        originating_draft = self._find_originating_draft(decision)
        active_case_drafts = tuple(self._drafts.list_active_for_case(decision.case_id))
        assumptions = tuple(self._assumptions.list_for_decision(decision_id))
        case_conditions = tuple(self._case_conditions.list_for_decision(decision_id))

        return DecisionReasoningWorkspace(
            decision=decision,
            decision_context=decision_context,
            originating_draft=originating_draft,
            active_case_drafts=active_case_drafts,
            assumptions=assumptions,
            case_conditions=case_conditions,
        )

    def commit_draft_with_reasoning(
        self,
        draft_id: DraftId,
        *,
        assumptions: tuple[AssumptionWithLinkedConditions, ...] = (),
        standalone_case_condition_contents: tuple[CaseConditionContent, ...] = (),
    ) -> DraftCommitWithReasoningResult:
        """Commits the draft exactly as `DecisionDraftService.commit()`
        already does (ADR-DD-001 §3's own commit boundary, unmodified),
        then optionally creates each requested `Assumption` (and any
        `CaseCondition`s it should be linked to) and each requested
        standalone `CaseCondition`, all anchored to the resulting
        Decision via its own real `decision_id` — never a fabricated
        or provisional one."""
        commit_result = self._drafts.commit(draft_id)
        decision = commit_result.decision

        created_assumptions: list[AssumptionView] = []
        created_conditions: list[CaseConditionView] = []

        for assumption_spec in assumptions:
            assumption_view = self._assumptions.create(
                decision_id=decision.id, content=assumption_spec.content
            )
            created_assumptions.append(assumption_view)
            for condition_content in assumption_spec.linked_condition_contents:
                condition_view = self._case_conditions.create(
                    case_id=decision.case_id,
                    decision_id=decision.id,
                    content=condition_content,
                )
                created_conditions.append(condition_view)
                assumption_view = self._assumptions.attach_case_condition(
                    assumption_view.assumption_id, condition_view.condition_id
                )
                created_assumptions[-1] = assumption_view

        for condition_content in standalone_case_condition_contents:
            created_conditions.append(
                self._case_conditions.create(
                    case_id=decision.case_id, decision_id=decision.id, content=condition_content
                )
            )

        return DraftCommitWithReasoningResult(
            decision=decision,
            decision_context=commit_result.decision_context,
            draft=commit_result.draft,
            assumptions=tuple(created_assumptions),
            case_conditions=tuple(created_conditions),
        )

    def _find_originating_draft(self, decision: Decision) -> DecisionDraftView | None:
        """No existing repository method answers "which draft, if any,
        became this Decision" directly (`DecisionDraftEventRepository`
        has no `get_by_committed_decision_id`), so this reads
        `list_latest_by_case` directly — the same read-only,
        sibling-repository pattern `AssumptionService` already uses for
        `CaseConditionEventRepository` (Sprint 11) — and scans for the
        one `"committed"` event naming this Decision.
        """
        latest_events = self._draft_repository.list_latest_by_case(decision.case_id)
        match = next(
            (
                event
                for event in latest_events
                if event.event_type == "committed"
                and event.committed_decision_id == str(decision.id.value)
            ),
            None,
        )
        if match is None:
            return None
        return self._drafts.get(match.draft_id)

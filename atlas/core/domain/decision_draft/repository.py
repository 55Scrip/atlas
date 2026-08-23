"""Repository interface for the DecisionDraft aggregate (ADR-DD-001).

Insert-only, like `Decision`'s and `DecisionContext`'s own repositories:
there is no update method, so "no UPDATE, ever" is enforced at the type
level, not by convention — see `decision/repository.py`'s own docstring
for the identical reasoning applied here.
"""
from __future__ import annotations

from typing import Protocol

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.value_objects import UserId
from atlas.core.domain.decision_draft.entity import DecisionDraftEvent
from atlas.core.domain.decision_draft.value_objects import DraftId


class DecisionDraftEventRepository(Protocol):
    def add(self, event: DecisionDraftEvent) -> None:
        """Insert a new event. Never UPDATEs or DELETEs."""
        ...

    def get_latest_event(self, draft_id: DraftId) -> DecisionDraftEvent | None:
        """The single most recent event for a draft, or None if it never existed."""
        ...

    def list_events(self, draft_id: DraftId) -> list[DecisionDraftEvent]:
        """Full history for one draft, oldest first."""
        ...

    def list_latest_by_case(self, case_id: CaseId) -> list[DecisionDraftEvent]:
        """The latest event for every distinct draft_id ever created
        under this Case, regardless of current status — filtering to
        Active is an application-layer concern, not a repository one.
        """
        ...

    def list_latest_by_user(self, user_id: UserId) -> list[DecisionDraftEvent]:
        """The latest event for every distinct draft_id ever created by
        this investor, across every Case — the cross-Case counterpart
        to `list_latest_by_case`, serving the Daily Brief summary
        projection (ADR-DD-001 §4). Not present in
        `DecisionDraft-Implementation-Design.md` §5.1's own code
        block, which specified the `GET .../daily-brief-summary` route
        (§6.1) and this exact `user_id` index (§5.3) but omitted the
        repository method needed to serve it — added here as the
        direct, mechanical completion of what those two sections
        already imply. See this sprint's own execution report,
        "Implementation findings," for the explicit disclosure.
        """
        ...

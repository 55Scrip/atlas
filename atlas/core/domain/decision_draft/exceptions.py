"""Domain errors for the DecisionDraft aggregate (ADR-DD-001).

`Decision`'s own `DecisionValidationError` (422) and `DecisionContext`'s
own `DecisionContextValidationError` (400) are deliberately not
redeclared here: `DecisionDraftService.commit()` lets those propagate,
unmodified, from `Decision.register()`/`DecisionContext.capture()`
directly, and their own existing, already-registered app-wide exception
handlers (`atlas.core.infrastructure.api.decision.errors`,
`atlas.core.infrastructure.api.decision_context.errors`) already map
them, with no new handler required here. See
`DecisionDraft-Implementation-Design.md` §6.4.

`atlas.core.domain.case.exceptions.CaseNotFoundError` is reused
directly for the same reason — this package raises it, never a new
draft-specific equivalent.
"""
from __future__ import annotations


class DecisionDraftError(Exception):
    """Base class for all DecisionDraft domain errors."""


class DecisionDraftNotFoundError(DecisionDraftError):
    """Raised when a requested DecisionDraft does not exist."""


class DecisionDraftAlreadyAbandonedError(DecisionDraftError):
    """Raised when revise/abandon/commit is attempted on a draft whose
    latest event is already `"abandoned"`."""


class DecisionDraftAlreadyCommittedError(DecisionDraftError):
    """Raised when revise/abandon/commit is attempted on a draft whose
    latest event is already `"committed"`.

    Also the guard against a duplicate `Decision` being created by a
    retried commit call — see `DecisionDraft-Implementation-Design.md`
    §10's own disclosed partial-commit-failure risk.
    """


class DecisionDraftConflictError(DecisionDraftError):
    """Raised when a `revise` call's own `expected_latest_event_id`
    does not match the server's actual latest event for that draft —
    the optimistic-concurrency guard described in
    `DecisionDraft-Implementation-Design.md` §6.4/§7.5.
    """

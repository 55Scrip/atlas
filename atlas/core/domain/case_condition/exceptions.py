"""Domain errors for the CaseCondition aggregate (ADR-CC-001).

`atlas.core.domain.case.exceptions.CaseNotFoundError` and
`atlas.core.domain.decision.exceptions.DecisionValidationError` are
reused directly, not redeclared — the same discipline
`decision_draft/exceptions.py` already established (Sprint 9): each
already has its own app-wide error handler.
"""
from __future__ import annotations


class CaseConditionError(Exception):
    """Base class for all CaseCondition domain errors."""


class CaseConditionNotFoundError(CaseConditionError):
    """Raised when a requested CaseCondition does not exist."""


class CaseConditionTerminatedError(CaseConditionError):
    """Raised when revise/evaluate/retire/supersede is attempted on a
    condition whose latest event is already `"retired"` or
    `"superseded"` — both are terminal; see `entity.py`'s own
    docstring for why."""


class CrossCaseDecisionError(CaseConditionError):
    """Raised when a CaseCondition's optional `decision_id` refers to a
    Decision belonging to a different Case — the same INV-004-style
    same-Case requirement already enforced for `Decision.observation_id`
    (see `atlas.core.domain.decision.exceptions
    .CrossCaseObservationError`'s own docstring), applied here to the
    equivalent optional back-reference ADR-CC-001 §6 establishes.
    """


class ConditionNotMechanicallyEvaluableError(CaseConditionError):
    """Raised by `evaluate()` when a condition has no structured
    sub-field (free-text only, ADR-CC-001 §3) and no
    `human_asserted_satisfied` override was supplied — a qualitative
    condition cannot be mechanically checked and requires a human
    judgment, per this ADR's own predicate-content model."""


class MissingObservedValueError(CaseConditionError):
    """Raised by `evaluate()` when a threshold-structured condition is
    mechanically evaluated with no `observed_value` supplied — Atlas
    has no live-data feed of its own to invent one from (ADR-CC-001
    §5, §9: `atlas/monitoring`'s own comparison baseline is
    synthetically fabricated and must never be reused as if it were
    real)."""

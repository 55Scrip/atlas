"""Domain errors for the Assumption aggregate (ADR-AS-001).

`atlas.core.domain.decision_context.exceptions.DecisionNotFoundError`
is reused directly for "decision_id does not exist" — the same
discipline `case_condition/exceptions.py` already established (Sprint
10) for the identical situation.
"""
from __future__ import annotations


class AssumptionError(Exception):
    """Base class for all Assumption domain errors."""


class AssumptionNotFoundError(AssumptionError):
    """Raised when a requested Assumption does not exist."""


class AssumptionTerminatedError(AssumptionError):
    """Raised when revise/challenge/retire/supersede/attach/detach is
    attempted on an assumption whose latest event is already
    `"retired"` or `"superseded"` — both are terminal; see `entity.py`'s
    own docstring for why."""


class CaseConditionNotFoundForLinkError(AssumptionError):
    """Raised by `attach_case_condition` when the given `CaseCondition`
    id does not name a real, existing condition — `Assumption` never
    accepts a dangling cross-reference (ADR-AS-001 §8's own "loose,
    optional cross-reference" is still a reference to something real,
    not an arbitrary string)."""

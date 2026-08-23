"""The CaseCondition evaluation engine (ADR-CC-001 §5).

Pure predicate-evaluation logic — no I/O, no repository, no scheduling.
"What the actual scheduling/evaluation mechanism for state-based
conditions is" is explicitly named by ADR-CC-001's own Open Questions
as "a real, unavoidable next question, explicitly out of this ADR's
own ontology-only scope" — this module answers only "given a
condition's own current content and, where needed, a caller-supplied
observed value, is the predicate met?", never "how or when should this
be checked" or "where does live data come from." No connection to
`atlas/monitoring` is made or implied; that package's own comparison
baseline is synthetically fabricated (ADR-CC-001 §9) and is never
reused here as if it were real data.

**Time-based** conditions (`structured_kind="date"`) are self-contained:
a trivial `evaluated_at >= threshold_date` comparison, no external
input needed — the same comparison idiom already used by
`atlas.alpha.investment_case.service._is_thesis_stale`
(`(evaluated_at - reference).days >= threshold`), reused here in its
general `>=` form rather than reinvented.

**State-based** conditions (`structured_kind="threshold"`) require the
caller to supply `observed_value` — Atlas has no live financial-data
feed wired to any Decision/Case-anchored object today (ADR-CC-001 §5),
so this module never invents one; it only compares whatever value the
caller (a future data-feed integration, a script, or a manually
triggered check) asserts as current.

**Free-text-only** conditions (`structured_kind=None`) cannot be
mechanically evaluated at all — ADR-CC-001 §3's own predicate model has
no formal schema for qualitative content. Only a human judgment can
satisfy one; see `CaseConditionService.evaluate`'s own
`human_asserted_satisfied` override.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from atlas.core.domain.case_condition.entity import CaseConditionView, ThresholdOperator
from atlas.core.domain.case_condition.exceptions import (
    ConditionNotMechanicallyEvaluableError,
    MissingObservedValueError,
)

_OPERATORS: dict[ThresholdOperator, Callable[[float, float], bool]] = {
    "<": lambda observed, threshold: observed < threshold,
    "<=": lambda observed, threshold: observed <= threshold,
    ">": lambda observed, threshold: observed > threshold,
    ">=": lambda observed, threshold: observed >= threshold,
    "==": lambda observed, threshold: observed == threshold,
    "!=": lambda observed, threshold: observed != threshold,
}


def evaluate_date_condition(threshold_date: datetime, evaluated_at: datetime) -> bool:
    """`today >= threshold_date` — the calendar-comparison mechanism
    ADR-CC-001 §5 describes as needing "no live data.\""""
    return evaluated_at >= threshold_date


def evaluate_threshold_condition(
    operator: ThresholdOperator, threshold_value: float, observed_value: float
) -> bool:
    """The live-data threshold comparison ADR-CC-001 §5 describes —
    given, never derived or fabricated here."""
    return _OPERATORS[operator](observed_value, threshold_value)


def evaluate(
    view: CaseConditionView,
    *,
    evaluated_at: datetime,
    observed_value: float | None = None,
) -> bool:
    """Mechanically evaluate a condition's current predicate.

    Raises `ConditionNotMechanicallyEvaluableError` for a free-text-only
    condition (no `structured_kind`) — call `CaseConditionService
    .evaluate` with `human_asserted_satisfied` instead for those.
    Raises `MissingObservedValueError` for a threshold-structured
    condition evaluated with no `observed_value` supplied.
    """
    if view.structured_kind == "date":
        assert view.threshold_date is not None
        return evaluate_date_condition(view.threshold_date, evaluated_at)

    if view.structured_kind == "threshold":
        if observed_value is None:
            raise MissingObservedValueError(
                f"CaseCondition {view.condition_id} is threshold-structured but no "
                "observed_value was supplied to evaluate it"
            )
        assert view.threshold_operator is not None
        assert view.threshold_value is not None
        return evaluate_threshold_condition(
            view.threshold_operator, view.threshold_value, observed_value
        )

    raise ConditionNotMechanicallyEvaluableError(
        f"CaseCondition {view.condition_id} has no structured sub-field (free-text "
        "predicate only) and cannot be mechanically evaluated; supply "
        "human_asserted_satisfied instead"
    )

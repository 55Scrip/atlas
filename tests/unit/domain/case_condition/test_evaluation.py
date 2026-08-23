"""Tests for the CaseCondition evaluation engine (ADR-CC-001 §5)."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.case_condition.entity import CaseConditionEvent, reconstruct_current_state
from atlas.core.domain.case_condition.evaluation import (
    evaluate,
    evaluate_date_condition,
    evaluate_threshold_condition,
)
from atlas.core.domain.case_condition.exceptions import (
    ConditionNotMechanicallyEvaluableError,
    MissingObservedValueError,
)
from atlas.core.domain.case_condition.value_objects import CaseConditionId

_CASE_ID = CaseId()
_CONDITION_ID = CaseConditionId()


def _view(**content):
    event = CaseConditionEvent.revised(
        condition_id=_CONDITION_ID, case_id=_CASE_ID, decision_id=None, event_id="event-1", **content
    )
    return reconstruct_current_state([event])


class TestEvaluateDateCondition:
    def test_true_when_evaluated_at_is_on_or_after_the_threshold(self):
        threshold = datetime(2026, 6, 1, tzinfo=timezone.utc)
        assert evaluate_date_condition(threshold, datetime(2026, 6, 1, tzinfo=timezone.utc)) is True
        assert evaluate_date_condition(threshold, datetime(2026, 6, 2, tzinfo=timezone.utc)) is True

    def test_false_before_the_threshold(self):
        threshold = datetime(2026, 6, 1, tzinfo=timezone.utc)
        assert evaluate_date_condition(threshold, datetime(2026, 5, 31, tzinfo=timezone.utc)) is False


class TestEvaluateThresholdCondition:
    @pytest.mark.parametrize(
        "operator,observed,threshold,expected",
        [
            ("<", 0.02, 0.05, True),
            ("<", 0.10, 0.05, False),
            ("<=", 0.05, 0.05, True),
            (">", 0.10, 0.05, True),
            (">=", 0.05, 0.05, True),
            ("==", 0.05, 0.05, True),
            ("!=", 0.05, 0.05, False),
        ],
    )
    def test_operators(self, operator, observed, threshold, expected):
        assert evaluate_threshold_condition(operator, threshold, observed) is expected


class TestEvaluateDispatch:
    def test_dispatches_to_date_evaluation(self):
        view = _view(structured_kind="date", threshold_date=datetime(2026, 6, 1, tzinfo=timezone.utc))
        assert evaluate(view, evaluated_at=datetime(2026, 6, 2, tzinfo=timezone.utc)) is True
        assert evaluate(view, evaluated_at=datetime(2026, 5, 1, tzinfo=timezone.utc)) is False

    def test_dispatches_to_threshold_evaluation(self):
        view = _view(
            structured_kind="threshold",
            threshold_metric="china_revenue_growth",
            threshold_operator="<",
            threshold_value=0.05,
        )
        assert evaluate(view, evaluated_at=datetime.now(timezone.utc), observed_value=0.02) is True
        assert evaluate(view, evaluated_at=datetime.now(timezone.utc), observed_value=0.10) is False

    def test_raises_when_threshold_condition_has_no_observed_value(self):
        view = _view(
            structured_kind="threshold",
            threshold_metric="china_revenue_growth",
            threshold_operator="<",
            threshold_value=0.05,
        )
        with pytest.raises(MissingObservedValueError):
            evaluate(view, evaluated_at=datetime.now(timezone.utc))

    def test_raises_for_a_free_text_only_condition(self):
        view = _view(predicate_text="Management changes capital-allocation policy")
        with pytest.raises(ConditionNotMechanicallyEvaluableError):
            evaluate(view, evaluated_at=datetime.now(timezone.utc))

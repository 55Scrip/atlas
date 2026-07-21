"""Tests for the Reasoning Trace aggregate root (DO-IMP-009)."""
from __future__ import annotations

import dataclasses
import uuid
from datetime import datetime, timezone

import pytest

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.reasoning_trace.entity import ReasoningTrace
from atlas.core.domain.reasoning_trace.exceptions import EmptySupportError
from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.domain.shared.typed_reference import TypedDomainObjectReference

_CASE_ID = CaseId()
_SUPPORT_A = TypedDomainObjectReference(
    target_type=DomainObjectType.OBSERVATION, target_id=uuid.uuid4()
)
_SUPPORT_B = TypedDomainObjectReference(
    target_type=DomainObjectType.JUDGMENT, target_id=uuid.uuid4()
)


def _fixed_clock(dt: datetime):
    return lambda: dt


class TestReasoningTraceCapture:
    def test_captures_with_one_support(self):
        trace = ReasoningTrace.capture(case_id=_CASE_ID, supports=frozenset({_SUPPORT_A}))
        assert trace.case_id == _CASE_ID
        assert trace.supports == frozenset({_SUPPORT_A})

    def test_captures_with_multiple_supports(self):
        trace = ReasoningTrace.capture(
            case_id=_CASE_ID, supports=frozenset({_SUPPORT_A, _SUPPORT_B})
        )
        assert trace.supports == frozenset({_SUPPORT_A, _SUPPORT_B})

    def test_assigns_a_fresh_id(self):
        first = ReasoningTrace.capture(case_id=_CASE_ID, supports=frozenset({_SUPPORT_A}))
        second = ReasoningTrace.capture(case_id=_CASE_ID, supports=frozenset({_SUPPORT_A}))
        assert first.id != second.id

    def test_recorded_at_is_always_now(self):
        now = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)
        trace = ReasoningTrace.capture(
            case_id=_CASE_ID, supports=frozenset({_SUPPORT_A}), clock=_fixed_clock(now)
        )
        assert trace.recorded_at == now

    def test_recorded_at_defaults_to_the_real_clock(self):
        before = datetime.now(timezone.utc)
        trace = ReasoningTrace.capture(case_id=_CASE_ID, supports=frozenset({_SUPPORT_A}))
        after = datetime.now(timezone.utc)
        assert before <= trace.recorded_at <= after

    def test_requires_a_case_id(self):
        with pytest.raises(TypeError):
            ReasoningTrace.capture(supports=frozenset({_SUPPORT_A}))

    def test_requires_supports(self):
        with pytest.raises(TypeError):
            ReasoningTrace.capture(case_id=_CASE_ID)


class TestEmptySupportRejection:
    def test_capture_with_an_empty_frozenset_raises(self):
        with pytest.raises(EmptySupportError):
            ReasoningTrace.capture(case_id=_CASE_ID, supports=frozenset())

    def test_direct_construction_with_an_empty_frozenset_raises(self):
        with pytest.raises(EmptySupportError):
            ReasoningTrace(
                id=ReasoningTrace.capture(
                    case_id=_CASE_ID, supports=frozenset({_SUPPORT_A})
                ).id,
                case_id=_CASE_ID,
                supports=frozenset(),
                recorded_at=datetime.now(timezone.utc),
            )


class TestDuplicateSupportCollapse:
    def test_duplicate_typed_references_in_the_constructor_input_collapse(self):
        trace = ReasoningTrace.capture(
            case_id=_CASE_ID, supports=[_SUPPORT_A, _SUPPORT_A, _SUPPORT_B]
        )
        assert len(trace.supports) == 2
        assert trace.supports == frozenset({_SUPPORT_A, _SUPPORT_B})


class TestReasoningTraceHasNoSpeculativeFields:
    def test_only_the_four_canonical_fields_are_declared(self):
        # No statement, content, conclusion, reasoning text, title,
        # description, sequence, confidence, author, source, status,
        # updated_at, or metadata field exists — Sections 11/16 of the
        # audited design forbid all of them.
        declared = {f.name for f in dataclasses.fields(ReasoningTrace)}
        assert declared == {"id", "case_id", "supports", "recorded_at"}


class TestSupportsIsAFrozenset:
    def test_supports_is_stored_as_a_frozenset(self):
        trace = ReasoningTrace.capture(case_id=_CASE_ID, supports=[_SUPPORT_A, _SUPPORT_B])
        assert isinstance(trace.supports, frozenset)


class TestSupportOrderIsIrrelevant:
    def test_supports_built_in_different_orders_are_identical(self):
        first = ReasoningTrace.capture(case_id=_CASE_ID, supports=[_SUPPORT_A, _SUPPORT_B])
        second = ReasoningTrace.capture(case_id=_CASE_ID, supports=[_SUPPORT_B, _SUPPORT_A])
        assert first.supports == second.supports


class TestReasoningTraceImmutability:
    def test_is_frozen(self):
        trace = ReasoningTrace.capture(case_id=_CASE_ID, supports=frozenset({_SUPPORT_A}))
        with pytest.raises(dataclasses.FrozenInstanceError):
            trace.supports = frozenset({_SUPPORT_B})


class TestReasoningTraceIdentity:
    def test_two_traces_with_identical_case_and_supports_remain_distinct(self):
        same_instant = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)
        first = ReasoningTrace.capture(
            case_id=_CASE_ID, supports=frozenset({_SUPPORT_A}), clock=_fixed_clock(same_instant)
        )
        second = ReasoningTrace.capture(
            case_id=_CASE_ID, supports=frozenset({_SUPPORT_A}), clock=_fixed_clock(same_instant)
        )
        assert first != second
        assert first.id != second.id

    def test_a_reasoning_trace_equals_itself(self):
        trace = ReasoningTrace.capture(case_id=_CASE_ID, supports=frozenset({_SUPPORT_A}))
        assert trace == trace

    def test_duplicate_support_sets_across_separate_traces_are_permitted(self):
        first = ReasoningTrace.capture(case_id=_CASE_ID, supports=frozenset({_SUPPORT_A}))
        second = ReasoningTrace.capture(case_id=_CASE_ID, supports=frozenset({_SUPPORT_A}))
        assert first.supports == second.supports
        assert first.id != second.id

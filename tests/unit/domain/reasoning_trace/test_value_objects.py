"""Tests for Reasoning Trace value objects (DO-IMP-009)."""
from __future__ import annotations

import uuid

from atlas.core.domain.reasoning_trace.value_objects import ReasoningTraceId


class TestReasoningTraceId:
    def test_generates_a_uuid_by_default(self):
        assert isinstance(ReasoningTraceId().value, uuid.UUID)

    def test_two_default_ids_are_different(self):
        assert ReasoningTraceId() != ReasoningTraceId()

    def test_equal_by_value(self):
        value = uuid.uuid4()
        assert ReasoningTraceId(value) == ReasoningTraceId(value)

    def test_str_returns_the_uuid_string(self):
        value = uuid.uuid4()
        assert str(ReasoningTraceId(value)) == str(value)

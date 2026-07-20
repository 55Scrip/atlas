"""Tests for Case value objects (DO-IMP-001 Case Aggregate)."""
from __future__ import annotations

import uuid

from atlas.core.domain.case.value_objects import CaseId


class TestCaseId:
    def test_generates_a_uuid_by_default(self):
        assert isinstance(CaseId().value, uuid.UUID)

    def test_two_default_ids_are_different(self):
        assert CaseId() != CaseId()

    def test_equal_by_value(self):
        value = uuid.uuid4()
        assert CaseId(value) == CaseId(value)

    def test_str_returns_the_uuid_string(self):
        value = uuid.uuid4()
        assert str(CaseId(value)) == str(value)

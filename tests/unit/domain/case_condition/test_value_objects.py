"""Tests for CaseCondition's own value objects (ADR-CC-001)."""
from __future__ import annotations

import uuid

from atlas.core.domain.case_condition.value_objects import CaseConditionId


class TestCaseConditionId:
    def test_generates_a_fresh_uuid_by_default(self):
        first = CaseConditionId()
        second = CaseConditionId()
        assert first != second
        assert isinstance(first.value, uuid.UUID)

    def test_wraps_a_given_uuid(self):
        value = uuid.uuid4()
        condition_id = CaseConditionId(value)
        assert condition_id.value == value

    def test_str_returns_the_uuid_string(self):
        value = uuid.uuid4()
        condition_id = CaseConditionId(value)
        assert str(condition_id) == str(value)

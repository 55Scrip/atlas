"""Tests for Assumption's own value objects (ADR-AS-001)."""
from __future__ import annotations

import uuid

from atlas.core.domain.assumption.value_objects import AssumptionId


class TestAssumptionId:
    def test_generates_a_fresh_uuid_by_default(self):
        first = AssumptionId()
        second = AssumptionId()
        assert first != second
        assert isinstance(first.value, uuid.UUID)

    def test_wraps_a_given_uuid(self):
        value = uuid.uuid4()
        assumption_id = AssumptionId(value)
        assert assumption_id.value == value

    def test_str_returns_the_uuid_string(self):
        value = uuid.uuid4()
        assumption_id = AssumptionId(value)
        assert str(assumption_id) == str(value)

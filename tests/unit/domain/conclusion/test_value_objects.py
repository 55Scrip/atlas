"""Tests for Conclusion value objects (ATLAS-001 Core Loop)."""
from __future__ import annotations

import uuid

import pytest

from atlas.core.domain.conclusion.exceptions import MissingStatementError
from atlas.core.domain.conclusion.value_objects import ConclusionId, Statement


class TestConclusionId:
    def test_generates_a_uuid_by_default(self):
        assert isinstance(ConclusionId().value, uuid.UUID)

    def test_two_default_ids_are_different(self):
        assert ConclusionId() != ConclusionId()

    def test_equal_by_value(self):
        value = uuid.uuid4()
        assert ConclusionId(value) == ConclusionId(value)


class TestStatement:
    def test_holds_the_value(self):
        statement = Statement("The weight of evidence supports accelerating demand.")
        assert statement.value == "The weight of evidence supports accelerating demand."

    def test_strips_surrounding_whitespace(self):
        assert Statement("  the case holds up  ").value == "the case holds up"

    def test_rejects_empty_statement(self):
        with pytest.raises(MissingStatementError):
            Statement("")

    def test_rejects_whitespace_only_statement(self):
        with pytest.raises(MissingStatementError):
            Statement("   ")

    def test_rejects_missing_statement(self):
        with pytest.raises(MissingStatementError):
            Statement(None)

    def test_is_frozen(self):
        statement = Statement("the case holds up")
        with pytest.raises(AttributeError):
            statement.value = "changed"

"""Tests for Interpretation value objects (ATLAS-001 Core Loop)."""
from __future__ import annotations

import uuid

import pytest

from atlas.core.domain.interpretation.exceptions import MissingStatementError
from atlas.core.domain.interpretation.value_objects import InterpretationId, Statement


class TestInterpretationId:
    def test_generates_a_uuid_by_default(self):
        assert isinstance(InterpretationId().value, uuid.UUID)

    def test_two_default_ids_are_different(self):
        assert InterpretationId() != InterpretationId()

    def test_equal_by_value(self):
        value = uuid.uuid4()
        assert InterpretationId(value) == InterpretationId(value)


class TestStatement:
    def test_holds_the_value(self):
        statement = Statement("This suggests demand may be accelerating.")
        assert statement.value == "This suggests demand may be accelerating."

    def test_strips_surrounding_whitespace(self):
        assert Statement("  this matters because  ").value == "this matters because"

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
        statement = Statement("this matters because")
        with pytest.raises(AttributeError):
            statement.value = "changed"

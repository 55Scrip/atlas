"""Tests for Outcome value objects (ATLAS-001 Core Loop)."""
from __future__ import annotations

import uuid

import pytest

from atlas.core.domain.outcome.exceptions import MissingStatementError
from atlas.core.domain.outcome.value_objects import OutcomeId, Statement


class TestOutcomeId:
    def test_generates_a_uuid_by_default(self):
        assert isinstance(OutcomeId().value, uuid.UUID)

    def test_two_default_ids_are_different(self):
        assert OutcomeId() != OutcomeId()

    def test_equal_by_value(self):
        value = uuid.uuid4()
        assert OutcomeId(value) == OutcomeId(value)


class TestStatement:
    def test_holds_the_value(self):
        statement = Statement("Revenue growth accelerated as expected.")
        assert statement.value == "Revenue growth accelerated as expected."

    def test_strips_surrounding_whitespace(self):
        assert Statement("  it played out as expected  ").value == "it played out as expected"

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
        statement = Statement("it played out as expected")
        with pytest.raises(AttributeError):
            statement.value = "changed"

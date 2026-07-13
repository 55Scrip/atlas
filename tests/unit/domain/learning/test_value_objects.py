"""Tests for Learning value objects (ATLAS-001 Core Loop)."""
from __future__ import annotations

import uuid

import pytest

from atlas.core.domain.learning.exceptions import MissingStatementError
from atlas.core.domain.learning.value_objects import LearningId, Statement


class TestLearningId:
    def test_generates_a_uuid_by_default(self):
        assert isinstance(LearningId().value, uuid.UUID)

    def test_two_default_ids_are_different(self):
        assert LearningId() != LearningId()

    def test_equal_by_value(self):
        value = uuid.uuid4()
        assert LearningId(value) == LearningId(value)


class TestStatement:
    def test_holds_the_value(self):
        statement = Statement("Weigh capex guidance more heavily than headline revenue growth.")
        assert statement.value == (
            "Weigh capex guidance more heavily than headline revenue growth."
        )

    def test_strips_surrounding_whitespace(self):
        assert Statement("  trust the guidance signal  ").value == "trust the guidance signal"

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
        statement = Statement("trust the guidance signal")
        with pytest.raises(AttributeError):
            statement.value = "changed"

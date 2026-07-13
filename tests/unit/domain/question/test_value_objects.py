"""Tests for Question value objects (ATLAS-001 Core Loop)."""
from __future__ import annotations

import uuid

import pytest

from atlas.core.domain.question.exceptions import MissingStatementError
from atlas.core.domain.question.value_objects import QuestionId, Statement


class TestQuestionId:
    def test_generates_a_uuid_by_default(self):
        assert isinstance(QuestionId().value, uuid.UUID)

    def test_two_default_ids_are_different(self):
        assert QuestionId() != QuestionId()

    def test_equal_by_value(self):
        value = uuid.uuid4()
        assert QuestionId(value) == QuestionId(value)


class TestStatement:
    def test_holds_the_value(self):
        statement = Statement("Is demand for AI infrastructure accelerating?")
        assert statement.value == "Is demand for AI infrastructure accelerating?"

    def test_strips_surrounding_whitespace(self):
        assert Statement("  what is going on here?  ").value == "what is going on here?"

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
        statement = Statement("what is going on here?")
        with pytest.raises(AttributeError):
            statement.value = "changed"

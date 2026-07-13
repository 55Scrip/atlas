"""Tests for Evaluation value objects (ATLAS-001 Core Loop)."""
from __future__ import annotations

import uuid

import pytest

from atlas.core.domain.evaluation.exceptions import MissingStatementError
from atlas.core.domain.evaluation.value_objects import EvaluationId, Statement


class TestEvaluationId:
    def test_generates_a_uuid_by_default(self):
        assert isinstance(EvaluationId().value, uuid.UUID)

    def test_two_default_ids_are_different(self):
        assert EvaluationId() != EvaluationId()

    def test_equal_by_value(self):
        value = uuid.uuid4()
        assert EvaluationId(value) == EvaluationId(value)


class TestStatement:
    def test_holds_the_value(self):
        statement = Statement("The decision proved correct; demand did accelerate.")
        assert statement.value == "The decision proved correct; demand did accelerate."

    def test_strips_surrounding_whitespace(self):
        assert Statement("  it held up  ").value == "it held up"

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
        statement = Statement("it held up")
        with pytest.raises(AttributeError):
            statement.value = "changed"

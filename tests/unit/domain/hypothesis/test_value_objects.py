"""Tests for Hypothesis value objects (API-004 Hypothesis Capture)."""
from __future__ import annotations

import uuid

import pytest

from atlas.core.domain.hypothesis.exceptions import MissingStatementError
from atlas.core.domain.hypothesis.value_objects import HypothesisId, Statement


class TestHypothesisId:
    def test_generates_a_uuid_by_default(self):
        assert isinstance(HypothesisId().value, uuid.UUID)

    def test_two_default_ids_are_different(self):
        assert HypothesisId() != HypothesisId()

    def test_equal_by_value(self):
        value = uuid.uuid4()
        assert HypothesisId(value) == HypothesisId(value)


class TestStatement:
    def test_holds_the_value(self):
        statement = Statement(
            "Demand for AI infrastructure may be accelerating faster than the "
            "market expects."
        )
        assert statement.value == (
            "Demand for AI infrastructure may be accelerating faster than the "
            "market expects."
        )

    def test_strips_surrounding_whitespace(self):
        assert Statement("  margin pressure may be temporary  ").value == (
            "margin pressure may be temporary"
        )

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
        statement = Statement("margin pressure may be temporary")
        with pytest.raises(AttributeError):
            statement.value = "changed"

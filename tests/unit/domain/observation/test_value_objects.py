"""Tests for Observation value objects (API-003 Observation Capture)."""
from __future__ import annotations

import uuid

import pytest

from atlas.core.domain.observation.exceptions import (
    MissingStatementError,
    MissingSubjectError,
)
from atlas.core.domain.observation.value_objects import ObservationId, Statement, Subject


class TestObservationId:
    def test_generates_a_uuid_by_default(self):
        assert isinstance(ObservationId().value, uuid.UUID)

    def test_two_default_ids_are_different(self):
        assert ObservationId() != ObservationId()

    def test_equal_by_value(self):
        value = uuid.uuid4()
        assert ObservationId(value) == ObservationId(value)


class TestSubject:
    def test_holds_the_value(self):
        assert Subject("Semiconductor sector").value == "Semiconductor sector"

    def test_strips_surrounding_whitespace(self):
        assert Subject("  NVIDIA  ").value == "NVIDIA"

    def test_rejects_empty_subject(self):
        with pytest.raises(MissingSubjectError):
            Subject("")

    def test_rejects_whitespace_only_subject(self):
        with pytest.raises(MissingSubjectError):
            Subject("   ")

    def test_rejects_missing_subject(self):
        with pytest.raises(MissingSubjectError):
            Subject(None)

    def test_is_frozen(self):
        subject = Subject("NVIDIA")
        with pytest.raises(AttributeError):
            subject.value = "changed"


class TestStatement:
    def test_holds_the_value(self):
        statement = Statement("The company raised full-year guidance.")
        assert statement.value == "The company raised full-year guidance."

    def test_strips_surrounding_whitespace(self):
        assert Statement("  raised guidance  ").value == "raised guidance"

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
        statement = Statement("raised guidance")
        with pytest.raises(AttributeError):
            statement.value = "changed"

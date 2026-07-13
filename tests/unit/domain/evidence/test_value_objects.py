"""Tests for Evidence value objects (API-005 Evidence Capture)."""
from __future__ import annotations

import uuid

import pytest

from atlas.core.domain.evidence.exceptions import InvalidDirectionError, MissingStatementError
from atlas.core.domain.evidence.value_objects import Direction, EvidenceId, Statement


class TestEvidenceId:
    def test_generates_a_uuid_by_default(self):
        assert isinstance(EvidenceId().value, uuid.UUID)

    def test_two_default_ids_are_different(self):
        assert EvidenceId() != EvidenceId()

    def test_equal_by_value(self):
        value = uuid.uuid4()
        assert EvidenceId(value) == EvidenceId(value)


class TestStatement:
    def test_holds_the_value(self):
        statement = Statement(
            "Order intake increased by 24 percent and management raised "
            "full-year guidance for the second consecutive quarter."
        )
        assert statement.value == (
            "Order intake increased by 24 percent and management raised "
            "full-year guidance for the second consecutive quarter."
        )

    def test_strips_surrounding_whitespace(self):
        assert Statement("  free cash flow declined  ").value == "free cash flow declined"

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
        statement = Statement("free cash flow declined")
        with pytest.raises(AttributeError):
            statement.value = "changed"


class TestDirection:
    def test_supports_is_accepted(self):
        assert Direction.coerce("SUPPORTS") == Direction.SUPPORTS

    def test_challenges_is_accepted(self):
        assert Direction.coerce("CHALLENGES") == Direction.CHALLENGES

    def test_accepts_a_direction_instance_unchanged(self):
        assert Direction.coerce(Direction.SUPPORTS) == Direction.SUPPORTS

    def test_rejects_unknown_direction(self):
        with pytest.raises(InvalidDirectionError):
            Direction.coerce("PROVES")

    def test_rejects_missing_direction(self):
        with pytest.raises(InvalidDirectionError):
            Direction.coerce(None)

    def test_only_two_values_exist(self):
        assert {member.value for member in Direction} == {"SUPPORTS", "CHALLENGES"}

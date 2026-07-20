"""Domain tests for Judgment's value objects (DO-IMP-004)."""
from __future__ import annotations

import uuid

import pytest

from atlas.core.domain.judgment.exceptions import MissingCharacterizationError
from atlas.core.domain.judgment.value_objects import Characterization, JudgmentId


class TestJudgmentId:
    def test_generates_a_uuid_by_default(self):
        assert isinstance(JudgmentId().value, uuid.UUID)

    def test_two_default_constructions_are_distinct(self):
        assert JudgmentId() != JudgmentId()

    def test_accepts_an_explicit_uuid(self):
        value = uuid.uuid4()
        assert JudgmentId(value).value == value

    def test_str_matches_the_underlying_uuid(self):
        value = uuid.uuid4()
        assert str(JudgmentId(value)) == str(value)


class TestCharacterization:
    def test_accepts_non_empty_text(self):
        assert Characterization("This is a settled assessment").value == (
            "This is a settled assessment"
        )

    def test_strips_surrounding_whitespace(self):
        assert Characterization("  settled  ").value == "settled"

    def test_rejects_none(self):
        with pytest.raises(MissingCharacterizationError):
            Characterization(None)

    def test_rejects_empty_string(self):
        with pytest.raises(MissingCharacterizationError):
            Characterization("")

    def test_rejects_whitespace_only(self):
        with pytest.raises(MissingCharacterizationError):
            Characterization("   ")

    def test_str_returns_the_value(self):
        assert str(Characterization("settled")) == "settled"

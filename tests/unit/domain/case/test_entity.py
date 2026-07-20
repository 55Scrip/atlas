"""Tests for the Case aggregate root (DO-IMP-001 Case Aggregate)."""
from __future__ import annotations

import dataclasses
from datetime import datetime, timezone

import pytest

from atlas.core.domain.case.entity import Case


def _fixed_clock(dt: datetime):
    return lambda: dt


class TestCaseCreate:
    def test_assigns_a_fresh_id(self):
        first = Case.create()
        second = Case.create()
        assert first.id != second.id

    def test_recorded_at_is_always_now(self):
        now = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)
        case = Case.create(clock=_fixed_clock(now))
        assert case.recorded_at == now

    def test_recorded_at_defaults_to_the_real_clock(self):
        before = datetime.now(timezone.utc)
        case = Case.create()
        after = datetime.now(timezone.utc)
        assert before <= case.recorded_at <= after

    def test_creating_a_case_requires_no_arguments(self):
        # Case has no semantic input at all — this absence is itself the
        # canonical proposition under test (OE-002 §3.1).
        Case.create()


class TestCaseHasNoSpeculativeFields:
    def test_only_id_and_recorded_at_are_declared(self):
        declared = {f.name for f in dataclasses.fields(Case)}
        assert declared == {"id", "recorded_at"}


class TestCaseImmutability:
    def test_is_frozen(self):
        case = Case.create()
        with pytest.raises(dataclasses.FrozenInstanceError):
            case.recorded_at = datetime.now(timezone.utc)


class TestCaseIdentity:
    def test_two_cases_created_at_the_identical_instant_remain_distinct(self):
        # Identity, not content, distinguishes Domain Objects (INV-006).
        same_instant = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)
        first = Case.create(clock=_fixed_clock(same_instant))
        second = Case.create(clock=_fixed_clock(same_instant))
        assert first != second
        assert first.id != second.id

    def test_a_case_equals_itself(self):
        case = Case.create()
        assert case == case

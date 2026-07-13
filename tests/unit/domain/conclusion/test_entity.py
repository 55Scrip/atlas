"""Tests for the Conclusion aggregate root (ATLAS-001 Core Loop)."""
from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta, timezone

import pytest

from atlas.core.domain.conclusion.entity import Conclusion
from atlas.core.domain.conclusion.exceptions import InvalidConcludedAtError
from atlas.core.domain.conclusion.value_objects import Statement
from atlas.core.domain.evidence.value_objects import EvidenceId

_EVIDENCE_ID = EvidenceId()
_STATEMENT = Statement("The weight of evidence supports accelerating demand.")
_CONCLUDED_AT = datetime(2026, 7, 13, 12, 0, 0, tzinfo=timezone(timedelta(hours=2)))


def _fixed_clock(dt: datetime):
    return lambda: dt


class TestConclusionCapture:
    def test_captures_the_given_fields(self):
        conclusion = Conclusion.capture(
            evidence_id=_EVIDENCE_ID, statement=_STATEMENT, concluded_at=_CONCLUDED_AT
        )
        assert conclusion.evidence_id == _EVIDENCE_ID
        assert conclusion.statement == _STATEMENT
        assert conclusion.concluded_at == _CONCLUDED_AT

    def test_assigns_a_fresh_id(self):
        first = Conclusion.capture(
            evidence_id=_EVIDENCE_ID, statement=_STATEMENT, concluded_at=_CONCLUDED_AT
        )
        second = Conclusion.capture(
            evidence_id=_EVIDENCE_ID, statement=_STATEMENT, concluded_at=_CONCLUDED_AT
        )
        assert first.id != second.id

    def test_recorded_at_is_always_now(self):
        now = datetime(2026, 7, 13, 10, 0, tzinfo=timezone.utc)
        conclusion = Conclusion.capture(
            evidence_id=_EVIDENCE_ID,
            statement=_STATEMENT,
            concluded_at=_CONCLUDED_AT,
            clock=_fixed_clock(now),
        )
        assert conclusion.recorded_at == now

    def test_concluded_at_preserves_its_original_offset_unlike_recorded_at(self):
        now_utc = datetime(2026, 7, 13, 10, 0, tzinfo=timezone.utc)
        conclusion = Conclusion.capture(
            evidence_id=_EVIDENCE_ID,
            statement=_STATEMENT,
            concluded_at=_CONCLUDED_AT,
            clock=_fixed_clock(now_utc),
        )
        assert conclusion.concluded_at.utcoffset() == timedelta(hours=2)
        assert conclusion.concluded_at.isoformat() == "2026-07-13T12:00:00+02:00"
        assert conclusion.recorded_at.utcoffset() == timedelta(0)

    def test_note_defaults_to_none(self):
        conclusion = Conclusion.capture(
            evidence_id=_EVIDENCE_ID, statement=_STATEMENT, concluded_at=_CONCLUDED_AT
        )
        assert conclusion.note is None

    @pytest.mark.parametrize("blank", ["", "   "])
    def test_blank_note_normalizes_to_none(self, blank):
        conclusion = Conclusion.capture(
            evidence_id=_EVIDENCE_ID, statement=_STATEMENT, concluded_at=_CONCLUDED_AT, note=blank
        )
        assert conclusion.note is None

    def test_rejects_missing_concluded_at(self):
        with pytest.raises(InvalidConcludedAtError):
            Conclusion.capture(evidence_id=_EVIDENCE_ID, statement=_STATEMENT, concluded_at=None)

    def test_rejects_naive_concluded_at(self):
        with pytest.raises(InvalidConcludedAtError):
            Conclusion.capture(
                evidence_id=_EVIDENCE_ID,
                statement=_STATEMENT,
                concluded_at=datetime(2026, 7, 13, 12, 0, 0),
            )

    def test_requires_an_evidence_id(self):
        with pytest.raises(TypeError):
            Conclusion.capture(statement=_STATEMENT, concluded_at=_CONCLUDED_AT)

    def test_requires_a_statement(self):
        with pytest.raises(TypeError):
            Conclusion.capture(evidence_id=_EVIDENCE_ID, concluded_at=_CONCLUDED_AT)


class TestConclusionImmutability:
    def test_is_frozen(self):
        conclusion = Conclusion.capture(
            evidence_id=_EVIDENCE_ID, statement=_STATEMENT, concluded_at=_CONCLUDED_AT
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            conclusion.statement = Statement("changed")

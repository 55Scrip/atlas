"""Tests for `atlas.analysis_engine.business_data.sources` (ATLAS-022
Phase 5) -- the closed document-type taxonomy."""
from __future__ import annotations

from atlas.analysis_engine.business_data.sources import SourceKind


class TestSourceKindIsClosed:
    def test_exactly_eleven_members(self):
        assert len(SourceKind) == 11

    def test_is_a_closed_string_enum(self):
        assert issubclass(SourceKind, str)
        for member in SourceKind:
            assert isinstance(member.value, str)

    def test_contains_every_phase_5_example(self):
        expected = {
            "annual_report",
            "quarterly_report",
            "transcript",
            "press_release",
            "investor_presentation",
            "macro_report",
            "news",
            "manual_document",
            "unknown",
        }
        assert expected.issubset({member.value for member in SourceKind})

    def test_unknown_is_a_real_member_not_a_rejection(self):
        assert SourceKind.UNKNOWN.value == "unknown"

    def test_unrecognized_string_is_not_constructible(self):
        try:
            SourceKind("blog_post")
            assert False, "expected ValueError for an unrecognized source kind"
        except ValueError:
            pass

"""Tests for `atlas.analysis_engine.business_data.sources` (ATLAS-022
Phase 5) -- the closed document-type taxonomy."""
from __future__ import annotations

from atlas.analysis_engine.business_data.sources import SourceKind


class TestSourceKindIsClosed:
    def test_exactly_thirteen_members(self):
        """ATLAS-024 added MARKET_DATA_SNAPSHOT (the twelfth); the
        Investment Case Engine v1 slice added COMPANY_PROFILE (the
        thirteenth) -- a company's descriptive identity is a distinct
        document kind from its current market data, per that member's
        own docstring."""
        assert len(SourceKind) == 13

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

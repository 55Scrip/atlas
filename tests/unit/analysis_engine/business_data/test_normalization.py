"""Tests for `atlas.analysis_engine.business_data.normalization`
(ATLAS-022 Phase 6) -- deterministic structural transformation only."""
from __future__ import annotations

from atlas.analysis_engine.business_data.normalization import normalize
from atlas.analysis_engine.business_data.sources import SourceKind
from tests.unit.analysis_engine.business_data._fixtures import build_raw_document


class TestStructuralNormalization:
    def test_whitespace_is_trimmed(self):
        document = build_raw_document(identifier="  10-K-2025  ", company="  ASML  ")
        normalized = normalize(document)
        assert normalized.identifier == "10-K-2025"
        assert normalized.company == "ASML"

    def test_content_hash_is_lowercased(self):
        document = build_raw_document(content_hash="ABC123")
        normalized = normalize(document)
        assert normalized.content_hash == "abc123"

    def test_language_is_lowercased(self):
        document = build_raw_document(language="EN")
        normalized = normalize(document)
        assert normalized.language == "en"

    def test_source_kind_becomes_a_real_enum_member(self):
        document = build_raw_document(source_kind="annual_report")
        normalized = normalize(document)
        assert normalized.source_kind is SourceKind.ANNUAL_REPORT

    def test_period_fields_pass_through_unchanged(self):
        import datetime as dt

        start = dt.date(2025, 1, 1)
        end = dt.date(2025, 12, 31)
        document = build_raw_document(period_start=start, period_end=end)
        normalized = normalize(document)
        assert normalized.period_start == start
        assert normalized.period_end == end

    def test_metadata_is_carried_through(self):
        document = build_raw_document(metadata={"fiscal_year": 2025})
        normalized = normalize(document)
        assert normalized.metadata["fiscal_year"] == 2025


class TestNoSemanticInterpretation:
    def test_company_casing_is_never_altered(self):
        """Only whitespace is trimmed -- casing is never changed, since
        that would require assuming something about what the company
        name/ticker convention is (a semantic judgment this module
        never makes)."""
        document = build_raw_document(company="asml Holding")
        normalized = normalize(document)
        assert normalized.company == "asml Holding"


class TestDeterminism:
    def test_identical_input_produces_a_deeply_equal_result(self):
        document = build_raw_document()
        assert normalize(document) == normalize(document)

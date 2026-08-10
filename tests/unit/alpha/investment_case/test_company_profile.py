"""Tests for `atlas.alpha.investment_case.company_profile
.extract_company_profile` (Investment Case Engine v1 slice; extended
Company Data Foundation v1). No dedicated test file existed for this
module before this sprint -- exercised only indirectly through API
integration tests until now."""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.investment_case.company_profile import extract_company_profile
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest

_NOW = datetime(2026, 8, 9, tzinfo=timezone.utc)


def _profile_document(*, ticker: str = "AAPL", published_at: datetime = _NOW, **metadata) -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier=f"{ticker}:profile",
        company=ticker,
        source_kind="company_profile",
        published_at=published_at,
        provider_id="alpha_vantage",
        raw_reference="https://example.test/overview",
        content_hash=f"hash-{published_at.isoformat()}",
        language="en",
        metadata=metadata,
    )


def _ingest(document: RawBusinessDocument):
    result = ingest(document, evaluated_at=_NOW)
    assert isinstance(result, IngestedRecord)
    return result.record


class TestNoProfileRecord:
    def test_no_company_profile_record_returns_none(self):
        assert extract_company_profile("AAPL", ()) is None

    def test_a_financial_statement_record_alone_does_not_count(self):
        other = RawBusinessDocument(
            identifier="AAPL:FY:2024",
            company="AAPL",
            source_kind="financial_statement",
            published_at=_NOW,
            provider_id="sec_edgar",
            raw_reference="https://example.test/10k",
            content_hash="hash-1",
            language="en",
            metadata={"revenue": 1000.0},
        )
        assert extract_company_profile("AAPL", (_ingest(other),)) is None


class TestBasicFields:
    def test_all_identity_fields_pass_through(self):
        record = _ingest(
            _profile_document(
                name="Apple Inc.",
                exchange="NASDAQ",
                sector="TECHNOLOGY",
                industry="CONSUMER ELECTRONICS",
                country="USA",
                description="Apple designs and sells consumer electronics.",
                currency="USD",
                fiscal_year_end="September",
            )
        )
        profile = extract_company_profile("AAPL", (record,))
        assert profile is not None
        assert profile.ticker == "AAPL"
        assert profile.name == "Apple Inc."
        assert profile.exchange == "NASDAQ"
        assert profile.sector == "TECHNOLOGY"
        assert profile.industry == "CONSUMER ELECTRONICS"
        assert profile.country == "USA"
        assert "consumer electronics" in profile.description
        assert profile.currency == "USD"
        assert profile.fiscal_year_end == "September"
        assert profile.as_of == _NOW

    def test_fields_the_provider_did_not_report_are_honestly_none(self):
        record = _ingest(_profile_document(name="Xyz Corp"))
        profile = extract_company_profile("XYZ", (record,))
        assert profile.name == "Xyz Corp"
        assert profile.currency is None
        assert profile.fiscal_year_end is None
        assert profile.sector is None


class TestMultipleRecords:
    def test_the_most_recently_published_profile_wins(self):
        older = _ingest(_profile_document(published_at=_NOW, name="Old Name"))
        newer_time = datetime(2026, 8, 10, tzinfo=timezone.utc)
        newer = _ingest(_profile_document(published_at=newer_time, name="New Name"))
        profile = extract_company_profile("AAPL", (older, newer))
        assert profile.name == "New Name"
        assert profile.as_of == newer_time


class TestDeterminism:
    def test_identical_records_produce_a_deeply_equal_result(self):
        record = _ingest(_profile_document(name="Apple Inc."))
        assert extract_company_profile("AAPL", (record,)) == extract_company_profile("AAPL", (record,))

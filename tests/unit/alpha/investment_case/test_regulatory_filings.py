"""Tests for `atlas.alpha.investment_case.regulatory_filings
.extract_regulatory_filings` (Automatic Knowledge Ingestion Framework,
Foundation Provider). Mirrors `test_company_profile.py`'s own real-
`ingest()` convention exactly."""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.investment_case.regulatory_filings import extract_regulatory_filings
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest

_NOW = datetime(2026, 8, 22, tzinfo=timezone.utc)


def _filing_document(
    *, ticker: str = "AAPL", accession: str = "0000320193-26-000010", published_at: datetime = _NOW, **metadata
) -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier=f"{ticker}:FILING:{accession}",
        company=ticker,
        source_kind="company_filing",
        published_at=published_at,
        provider_id="sec_edgar_filings",
        raw_reference=f"https://example.test/{accession}",
        content_hash=f"hash-{accession}",
        language="en",
        metadata={"form_type": "10-K", "accession_number": accession, **metadata},
    )


def _ingest(document: RawBusinessDocument):
    result = ingest(document, evaluated_at=_NOW)
    assert isinstance(result, IngestedRecord)
    return result.record


class TestNoFilingRecords:
    def test_no_company_filing_record_returns_empty_tuple(self):
        assert extract_regulatory_filings(()) == ()

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
        assert extract_regulatory_filings((_ingest(other),)) == ()


class TestBasicFields:
    def test_all_fields_pass_through(self):
        record = _ingest(_filing_document(filing_url="https://example.test/aapl-10k.htm"))
        filings = extract_regulatory_filings((record,))
        assert len(filings) == 1
        filing = filings[0]
        assert filing.form_type == "10-K"
        assert filing.accession_number == "0000320193-26-000010"
        assert filing.filed_at == _NOW
        assert filing.filing_url == "https://example.test/aapl-10k.htm"

    def test_missing_metadata_falls_back_to_source_reference(self):
        record = _ingest(_filing_document())
        filing = extract_regulatory_filings((record,))[0]
        assert filing.filing_url == record.source_reference

    def test_a_record_missing_required_metadata_is_skipped(self):
        document = RawBusinessDocument(
            identifier="AAPL:FILING:bad",
            company="AAPL",
            source_kind="company_filing",
            published_at=_NOW,
            provider_id="sec_edgar_filings",
            raw_reference="https://example.test/bad",
            content_hash="hash-bad",
            language="en",
            metadata={},  # no form_type/accession_number
        )
        assert extract_regulatory_filings((_ingest(document),)) == ()


class TestOrdering:
    def test_newest_filing_first(self):
        older = _ingest(_filing_document(accession="0000320193-25-000090", published_at=_NOW))
        newer_time = datetime(2026, 8, 23, tzinfo=timezone.utc)
        newer = _ingest(_filing_document(accession="0000320193-26-000010", published_at=newer_time))
        filings = extract_regulatory_filings((older, newer))
        assert filings[0].accession_number == "0000320193-26-000010"
        assert filings[1].accession_number == "0000320193-25-000090"


class TestDeterminism:
    def test_identical_records_produce_a_deeply_equal_result(self):
        record = _ingest(_filing_document())
        assert extract_regulatory_filings((record,)) == extract_regulatory_filings((record,))

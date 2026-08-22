"""Tests for `atlas.alpha.investment_case.incentive_intelligence`
(Capability Expansion Sprint 12, Phases 2 through 8).
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.investment_case.incentive_intelligence import (
    IncentiveChangeFindingKind,
    extract_incentive_intelligence,
)
from atlas.alpha.investment_case.regulatory_filings import extract_regulatory_filings
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest

_EVALUATED_AT = datetime(2026, 8, 22, tzinfo=timezone.utc)


def _filing_record(form_type: str, accession: str, published_at: datetime):
    document = RawBusinessDocument(
        identifier=f"AAPL:FILING:{accession}",
        company="AAPL",
        source_kind="company_filing",
        published_at=published_at,
        provider_id="sec_edgar_filings",
        raw_reference=f"https://example.test/{accession}",
        content_hash=f"hash-{accession}",
        language="en",
        period_start=None,
        period_end=None,
        metadata={"form_type": form_type, "accession_number": accession, "filing_url": f"https://example.test/{accession}"},
    )
    result = ingest(document, evaluated_at=_EVALUATED_AT)
    assert isinstance(result, IngestedRecord)
    return result.record


def _knowledge(records):
    return extract_incentive_intelligence(extract_regulatory_filings(records))


class TestEmptyInput:
    def test_no_filings_yields_empty_knowledge_and_unavailable_finding(self):
        knowledge = _knowledge(())
        assert knowledge.compensation_disclosure_filings == ()
        assert knowledge.executive_incentive_programs == ()
        assert knowledge.timeline == ()
        assert knowledge.ownership_alignment == ()
        assert knowledge.dilution_events == ()
        assert knowledge.incentive_structures == ()
        assert len(knowledge.findings) == 1
        assert knowledge.findings[0].kind is IncentiveChangeFindingKind.COMPENSATION_DATA_UNAVAILABLE
        assert knowledge.findings[0].evidence_count == 0


class TestCompensationDisclosureDiscovery:
    def test_def_14a_filing_is_discovered(self):
        records = (_filing_record("DEF 14A", "0000320193-26-000003", datetime(2026, 1, 15, tzinfo=timezone.utc)),)
        knowledge = _knowledge(records)
        assert len(knowledge.compensation_disclosure_filings) == 1
        disclosure = knowledge.compensation_disclosure_filings[0]
        assert disclosure.filing.form_type == "DEF 14A"
        assert disclosure.filing.accession_number == "0000320193-26-000003"

    def test_non_proxy_filings_are_not_treated_as_compensation_disclosures(self):
        records = (
            _filing_record("10-K", "0000320193-26-000001", datetime(2026, 2, 1, tzinfo=timezone.utc)),
            _filing_record("8-K", "0000320193-26-000002", datetime(2026, 3, 1, tzinfo=timezone.utc)),
        )
        knowledge = _knowledge(records)
        assert knowledge.compensation_disclosure_filings == ()

    def test_multiple_proxy_filings_are_all_discovered(self):
        records = (
            _filing_record("DEF 14A", "0000320193-25-000030", datetime(2025, 1, 10, tzinfo=timezone.utc)),
            _filing_record("DEF 14A", "0000320193-26-000003", datetime(2026, 1, 15, tzinfo=timezone.utc)),
        )
        knowledge = _knowledge(records)
        assert len(knowledge.compensation_disclosure_filings) == 2

    def test_content_is_never_populated_even_with_a_real_disclosure(self):
        """The central discipline this sprint enforces: knowing a proxy
        statement exists is not the same as knowing what it says."""
        records = (_filing_record("DEF 14A", "0000320193-26-000003", datetime(2026, 1, 15, tzinfo=timezone.utc)),)
        knowledge = _knowledge(records)
        assert knowledge.executive_incentive_programs == ()
        assert knowledge.ownership_alignment == ()
        assert knowledge.incentive_structures == ()


class TestFindings:
    def test_finding_evidence_count_reflects_real_disclosure_count(self):
        records = (
            _filing_record("DEF 14A", "0000320193-25-000030", datetime(2025, 1, 10, tzinfo=timezone.utc)),
            _filing_record("DEF 14A", "0000320193-26-000003", datetime(2026, 1, 15, tzinfo=timezone.utc)),
        )
        knowledge = _knowledge(records)
        assert knowledge.findings[0].evidence_count == 2

    def test_finding_is_always_compensation_data_unavailable(self):
        records = (_filing_record("DEF 14A", "0000320193-26-000003", datetime(2026, 1, 15, tzinfo=timezone.utc)),)
        knowledge = _knowledge(records)
        kinds = {f.kind for f in knowledge.findings}
        assert kinds == {IncentiveChangeFindingKind.COMPENSATION_DATA_UNAVAILABLE}

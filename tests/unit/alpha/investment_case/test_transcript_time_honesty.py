"""Stage 3.2 -- no production path may read a transcript's fetch time,
ingestion time or calendar period as when management spoke.

Every transcript record Atlas holds carries one trustworthy temporal
fact: the provider's fiscal-quarter label. Records ingested before this
stage also carry a calendar `period_end` derived from that label and a
`published_at` that is only a fetch instant (for the historical backfill,
an operator-chosen one). These tests build records of both shapes --
through the real provider path for new ones, exactly as stored for
legacy ones -- and check every consumer: earnings-call knowledge,
knowledge-coverage freshness, guidance and credibility outcomes,
executive windows and the daily brief's executive-change signal.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest

from atlas.alpha.daily_brief_agenda.engine import executive_change_signal
from atlas.alpha.evidence_quality.models import EvidenceFreshness
from atlas.alpha.investment_case.capital_allocation_intelligence import extract_capital_allocation_history
from atlas.alpha.investment_case.earnings_call import compute_change_intelligence, extract_earnings_call_knowledge
from atlas.alpha.investment_case.executive_change_intelligence import extract_executive_change_intelligence
from atlas.alpha.investment_case.financial_statement_intelligence import extract_financial_statement_history
from atlas.alpha.investment_case.growth_intelligence import extract_growth_knowledge
from atlas.alpha.investment_case.management_credibility_intelligence import (
    CommitmentOutcome,
    extract_management_credibility,
)
from atlas.alpha.investment_case.management_guidance_intelligence import (
    GuidanceOutcome,
    GuidanceStatus,
    extract_management_guidance,
)
from atlas.alpha.knowledge_coverage.engine import _freshness_dominance_for_earnings_call
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.business_data.transcript_time import transcript_period, transcript_statement_date
from atlas.business_data_providers.alpha_vantage import AlphaVantageMarketDataProvider

AS_OF = datetime(2026, 9, 11, 12, tzinfo=timezone.utc)
INGESTED = datetime(2026, 9, 11, 16, tzinfo=timezone.utc)


def legacy_statement(quarter: str, content: str, *, company: str = "NVDA", index: int = 0,
                     published_at: datetime, period_end: date | None, title: str = "Chief Financial Officer",
                     speaker: str = "A. Exec"):
    """A transcript record shaped exactly like the ones in the live DB."""
    result = ingest(
        RawBusinessDocument(
            identifier=f"{company}:transcript:{quarter}:{index}",
            company=company,
            source_kind="transcript",
            published_at=published_at,
            provider_id="alpha_vantage",
            raw_reference=f"https://example.test/{company}/{quarter}",
            content_hash=f"{company}-{quarter}-{index}",
            language="en",
            period_start=period_end,
            period_end=period_end,
            metadata={"quarter": quarter, "statement_index": index, "speaker": speaker, "title": title,
                      "content": content},
        ),
        evaluated_at=INGESTED,
    )
    assert isinstance(result, IngestedRecord)
    return result.record


def fiscal_year(year: int, **metadata):
    result = ingest(
        RawBusinessDocument(
            identifier=f"NVDA:FY:{year}", company="NVDA", source_kind="financial_statement",
            published_at=datetime(year + 1, 2, 15, tzinfo=timezone.utc), provider_id="sec_edgar",
            raw_reference="https://example.test/10k", content_hash=f"fy-{year}", language="en",
            period_start=date(year, 1, 1), period_end=date(year, 12, 31), metadata={**metadata, "currency": "USD"},
        ),
        evaluated_at=INGESTED,
    )
    return result.record


#: NVIDIA's real "2025Q3" call is dated in its own text 20 November 2024;
#: Atlas stored 2025-09-30 as its period end and a backfill-chosen
#: 2025-12-12 as its published_at.
NVDA_Q3 = dict(published_at=datetime(2025, 12, 12, 16, 6, 28, tzinfo=timezone.utc), period_end=date(2025, 9, 30))


def freshness_of(knowledge) -> EvidenceFreshness:
    composition = SimpleNamespace(earnings_call=knowledge)
    return _freshness_dominance_for_earnings_call(composition, (), evaluated_at=AS_OF)[0]


class TestNewRecordsThroughTheProvider:
    """Phase 15 -- the production provider, with no network call."""

    def _records(self):
        payload = {"symbol": "CRM", "quarter": "2025Q3", "transcript": [
            {"speaker": "A. Exec", "title": "Chief Financial Officer",
             "content": "We expect margin to improve going forward."},
        ]}
        provider = AlphaVantageMarketDataProvider(lambda url, headers: payload, api_key="k", sleeper=lambda _: None)
        evaluated = datetime(2025, 12, 12, 16, 6, 28, tzinfo=timezone.utc)  # a backfill-style as-of instant
        documents = provider.fetch_earnings_call_transcripts(company_identifier="CRM", evaluated_at=evaluated)
        results = [ingest(d, evaluated_at=INGESTED) for d in documents]
        return tuple(r.record for r in results if isinstance(r, IngestedRecord))

    def test_no_calendar_period_is_derived_from_the_fiscal_label(self):
        (record,) = self._records()
        assert transcript_period(record) == "2025Q3"
        assert (record.period_start, record.period_end) == (None, None)

    def test_the_fetch_instant_is_observation_time_never_a_call_date(self):
        (record,) = self._records()
        assert record.version.created_at == INGESTED  # real ingestion time, operational
        assert transcript_statement_date(record) is None
        assert extract_earnings_call_knowledge(self._records()).transcripts[0].statement_date is None


class TestLegacyRecordsAreReadHonestly:
    """Phase 16 -- existing records keep their synthetic fields; no
    consumer reads them as event time, so no migration is needed."""

    def test_a_synthetic_period_end_and_fetch_time_never_become_a_statement_date(self):
        record = legacy_statement("2025Q3", "All our statements are made as of today, November 20, 2024.", **NVDA_Q3)
        knowledge = extract_earnings_call_knowledge((record,))
        assert knowledge.transcripts[0].statement_date is None

    def test_nvda_style_evidence_is_not_graded_fresh(self):
        """Before Stage 3.2: the 2025-09-30 calendar end was graded as the
        call's date, and the transcript came out FRESH."""
        record = legacy_statement("2025Q3", "We expect strong demand.", **NVDA_Q3)
        assert freshness_of(extract_earnings_call_knowledge((record,))) is EvidenceFreshness.NOT_APPLICABLE

    def test_a_calendar_coincidence_is_still_not_a_date(self):
        """GOOGL's calendar period ends look plausible. They are still a
        reading of a label, so they are not used either."""
        record = legacy_statement("2026Q2", "We expect strong demand.", company="GOOGL",
                                  published_at=datetime(2026, 8, 25, tzinfo=timezone.utc), period_end=date(2026, 6, 30))
        assert freshness_of(extract_earnings_call_knowledge((record,))) is EvidenceFreshness.NOT_APPLICABLE


class TestFreshnessNeedsAStatementDate:
    def _knowledge(self, statement_date: date | None):
        record = legacy_statement("2025Q3", "We expect strong demand.", **NVDA_Q3)
        knowledge = extract_earnings_call_knowledge((record,))
        return replace(knowledge, transcripts=(replace(knowledge.transcripts[0], statement_date=statement_date),))

    def test_unknown_statement_time_is_neither_fresh_nor_stale(self):
        freshness = freshness_of(self._knowledge(None))
        assert freshness is EvidenceFreshness.NOT_APPLICABLE
        assert freshness not in (EvidenceFreshness.FRESH, EvidenceFreshness.STALE)

    def test_a_known_recent_statement_is_fresh(self):
        assert freshness_of(self._knowledge(date(2026, 8, 20))) is EvidenceFreshness.FRESH

    def test_a_known_old_statement_is_stale_whatever_was_fetched_recently(self):
        """Ingested 2026-09-11, stated 2024-11-20: age is measured from the
        statement."""
        assert freshness_of(self._knowledge(date(2024, 11, 20))) is EvidenceFreshness.STALE


class TestChronologyComesFromTheFiscalPeriod:
    def _two_calls(self, older_fetched: datetime, newer_fetched: datetime):
        return (
            legacy_statement("2025Q3", "Our strategy remains focused.", published_at=older_fetched, period_end=None),
            legacy_statement("2025Q4", "Our strategy remains focused.", published_at=newer_fetched, period_end=None),
        )

    @pytest.mark.parametrize("older_fetched,newer_fetched", [
        (datetime(2025, 12, 12, tzinfo=timezone.utc), datetime(2026, 3, 13, tzinfo=timezone.utc)),
        (datetime(2026, 9, 11, tzinfo=timezone.utc), datetime(2026, 3, 13, tzinfo=timezone.utc)),  # fetched out of order
        (datetime(2026, 9, 11, tzinfo=timezone.utc), datetime(2026, 9, 11, tzinfo=timezone.utc)),  # one backfill instant
    ])
    def test_order_is_fiscal_whatever_the_fetch_order(self, older_fetched, newer_fetched):
        knowledge = extract_earnings_call_knowledge(self._two_calls(older_fetched, newer_fetched))
        assert [t.quarter for t in knowledge.transcripts] == ["2025Q3", "2025Q4"]
        change = compute_change_intelligence(knowledge)
        assert (change.previous_quarter, change.current_quarter) == ("2025Q3", "2025Q4")

    def test_executive_windows_are_fiscal_periods(self):
        records = (
            legacy_statement("2025Q3", "Update.", speaker="Alice", title="CEO",
                             published_at=datetime(2026, 9, 11, tzinfo=timezone.utc), period_end=date(2025, 9, 30)),
            legacy_statement("2025Q4", "Update.", speaker="Alice", title="CEO",
                             published_at=datetime(2026, 3, 13, tzinfo=timezone.utc), period_end=date(2025, 12, 31)),
        )
        (alice,) = extract_executive_change_intelligence("NVDA", extract_earnings_call_knowledge(records)).executives
        assert (alice.first_observed_period, alice.last_observed_period) == ("2025Q3", "2025Q4")


class TestNoOutcomeFromAnUnknownDate:
    def test_guidance_and_commitments_resolve_to_insufficient_evidence(self):
        records = tuple(fiscal_year(2015 + i, revenue=1000.0, net_income=100.0 + i * 30) for i in range(6)) + (
            legacy_statement("2015Q4", "We expect margin expansion in coming years.",
                             published_at=datetime(2016, 1, 1, tzinfo=timezone.utc), period_end=date(2015, 12, 31)),
        )
        fsh = extract_financial_statement_history(records)
        cah = extract_capital_allocation_history(records)
        growth = extract_growth_knowledge(fsh)
        knowledge = extract_earnings_call_knowledge(records)
        (item,) = extract_management_guidance(knowledge, fsh, growth, cah).guidance_items
        assert (item.outcome, item.status) == (GuidanceOutcome.INSUFFICIENT_EVIDENCE, GuidanceStatus.UNRESOLVED)
        (commitment,) = extract_management_credibility(knowledge, fsh, growth, cah).commitments
        assert commitment.outcome is CommitmentOutcome.INSUFFICIENT_EVIDENCE


class TestDailyBriefExecutiveChange:
    def test_an_executive_change_seen_on_a_call_has_no_invented_since(self):
        records = (
            legacy_statement("2025Q3", "Update.", speaker="Alice", title="CEO", **NVDA_Q3),
            legacy_statement("2025Q4", "Update.", speaker="Dave", title="CEO", index=1,
                             published_at=datetime(2026, 3, 13, tzinfo=timezone.utc), period_end=date(2025, 12, 31)),
        )
        events = extract_executive_change_intelligence("NVDA", extract_earnings_call_knowledge(records)).leadership_changes
        latest = [e for e in events if e.source_transcript == "2025Q4"]
        assert latest and all(e.effective_date is None for e in latest)
        signal = executive_change_signal(latest[0].role_category, "reason", None)
        assert signal.since is None

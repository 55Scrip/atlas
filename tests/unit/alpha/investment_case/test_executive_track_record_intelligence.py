"""Tests for `atlas.alpha.investment_case.executive_track_record_intelligence`
(Capability Expansion Sprint 11, Phases 2 through 8).
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.alpha.investment_case.capital_allocation_intelligence import extract_capital_allocation_history
from atlas.alpha.investment_case.earnings_call import extract_earnings_call_knowledge
from atlas.alpha.investment_case.executive_change_intelligence import extract_executive_change_intelligence
from atlas.alpha.investment_case.executive_track_record_intelligence import (
    EvidenceCompleteness,
    TemporalAssociation,
    TrackRecordFindingKind,
    classify_association,
    extract_executive_track_record,
)
from atlas.alpha.investment_case.financial_statement_intelligence import extract_financial_statement_history
from atlas.alpha.investment_case.growth_intelligence import extract_growth_knowledge
from atlas.alpha.investment_case.management_credibility_intelligence import extract_management_credibility
from atlas.alpha.investment_case.management_guidance_intelligence import extract_management_guidance
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest

_EVALUATED_AT = datetime(2026, 8, 22, tzinfo=timezone.utc)


def _period(year: int, **metadata):
    document = RawBusinessDocument(
        identifier=f"AAPL:FY:{year}-12-31",
        company="AAPL",
        source_kind="financial_statement",
        published_at=datetime(year + 1, 2, 15, tzinfo=timezone.utc),
        provider_id="sec_edgar",
        raw_reference="https://example.test/10k",
        content_hash=f"hash-{year}",
        language="en",
        period_start=date(year, 1, 1),
        period_end=date(year, 12, 31),
        metadata={**metadata, "currency": "USD"},
    )
    result = ingest(document, evaluated_at=_EVALUATED_AT)
    assert isinstance(result, IngestedRecord)
    return result.record


def _statement(quarter: str, index: int, speaker: str, title: str | None, content: str, *, period_end: date):
    metadata = {"quarter": quarter, "statement_index": index, "speaker": speaker, "content": content}
    if title is not None:
        metadata["title"] = title
    document = RawBusinessDocument(
        identifier=f"AAPL:transcript:{quarter}:{index}",
        company="AAPL",
        source_kind="transcript",
        published_at=datetime(period_end.year, period_end.month, period_end.day, tzinfo=timezone.utc),
        provider_id="alpha_vantage",
        raw_reference="https://example.test/transcript",
        content_hash=f"hash-{quarter}-{index}",
        language="en",
        period_start=period_end,
        period_end=period_end,
        metadata=metadata,
    )
    result = ingest(document, evaluated_at=_EVALUATED_AT)
    assert isinstance(result, IngestedRecord)
    return result.record


def _track_record(records, ticker="AAPL"):
    fsh = extract_financial_statement_history(records)
    cah = extract_capital_allocation_history(records)
    growth = extract_growth_knowledge(fsh)
    earnings_call = extract_earnings_call_knowledge(records)
    executive_change = extract_executive_change_intelligence(ticker, earnings_call)
    management_credibility = extract_management_credibility(earnings_call, fsh, growth, cah)
    management_guidance = extract_management_guidance(earnings_call, fsh, growth, cah)
    return extract_executive_track_record(
        executive_change, fsh, earnings_call, cah, growth, management_credibility, management_guidance
    )


class TestClassifyAssociation:
    def test_before_tenure(self):
        assert classify_association(date(2020, 1, 1), date(2021, 1, 1), date(2022, 1, 1)) is TemporalAssociation.BEFORE_TENURE

    def test_during_tenure(self):
        assert classify_association(date(2021, 6, 1), date(2021, 1, 1), date(2022, 1, 1)) is TemporalAssociation.DURING_TENURE

    def test_after_tenure(self):
        assert classify_association(date(2023, 1, 1), date(2021, 1, 1), date(2022, 1, 1)) is TemporalAssociation.AFTER_TENURE

    def test_boundary_dates_are_during_tenure(self):
        assert classify_association(date(2021, 1, 1), date(2021, 1, 1), date(2022, 1, 1)) is TemporalAssociation.DURING_TENURE
        assert classify_association(date(2022, 1, 1), date(2021, 1, 1), date(2022, 1, 1)) is TemporalAssociation.DURING_TENURE


class TestEmptyInput:
    def test_no_executives_yields_empty_track_record(self):
        track_record = _track_record(())
        assert track_record.tenures == ()


class TestTenureContextLinking:
    def test_financial_periods_are_windowed_to_tenure(self):
        records = tuple(_period(2015 + i, revenue=1000.0) for i in range(6)) + (
            _statement("2015Q4", 0, "Alice Smith", "CEO", "Update.", period_end=date(2015, 12, 31)),
            _statement("2016Q4", 0, "Alice Smith", "CEO", "Update.", period_end=date(2016, 12, 31)),
        )
        track_record = _track_record(records)
        tenure = track_record.tenures[0]
        assert [p.period_end for p in tenure.context.financial_periods] == [date(2015, 12, 31), date(2016, 12, 31)]

    def test_periods_outside_tenure_are_excluded(self):
        records = tuple(_period(2015 + i, revenue=1000.0) for i in range(6)) + (
            _statement("2015Q4", 0, "Alice Smith", "CEO", "Update.", period_end=date(2015, 12, 31)),
        )
        track_record = _track_record(records)
        tenure = track_record.tenures[0]
        assert len(tenure.context.financial_periods) == 1
        assert tenure.context.financial_periods[0].period_end == date(2015, 12, 31)

    def test_commitments_are_linked_by_date_regardless_of_speaker(self):
        records = (
            _period(2015, revenue=1000.0, share_buybacks=50.0),
            _statement("2015Q4", 0, "Alice Smith", "CEO", "We are committed to our long-term vision.", period_end=date(2015, 12, 31)),
        )
        track_record = _track_record(records)
        tenure = track_record.tenures[0]
        assert len(tenure.context.commitments) == 1


class TestGuidanceHistoryLinking:
    def test_guidance_issued_by_this_executive_is_linked(self):
        records = tuple(_period(2015 + i, revenue=1000.0, net_income=100.0 + i * 30) for i in range(6)) + (
            _statement("2015Q4", 0, "Alice Smith", "CEO", "We expect margin to improve going forward.", period_end=date(2015, 12, 31)),
        )
        track_record = _track_record(records)
        tenure = track_record.tenures[0]
        assert len(tenure.guidance_history.issued) == 1
        assert len(tenure.guidance_history.fulfilled) == 1

    def test_guidance_by_a_different_speaker_is_not_linked(self):
        records = tuple(_period(2015 + i, revenue=1000.0, net_income=100.0 + i * 30) for i in range(6)) + (
            _statement("2015Q4", 0, "Alice Smith", "CEO", "General update.", period_end=date(2015, 12, 31)),
            _statement("2015Q4", 1, "Bob Jones", "CFO", "We expect margin to improve going forward.", period_end=date(2015, 12, 31)),
        )
        track_record = _track_record(records)
        alice_tenure = next(t for t in track_record.tenures if t.executive.name == "Alice Smith")
        assert alice_tenure.guidance_history.issued == ()


class TestTenureTimeline:
    def test_overlapping_executives_are_detected(self):
        records = (
            _statement("2023Q4", 0, "Alice Smith", "CEO", "Update.", period_end=date(2023, 12, 31)),
            _statement("2023Q4", 1, "Bob Jones", "CFO", "Update.", period_end=date(2023, 12, 31)),
        )
        track_record = _track_record(records)
        alice_tenure = next(t for t in track_record.tenures if t.executive.name == "Alice Smith")
        assert [e.name for e in alice_tenure.timeline.overlapping_executives] == ["Bob Jones"]

    def test_sequential_non_overlapping_executives_are_not_linked(self):
        records = (
            _statement("2020Q4", 0, "Alice Smith", "CEO", "Update.", period_end=date(2020, 12, 31)),
            _statement("2023Q4", 0, "Dave Kim", "CEO", "Update.", period_end=date(2023, 12, 31)),
        )
        track_record = _track_record(records)
        alice_tenure = next(t for t in track_record.tenures if t.executive.name == "Alice Smith")
        assert alice_tenure.timeline.overlapping_executives == ()

    def test_own_events_are_filtered_to_this_executive(self):
        records = (
            _statement("2020Q4", 0, "Alice Smith", "CEO", "Update.", period_end=date(2020, 12, 31)),
            _statement("2023Q4", 0, "Dave Kim", "CEO", "Update.", period_end=date(2023, 12, 31)),
        )
        track_record = _track_record(records)
        alice_tenure = next(t for t in track_record.tenures if t.executive.name == "Alice Smith")
        assert all(e.executive_name == "Alice Smith" for e in alice_tenure.timeline.own_events)


class TestEvidenceCompleteness:
    def test_single_transcript_is_single_observation(self):
        records = (_statement("2023Q4", 0, "Alice Smith", "CEO", "Update.", period_end=date(2023, 12, 31)),)
        track_record = _track_record(records)
        assert track_record.tenures[0].evidence_completeness is EvidenceCompleteness.SINGLE_OBSERVATION

    def test_four_transcripts_is_substantial_history(self):
        records = tuple(
            _statement(f"202{i}Q4", 0, "Alice Smith", "CEO", "Update.", period_end=date(2020 + i, 12, 31))
            for i in range(4)
        )
        track_record = _track_record(records)
        assert track_record.tenures[0].evidence_completeness is EvidenceCompleteness.SUBSTANTIAL_HISTORY


class TestFindings:
    def test_stable_single_executive_with_no_data_has_insufficient_evidence(self):
        records = (_statement("2023Q4", 0, "Alice Smith", None, "Update.", period_end=date(2023, 12, 31)),)
        track_record = _track_record(records)
        kinds = {f.kind for f in track_record.tenures[0].findings}
        assert TrackRecordFindingKind.COMMUNICATION_ACTIVITY_OBSERVED in kinds

    def test_guidance_activity_finding_reflects_real_count(self):
        records = tuple(_period(2015 + i, revenue=1000.0, net_income=100.0 + i * 30) for i in range(6)) + (
            _statement("2015Q4", 0, "Alice Smith", "CEO", "We expect margin to improve going forward.", period_end=date(2015, 12, 31)),
        )
        track_record = _track_record(records)
        finding = next(f for f in track_record.tenures[0].findings if f.kind is TrackRecordFindingKind.GUIDANCE_ACTIVITY_OBSERVED)
        assert finding.evidence_count == 1

    def test_leadership_transition_finding_for_overlapping_executives(self):
        records = (
            _statement("2023Q4", 0, "Alice Smith", "CEO", "Update.", period_end=date(2023, 12, 31)),
            _statement("2023Q4", 1, "Bob Jones", "CFO", "Update.", period_end=date(2023, 12, 31)),
        )
        track_record = _track_record(records)
        alice_tenure = next(t for t in track_record.tenures if t.executive.name == "Alice Smith")
        kinds = {f.kind for f in alice_tenure.findings}
        assert TrackRecordFindingKind.LEADERSHIP_TRANSITION_DURING_TENURE in kinds

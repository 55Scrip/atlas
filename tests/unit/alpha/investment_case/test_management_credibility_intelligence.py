"""Tests for `atlas.alpha.investment_case.management_credibility_intelligence`
(Capability Expansion Sprint 8, Phases 2 through 7).
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.alpha.investment_case.capital_allocation_intelligence import extract_capital_allocation_history
from atlas.alpha.investment_case.earnings_call import extract_earnings_call_knowledge
from atlas.alpha.investment_case.financial_statement_intelligence import extract_financial_statement_history
from atlas.alpha.investment_case.growth_intelligence import extract_growth_knowledge
from atlas.alpha.investment_case.management_credibility_intelligence import (
    CommitmentCategory,
    CommitmentOutcome,
    CommitmentSignal,
    CommunicationDirection,
    CredibilityFindingKind,
    ExecutionConsistency,
    GuidanceRevisionDirection,
    extract_management_commitments,
    extract_management_credibility,
)
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest

_EVALUATED_AT = datetime(2026, 8, 22, tzinfo=timezone.utc)


def _statement(quarter: str, index: int, speaker: str, content: str, *, period_end: date, sentiment=None):
    metadata = {"quarter": quarter, "statement_index": index, "speaker": speaker, "content": content}
    if sentiment is not None:
        metadata["sentiment"] = sentiment
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


def _credibility(records):
    fsh = extract_financial_statement_history(records)
    cah = extract_capital_allocation_history(records)
    growth = extract_growth_knowledge(fsh)
    earnings_call = extract_earnings_call_knowledge(records)
    return extract_management_credibility(earnings_call, fsh, growth, cah)


class TestEmptyInput:
    def test_no_transcripts_yields_insufficient_everywhere(self):
        credibility = _credibility(())
        assert credibility.commitments == ()
        assert credibility.communication_consistency.direction is CommunicationDirection.INSUFFICIENT_DATA
        assert credibility.execution_consistency is ExecutionConsistency.INSUFFICIENT_EVIDENCE
        assert credibility.findings[0].kind is CredibilityFindingKind.INSUFFICIENT_HISTORY


class TestCommitmentExtraction:
    def test_a_statement_with_no_commitment_signal_is_not_extracted(self):
        records = (_statement("2023Q4", 0, "CEO", "Our customers love the new product.", period_end=date(2023, 12, 31)),)
        commitments = extract_management_commitments(
            extract_earnings_call_knowledge(records), extract_financial_statement_history(records),
            extract_growth_knowledge(extract_financial_statement_history(records)),
            extract_capital_allocation_history(records),
        )
        assert commitments == ()

    def test_margin_guidance_statement_is_extracted_with_full_provenance(self):
        records = (
            _statement(
                "2023Q4", 0, "CFO", "We expect gross margin to expand next year.", period_end=date(2023, 12, 31),
            ),
        )
        commitments = extract_management_commitments(
            extract_earnings_call_knowledge(records), extract_financial_statement_history(records),
            extract_growth_knowledge(extract_financial_statement_history(records)),
            extract_capital_allocation_history(records),
        )
        assert len(commitments) == 1
        commitment = commitments[0]
        assert commitment.signal is CommitmentSignal.GUIDANCE
        assert commitment.commitment_category is CommitmentCategory.MARGIN
        assert commitment.speaker == "CFO"
        assert commitment.reporting_period == "2023Q4"
        assert commitment.source_transcript == "2023Q4"
        assert commitment.supporting_quotation == "We expect gross margin to expand next year."
        assert commitment.revision_direction is None

    def test_general_commitment_with_no_metric_topic_is_category_general(self):
        records = (_statement("2023Q4", 0, "CEO", "We are committed to our long-term vision.", period_end=date(2023, 12, 31)),)
        commitments = extract_management_commitments(
            extract_earnings_call_knowledge(records), extract_financial_statement_history(records),
            extract_growth_knowledge(extract_financial_statement_history(records)),
            extract_capital_allocation_history(records),
        )
        assert commitments[0].commitment_category is CommitmentCategory.GENERAL
        assert commitments[0].outcome is CommitmentOutcome.INSUFFICIENT_EVIDENCE

    def test_guidance_revision_raised_is_detected(self):
        records = (
            _statement("2023Q4", 0, "CFO", "We are raising our outlook for the full year.", period_end=date(2023, 12, 31)),
        )
        commitments = extract_management_commitments(
            extract_earnings_call_knowledge(records), extract_financial_statement_history(records),
            extract_growth_knowledge(extract_financial_statement_history(records)),
            extract_capital_allocation_history(records),
        )
        assert commitments[0].signal is CommitmentSignal.GUIDANCE_REVISION
        assert commitments[0].revision_direction is GuidanceRevisionDirection.RAISED

    def test_guidance_revision_lowered_is_detected(self):
        records = (
            _statement("2023Q4", 0, "CFO", "We are reducing our outlook for next quarter.", period_end=date(2023, 12, 31)),
        )
        commitments = extract_management_commitments(
            extract_earnings_call_knowledge(records), extract_financial_statement_history(records),
            extract_growth_knowledge(extract_financial_statement_history(records)),
            extract_capital_allocation_history(records),
        )
        assert commitments[0].revision_direction is GuidanceRevisionDirection.LOWERED


class TestOutcomeComparison:
    def test_no_subsequent_periods_is_no_observable_outcome_yet(self):
        records = (
            _period(2020, revenue=1000.0, gross_profit=500.0, operating_income=300.0, net_income=100.0),
            _statement("2020Q4", 0, "CFO", "We expect margin expansion.", period_end=date(2020, 12, 31)),
        )
        commitments = extract_management_commitments(
            extract_earnings_call_knowledge(records), extract_financial_statement_history(records),
            extract_growth_knowledge(extract_financial_statement_history(records)),
            extract_capital_allocation_history(records),
        )
        assert commitments[0].outcome is CommitmentOutcome.NO_OBSERVABLE_OUTCOME_YET

    def test_margin_commitment_is_fulfilled_when_net_margin_rises_afterward(self):
        records = tuple(
            _period(2015 + i, revenue=1000.0, net_income=100.0 + i * 30) for i in range(6)
        ) + (
            _statement("2015Q4", 0, "CFO", "We expect margin expansion in coming years.", period_end=date(2015, 12, 31)),
        )
        commitments = extract_management_commitments(
            extract_earnings_call_knowledge(records), extract_financial_statement_history(records),
            extract_growth_knowledge(extract_financial_statement_history(records)),
            extract_capital_allocation_history(records),
        )
        assert commitments[0].outcome is CommitmentOutcome.FULFILLED

    def test_cost_commitment_is_unresolved_when_operating_margin_falls_afterward(self):
        records = tuple(
            _period(2015 + i, revenue=1000.0, operating_income=300.0 - i * 30) for i in range(6)
        ) + (
            _statement("2015Q4", 0, "CFO", "We are committed to cost discipline going forward.", period_end=date(2015, 12, 31)),
        )
        commitments = extract_management_commitments(
            extract_earnings_call_knowledge(records), extract_financial_statement_history(records),
            extract_growth_knowledge(extract_financial_statement_history(records)),
            extract_capital_allocation_history(records),
        )
        assert commitments[0].commitment_category is CommitmentCategory.COST_REDUCTION
        assert commitments[0].outcome is CommitmentOutcome.UNRESOLVED

    def test_capital_allocation_commitment_is_partially_fulfilled_with_mixed_signals(self):
        records = tuple(
            _period(2015 + i, revenue=1000.0, share_buybacks=50.0 + i * 20, dividends=100.0 - i * 15) for i in range(6)
        ) + (
            _statement("2015Q4", 0, "CFO", "We are committed to our share repurchase program and dividend.", period_end=date(2015, 12, 31)),
        )
        commitments = extract_management_commitments(
            extract_earnings_call_knowledge(records), extract_financial_statement_history(records),
            extract_growth_knowledge(extract_financial_statement_history(records)),
            extract_capital_allocation_history(records),
        )
        assert commitments[0].commitment_category is CommitmentCategory.CAPITAL_ALLOCATION
        assert commitments[0].outcome is CommitmentOutcome.PARTIALLY_FULFILLED


class TestCommunicationConsistency:
    def test_single_transcript_is_insufficient_data(self):
        records = (_statement("2023Q4", 0, "CEO", "Our strategy remains focused.", period_end=date(2023, 12, 31)),)
        credibility = _credibility(records)
        assert credibility.communication_consistency.direction is CommunicationDirection.INSUFFICIENT_DATA

    def test_guidance_changed_flag_reflects_real_guidance_revision_statement(self):
        records = (
            _statement("2023Q3", 0, "CFO", "Business is steady.", period_end=date(2023, 9, 30)),
            _statement("2023Q4", 0, "CFO", "We are raising our outlook for the year.", period_end=date(2023, 12, 31)),
        )
        credibility = _credibility(records)
        assert credibility.communication_consistency.guidance_changed is True


class TestGuidanceReliability:
    def test_withdrawn_guidance_count_reflects_lowered_revisions(self):
        records = (
            _statement("2023Q4", 0, "CFO", "We are reducing our outlook for next quarter.", period_end=date(2023, 12, 31)),
        )
        credibility = _credibility(records)
        assert credibility.guidance_reliability.withdrawn_guidance_count == 1
        assert len(credibility.guidance_reliability.guidance_revisions) == 1

    def test_guidance_history_includes_both_guidance_and_revisions(self):
        records = (
            _statement("2023Q4", 0, "CFO", "We expect strong growth for the full year.", period_end=date(2023, 12, 31)),
            _statement("2023Q4", 1, "CFO", "We are raising our outlook.", period_end=date(2023, 12, 31)),
        )
        credibility = _credibility(records)
        assert len(credibility.guidance_reliability.guidance_history) == 2


class TestExecutionConsistencyAndFindings:
    def test_all_fulfilled_commitments_yield_strong_follow_through(self):
        records = tuple(
            _period(2015 + i, revenue=1000.0, net_income=100.0 + i * 30) for i in range(6)
        ) + (
            _statement("2015Q4", 0, "CFO", "We expect margin expansion in coming years.", period_end=date(2015, 12, 31)),
        )
        credibility = _credibility(records)
        assert credibility.execution_consistency is ExecutionConsistency.STRONG_FOLLOW_THROUGH
        kinds = {f.kind for f in credibility.findings}
        assert CredibilityFindingKind.CONSISTENT_FOLLOW_THROUGH in kinds

    def test_every_finding_with_commitments_names_them(self):
        records = tuple(
            _period(2015 + i, revenue=1000.0, net_income=100.0 + i * 30) for i in range(6)
        ) + (
            _statement("2015Q4", 0, "CFO", "We expect margin expansion in coming years.", period_end=date(2015, 12, 31)),
        )
        credibility = _credibility(records)
        for finding in credibility.findings:
            if finding.kind is CredibilityFindingKind.CONSISTENT_FOLLOW_THROUGH:
                assert len(finding.supporting_commitments) > 0

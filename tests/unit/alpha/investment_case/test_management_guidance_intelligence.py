"""Tests for `atlas.alpha.investment_case.management_guidance_intelligence`
(Capability Expansion Sprint 9, Phases 2 through 7).
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.alpha.investment_case.capital_allocation_intelligence import extract_capital_allocation_history
from atlas.alpha.investment_case.earnings_call import extract_earnings_call_knowledge
from atlas.alpha.investment_case.financial_statement_intelligence import extract_financial_statement_history
from atlas.alpha.investment_case.growth_intelligence import extract_growth_knowledge
from atlas.alpha.investment_case.management_guidance_intelligence import (
    ConfidenceWording,
    GuidanceDirection,
    GuidanceOutcome,
    GuidanceStatus,
    GuidanceType,
    RevisionKind,
    TargetUnit,
    extract_management_guidance,
)
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest

_EVALUATED_AT = datetime(2026, 8, 22, tzinfo=timezone.utc)


def _statement(quarter: str, index: int, speaker: str, content: str, *, period_end: date):
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
        metadata={"quarter": quarter, "statement_index": index, "speaker": speaker, "content": content},
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


def _guidance(records):
    fsh = extract_financial_statement_history(records)
    cah = extract_capital_allocation_history(records)
    growth = extract_growth_knowledge(fsh)
    earnings_call = extract_earnings_call_knowledge(records)
    return extract_management_guidance(earnings_call, fsh, growth, cah)


class TestEmptyInput:
    def test_no_transcripts_yields_empty_timeline(self):
        guidance = _guidance(())
        assert guidance.guidance_items == ()
        assert guidance.reliability.total_guidance_count == 0


class TestExtractionAndClassification:
    def test_non_guidance_statement_is_not_extracted(self):
        records = (_statement("2023Q4", 0, "CEO", "Our customers love the new product.", period_end=date(2023, 12, 31)),)
        guidance = _guidance(records)
        assert guidance.guidance_items == ()

    def test_margin_guidance_is_classified_correctly(self):
        records = (_statement("2023Q4", 0, "CFO", "We expect gross margin to expand next year.", period_end=date(2023, 12, 31)),)
        guidance = _guidance(records)
        assert guidance.guidance_items[0].guidance_type is GuidanceType.MARGIN
        assert guidance.guidance_items[0].direction is GuidanceDirection.INCREASE

    def test_revenue_keyword_is_classified_as_revenue(self):
        records = (_statement("2023Q4", 0, "CFO", "We expect revenue to grow next year.", period_end=date(2023, 12, 31)),)
        guidance = _guidance(records)
        assert guidance.guidance_items[0].guidance_type is GuidanceType.REVENUE

    def test_eps_per_share_target_is_extracted(self):
        records = (_statement("2023Q4", 0, "CFO", "We expect EPS of $1.50 per share this year.", period_end=date(2023, 12, 31)),)
        guidance = _guidance(records)
        item = guidance.guidance_items[0]
        assert item.guidance_type is GuidanceType.EPS
        assert item.explicit_target.value == 1.5
        assert item.explicit_target.unit is TargetUnit.USD_PER_SHARE

    def test_percent_range_is_extracted(self):
        records = (_statement("2023Q4", 0, "CFO", "We expect revenue growth of 8% to 10% next year.", period_end=date(2023, 12, 31)),)
        guidance = _guidance(records)
        item = guidance.guidance_items[0]
        assert item.explicit_target_range.low == 8.0
        assert item.explicit_target_range.high == 10.0
        assert item.explicit_target is None
        assert item.direction is GuidanceDirection.RANGE

    def test_dollar_billion_target_is_extracted(self):
        records = (_statement("2023Q4", 0, "CFO", "We expect free cash flow of $3 billion this year.", period_end=date(2023, 12, 31)),)
        guidance = _guidance(records)
        item = guidance.guidance_items[0]
        assert item.guidance_type is GuidanceType.FREE_CASH_FLOW
        assert item.explicit_target.value == 3.0
        assert item.explicit_target.unit is TargetUnit.USD_BILLION

    def test_no_numeric_pattern_leaves_target_absent(self):
        records = (_statement("2023Q4", 0, "CFO", "We expect margin to improve going forward.", period_end=date(2023, 12, 31)),)
        guidance = _guidance(records)
        item = guidance.guidance_items[0]
        assert item.explicit_target is None
        assert item.explicit_target_range is None

    def test_confidence_wording_is_detected(self):
        records = (_statement("2023Q4", 0, "CFO", "We are confident in our margin outlook.", period_end=date(2023, 12, 31)),)
        guidance = _guidance(records)
        assert guidance.guidance_items[0].confidence_wording is ConfidenceWording.CONFIDENT

    def test_withdrawal_is_detected(self):
        records = (_statement("2023Q4", 0, "CFO", "We are withdrawing our guidance for the year given uncertainty.", period_end=date(2023, 12, 31)),)
        guidance = _guidance(records)
        assert guidance.guidance_items[0].status is GuidanceStatus.WITHDRAWN


class TestOutcomeLinking:
    def test_no_subsequent_period_is_unresolved(self):
        records = (
            _period(2020, revenue=1000.0),
            _statement("2020Q4", 0, "CFO", "We expect revenue to increase next year.", period_end=date(2020, 12, 31)),
        )
        guidance = _guidance(records)
        assert guidance.guidance_items[0].outcome is GuidanceOutcome.UNRESOLVED
        assert guidance.guidance_items[0].status is GuidanceStatus.ACTIVE

    def test_range_direction_is_always_insufficient_evidence(self):
        records = tuple(_period(2015 + i, revenue=1000.0 + i * 100) for i in range(6)) + (
            _statement("2015Q4", 0, "CFO", "We expect revenue growth of 8% to 10%.", period_end=date(2015, 12, 31)),
        )
        guidance = _guidance(records)
        assert guidance.guidance_items[0].outcome is GuidanceOutcome.INSUFFICIENT_EVIDENCE

    def test_favorable_direction_fulfilled(self):
        records = tuple(_period(2015 + i, revenue=1000.0, net_income=100.0 + i * 30) for i in range(6)) + (
            _statement("2015Q4", 0, "CFO", "We expect margin to improve going forward.", period_end=date(2015, 12, 31)),
        )
        guidance = _guidance(records)
        assert guidance.guidance_items[0].outcome is GuidanceOutcome.FULFILLED
        assert guidance.guidance_items[0].status is GuidanceStatus.COMPLETED

    def test_unfavorable_direction_is_missed(self):
        records = tuple(_period(2015 + i, revenue=1000.0 - i * 80) for i in range(6)) + (
            _statement("2015Q4", 0, "CFO", "We expect revenue to increase substantially.", period_end=date(2015, 12, 31)),
        )
        guidance = _guidance(records)
        assert guidance.guidance_items[0].outcome is GuidanceOutcome.MISSED

    def test_decrease_direction_favorable_when_metric_falls(self):
        records = tuple(_period(2015 + i, revenue=1000.0, capital_expenditure=300.0 - i * 40) for i in range(6)) + (
            _statement("2015Q4", 0, "CFO", "We expect to decrease capital expenditure going forward.", period_end=date(2015, 12, 31)),
        )
        guidance = _guidance(records)
        assert guidance.guidance_items[0].guidance_type is GuidanceType.CAPITAL_EXPENDITURE
        assert guidance.guidance_items[0].outcome is GuidanceOutcome.FULFILLED


class TestTimelineAndRevisions:
    def test_first_guidance_in_group_is_initial(self):
        records = (_statement("2023Q4", 0, "CFO", "We expect revenue growth of 8% to 10%.", period_end=date(2023, 12, 31)),)
        guidance = _guidance(records)
        assert guidance.guidance_items[0].revision_kind is RevisionKind.INITIAL

    def test_later_range_with_higher_midpoint_is_raised(self):
        records = (
            _statement("2015Q4", 0, "CFO", "We expect revenue growth of 8% to 10% next year.", period_end=date(2015, 12, 31)),
            _statement("2016Q4", 0, "CFO", "We are raising our outlook to 12% to 14% revenue growth.", period_end=date(2016, 12, 31)),
        )
        guidance = _guidance(records)
        assert len(guidance.guidance_items) == 2
        assert guidance.guidance_items[0].status is GuidanceStatus.REVISED
        assert guidance.guidance_items[1].revision_kind is RevisionKind.RAISED

    def test_original_guidance_item_is_preserved_after_revision(self):
        records = (
            _statement("2015Q4", 0, "CFO", "We expect revenue growth of 8% to 10% next year.", period_end=date(2015, 12, 31)),
            _statement("2016Q4", 0, "CFO", "We are raising our outlook to 12% to 14% revenue growth.", period_end=date(2016, 12, 31)),
        )
        guidance = _guidance(records)
        assert guidance.guidance_items[0].explicit_target_range.low == 8.0
        assert guidance.guidance_items[0].explicit_target_range.high == 10.0

    def test_lower_numeric_target_is_lowered(self):
        records = (
            _statement("2015Q4", 0, "CFO", "We expect free cash flow of $5 billion this year.", period_end=date(2015, 12, 31)),
            _statement("2016Q4", 0, "CFO", "We expect free cash flow of $3 billion this year.", period_end=date(2016, 12, 31)),
        )
        guidance = _guidance(records)
        assert guidance.guidance_items[1].revision_kind is RevisionKind.LOWERED


class TestGuidanceReliability:
    def test_reliability_counts_match_items(self):
        records = tuple(_period(2015 + i, revenue=1000.0, net_income=100.0 + i * 30) for i in range(6)) + (
            _statement("2015Q4", 0, "CFO", "We expect margin to improve going forward.", period_end=date(2015, 12, 31)),
        )
        guidance = _guidance(records)
        assert guidance.reliability.total_guidance_count == 1
        assert guidance.reliability.fulfilled_count == 1

    def test_withdrawn_count_reflects_status(self):
        records = (_statement("2023Q4", 0, "CFO", "We are withdrawing our guidance for the year.", period_end=date(2023, 12, 31)),)
        guidance = _guidance(records)
        assert guidance.reliability.withdrawn_count == 1

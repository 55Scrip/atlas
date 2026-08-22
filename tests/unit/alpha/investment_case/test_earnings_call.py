"""Tests for `atlas.alpha.investment_case.earnings_call` (Capability
Expansion Sprint 2, Phases 1 + 3 + 4).
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.alpha.investment_case.earnings_call import (
    CommentaryCategory,
    EmphasisChange,
    SentimentTrend,
    compute_change_intelligence,
    extract_earnings_call_knowledge,
)
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest

_EVALUATED_AT = datetime(2026, 8, 22, tzinfo=timezone.utc)


def _statement(quarter: str, index: int, speaker: str, content: str, *, title: str | None = None, sentiment=None):
    metadata = {"quarter": quarter, "statement_index": index, "speaker": speaker, "content": content}
    if title is not None:
        metadata["title"] = title
    if sentiment is not None:
        metadata["sentiment"] = sentiment
    document = RawBusinessDocument(
        identifier=f"AAPL:transcript:{quarter}:{index}",
        company="AAPL",
        source_kind="transcript",
        published_at=_EVALUATED_AT,
        provider_id="alpha_vantage",
        raw_reference="https://example.test/transcript",
        content_hash=f"hash-{quarter}-{index}",
        language="en",
        period_start=date(2026, 3, 31) if quarter == "2026Q1" else date(2025, 12, 31),
        period_end=date(2026, 3, 31) if quarter == "2026Q1" else date(2025, 12, 31),
        metadata=metadata,
    )
    result = ingest(document, evaluated_at=_EVALUATED_AT)
    assert isinstance(result, IngestedRecord)
    return result.record


class TestExtractionOrganizesRawStatements:
    def test_no_transcript_records_produces_no_transcripts(self):
        knowledge = extract_earnings_call_knowledge(())
        assert knowledge.transcripts == ()

    def test_statements_are_grouped_by_quarter_and_ordered_by_index(self):
        records = (
            _statement("2026Q1", 1, "CFO", "Second statement."),
            _statement("2026Q1", 0, "CEO", "First statement."),
        )
        knowledge = extract_earnings_call_knowledge(records)
        assert len(knowledge.transcripts) == 1
        transcript = knowledge.transcripts[0]
        assert transcript.quarter == "2026Q1"
        assert [s.content for s in transcript.statements] == ["First statement.", "Second statement."]

    def test_content_is_preserved_verbatim(self):
        content = "We expect strong growth next quarter, driven by new products."
        records = (_statement("2026Q1", 0, "CEO", content, title="Chief Executive Officer"),)
        transcript = extract_earnings_call_knowledge(records).transcripts[0]
        statement = transcript.statements[0]
        assert statement.content == content
        assert statement.speaker == "CEO"
        assert statement.title == "Chief Executive Officer"

    def test_a_statement_matching_no_keyword_is_still_preserved(self):
        records = (_statement("2026Q1", 0, "Operator", "Good afternoon everyone, welcome to the call."),)
        transcript = extract_earnings_call_knowledge(records).transcripts[0]
        assert len(transcript.statements) == 1
        assert transcript.statements[0].categories == ()

    def test_transcripts_are_ordered_chronologically(self):
        records = (
            _statement("2026Q1", 0, "CEO", "Later statement."),
            _statement("2025Q4", 0, "CEO", "Earlier statement."),
        )
        knowledge = extract_earnings_call_knowledge(records)
        assert [t.quarter for t in knowledge.transcripts] == ["2025Q4", "2026Q1"]


class TestKeywordClassification:
    def test_guidance_language_is_tagged_management_guidance(self):
        records = (_statement("2026Q1", 0, "CFO", "For the full year, we expect revenue growth of 8%."),)
        statement = extract_earnings_call_knowledge(records).transcripts[0].statements[0]
        assert CommentaryCategory.MANAGEMENT_GUIDANCE in statement.categories

    def test_capital_allocation_language_is_tagged(self):
        records = (_statement("2026Q1", 0, "CFO", "We announced a new share repurchase program."),)
        statement = extract_earnings_call_knowledge(records).transcripts[0].statements[0]
        assert CommentaryCategory.CAPITAL_ALLOCATION_COMMENTARY in statement.categories

    def test_a_statement_can_match_multiple_categories(self):
        records = (
            _statement("2026Q1", 0, "CFO", "Our guidance reflects margin pressure from rising input costs."),
        )
        statement = extract_earnings_call_knowledge(records).transcripts[0].statements[0]
        assert CommentaryCategory.MANAGEMENT_GUIDANCE in statement.categories
        assert CommentaryCategory.MARGIN_COMMENTARY in statement.categories

    def test_a_question_is_tagged_open_questions_regardless_of_speaker(self):
        records = (_statement("2026Q1", 0, "Analyst", "Can you elaborate on the margin outlook?"),)
        statement = extract_earnings_call_knowledge(records).transcripts[0].statements[0]
        assert CommentaryCategory.OPEN_QUESTIONS in statement.categories

    def test_confidence_is_the_provider_reported_sentiment_unmodified(self):
        records = (_statement("2026Q1", 0, "CEO", "Business is strong.", sentiment=0.72),)
        statement = extract_earnings_call_knowledge(records).transcripts[0].statements[0]
        assert statement.confidence == 0.72

    def test_confidence_is_none_when_not_reported(self):
        records = (_statement("2026Q1", 0, "CEO", "Business is strong."),)
        statement = extract_earnings_call_knowledge(records).transcripts[0].statements[0]
        assert statement.confidence is None


class TestChangeIntelligence:
    def test_fewer_than_two_transcripts_is_insufficient(self):
        records = (_statement("2026Q1", 0, "CEO", "We expect growth."),)
        knowledge = extract_earnings_call_knowledge(records)
        change = compute_change_intelligence(knowledge)
        assert change.category_changes == ()
        assert change.previous_quarter is None
        assert change.current_quarter == "2026Q1"

    def test_a_category_newly_present_this_quarter_is_flagged(self):
        records = (
            _statement("2025Q4", 0, "CEO", "Business is steady."),
            _statement("2026Q1", 0, "CFO", "We announced a new share buyback program."),
        )
        change = compute_change_intelligence(extract_earnings_call_knowledge(records))
        capital_allocation = next(c for c in change.category_changes if c.category is CommentaryCategory.CAPITAL_ALLOCATION_COMMENTARY)
        assert capital_allocation.previous_statement_count == 0
        assert capital_allocation.current_statement_count == 1
        assert capital_allocation.emphasis_change is EmphasisChange.NEWLY_PRESENT

    def test_a_category_no_longer_present_is_flagged(self):
        records = (
            _statement("2025Q4", 0, "CFO", "We announced a new share buyback program."),
            _statement("2026Q1", 0, "CEO", "Business is steady."),
        )
        change = compute_change_intelligence(extract_earnings_call_knowledge(records))
        capital_allocation = next(c for c in change.category_changes if c.category is CommentaryCategory.CAPITAL_ALLOCATION_COMMENTARY)
        assert capital_allocation.emphasis_change is EmphasisChange.NO_LONGER_PRESENT

    def test_increased_emphasis_is_detected(self):
        previous = (_statement("2025Q4", 0, "CFO", "Margin was stable."),)
        current = tuple(_statement("2026Q1", i, "CFO", "Margin pressure continues.") for i in range(3))
        change = compute_change_intelligence(extract_earnings_call_knowledge(previous + current))
        margin = next(c for c in change.category_changes if c.category is CommentaryCategory.MARGIN_COMMENTARY)
        assert margin.previous_statement_count == 1
        assert margin.current_statement_count == 3
        assert margin.emphasis_change is EmphasisChange.INCREASED_EMPHASIS

    def test_rising_sentiment_is_detected(self):
        previous = (_statement("2025Q4", 0, "CEO", "For the full year, growth was modest.", sentiment=0.3),)
        current = (_statement("2026Q1", 0, "CEO", "For the full year, growth accelerated.", sentiment=0.8),)
        change = compute_change_intelligence(extract_earnings_call_knowledge(previous + current))
        guidance = next(c for c in change.category_changes if c.category is CommentaryCategory.MANAGEMENT_GUIDANCE)
        assert guidance.previous_average_confidence == 0.3
        assert guidance.current_average_confidence == 0.8
        assert guidance.sentiment_trend is SentimentTrend.RISING

    def test_stable_sentiment_with_no_reported_scores_is_insufficient_data(self):
        previous = (_statement("2025Q4", 0, "CEO", "For the full year, growth was modest."),)
        current = (_statement("2026Q1", 0, "CEO", "For the full year, growth accelerated."),)
        change = compute_change_intelligence(extract_earnings_call_knowledge(previous + current))
        guidance = next(c for c in change.category_changes if c.category is CommentaryCategory.MANAGEMENT_GUIDANCE)
        assert guidance.sentiment_trend is SentimentTrend.INSUFFICIENT_DATA

    def test_every_category_is_represented_in_the_comparison(self):
        previous = (_statement("2025Q4", 0, "CEO", "Business update."),)
        current = (_statement("2026Q1", 0, "CEO", "Business update."),)
        change = compute_change_intelligence(extract_earnings_call_knowledge(previous + current))
        categories_seen = {c.category for c in change.category_changes}
        assert categories_seen == set(CommentaryCategory)

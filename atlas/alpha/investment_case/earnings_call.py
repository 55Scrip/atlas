"""Earnings Call Knowledge Model + Structured Knowledge Extraction +
Change Intelligence (Capability Expansion Sprint 2: Earnings Call
Intelligence, Phases 1 + 3 + 4).

The transcript itself is not the product; understanding is. This
module never rewrites, summarizes, or generates a management statement
-- every `ManagementStatement.content` is the verbatim quote a real
`RawBusinessDocument` carried, and `categories`/`confidence` are the
only things added: a closed, keyword-anchored classification (never an
LLM call, never a semantic model -- this codebase has none, and this
sprint's own "extraction should prioritize factual management
statements over generated interpretation" instruction rules one out
even if it existed) and Alpha Vantage's own reported per-statement
sentiment score, passed through unmodified, never recomputed by Atlas.
A statement matching zero keyword categories is still preserved,
`categories=()` -- classification failure is never data loss.

**The keyword table (`_CATEGORY_KEYWORDS`) is a framework, not a
complete dataset** -- the identical "add a member, extend the mapping,
never touch the loop" discipline `KnowledgeDomain`/`_DOMAIN_EXTRACTORS`
already establish. A statement may match more than one category; `OPEN_
QUESTIONS` is the one structural (not keyword) category -- any verbatim
statement phrased as a question, regardless of speaker, since the
analyst's own wording is itself the traceable signal, not a claim about
whether management went on to answer it.

**Change Intelligence (Phase 4) compares real, computed signals across
the two most recent quarters -- never a generated narrative.** Two
things change per category: how much management said about it
(`statement_count`) and, where Alpha Vantage reported it, the average
sentiment of what they said (`average_confidence`). Both are named,
disclosed, categorical buckets over continuous numbers -- the same
"no fabricated score" discipline `historical_valuation.py`'s own
`ValuationTrend`/`ValuationStability` already establish, deliberately
mirrored in naming here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.sources import SourceKind

__all__ = [
    "CommentaryCategory",
    "ManagementStatement",
    "EarningsCallTranscript",
    "EarningsCallKnowledge",
    "EmphasisChange",
    "SentimentTrend",
    "CommentaryCategoryChange",
    "EarningsCallChangeIntelligence",
    "extract_earnings_call_knowledge",
    "compute_change_intelligence",
]


class CommentaryCategory(str, Enum):
    """Closed, growing -- see this module's own docstring. Mirrors the
    sprint brief's own list of reusable knowledge buckets verbatim."""

    MANAGEMENT_GUIDANCE = "management_guidance"
    STRATEGIC_PRIORITIES = "strategic_priorities"
    OPERATIONAL_PROGRESS = "operational_progress"
    CAPITAL_ALLOCATION_COMMENTARY = "capital_allocation_commentary"
    GROWTH_DRIVERS = "growth_drivers"
    MARGIN_COMMENTARY = "margin_commentary"
    COST_COMMENTARY = "cost_commentary"
    CUSTOMER_COMMENTARY = "customer_commentary"
    COMPETITIVE_COMMENTARY = "competitive_commentary"
    SUPPLY_CHAIN_COMMENTARY = "supply_chain_commentary"
    AI_COMMENTARY = "ai_commentary"
    MACROECONOMIC_COMMENTARY = "macroeconomic_commentary"
    REGULATORY_COMMENTARY = "regulatory_commentary"
    RISK_COMMENTARY = "risk_commentary"
    OPPORTUNITIES = "opportunities"
    OPEN_QUESTIONS = "open_questions"
    GUIDANCE_CHANGES = "guidance_changes"
    MANAGEMENT_COMMITMENTS = "management_commitments"


_CATEGORY_KEYWORDS: dict[CommentaryCategory, tuple[str, ...]] = {
    CommentaryCategory.MANAGEMENT_GUIDANCE: (
        "guidance", "we expect", "we anticipate", "outlook", "for the full year", "for next quarter",
    ),
    CommentaryCategory.STRATEGIC_PRIORITIES: (
        "strategic priority", "our strategy", "strategic focus", "long-term strategy",
    ),
    CommentaryCategory.OPERATIONAL_PROGRESS: ("operational", "execution", "we delivered", "on track"),
    CommentaryCategory.CAPITAL_ALLOCATION_COMMENTARY: (
        "capital allocation", "buyback", "share repurchase", "dividend", "return capital", "capital expenditure",
        "capex",
    ),
    CommentaryCategory.GROWTH_DRIVERS: ("growth driver", "drove growth", "key driver"),
    CommentaryCategory.MARGIN_COMMENTARY: ("margin", "gross margin", "operating margin"),
    CommentaryCategory.COST_COMMENTARY: ("cost discipline", "cost reduction", "operating expenses", "cost structure"),
    CommentaryCategory.CUSTOMER_COMMENTARY: ("customer demand", "our customers", "client demand"),
    CommentaryCategory.COMPETITIVE_COMMENTARY: ("competitor", "competitive", "competition", "market share"),
    CommentaryCategory.SUPPLY_CHAIN_COMMENTARY: ("supply chain", "supplier", "component shortage", "logistics"),
    CommentaryCategory.AI_COMMENTARY: ("artificial intelligence", "generative ai", "machine learning"),
    CommentaryCategory.MACROECONOMIC_COMMENTARY: (
        "macroeconomic", "macro environment", "inflation", "interest rate", "recession", "currency headwind",
    ),
    CommentaryCategory.REGULATORY_COMMENTARY: ("regulatory", "regulation", "compliance", "regulator"),
    CommentaryCategory.RISK_COMMENTARY: ("headwind", "challenge", "risk factor", "uncertain"),
    CommentaryCategory.OPPORTUNITIES: ("opportunity", "opportunities", "tailwind", "upside"),
    CommentaryCategory.GUIDANCE_CHANGES: (
        "raised guidance", "lowered guidance", "revised guidance", "updated guidance", "raising our outlook",
        "reducing our outlook",
    ),
    CommentaryCategory.MANAGEMENT_COMMITMENTS: ("we are committed", "we will continue to", "our commitment"),
}
"""`OPEN_QUESTIONS` deliberately has no entry -- see `_classify`'s own
structural (not keyword) rule for it."""


def _classify(content: str) -> tuple[CommentaryCategory, ...]:
    lowered = content.lower()
    matched = [
        category for category, keywords in _CATEGORY_KEYWORDS.items() if any(kw in lowered for kw in keywords)
    ]
    if "?" in content:
        matched.append(CommentaryCategory.OPEN_QUESTIONS)
    return tuple(matched)


@dataclass(frozen=True)
class ManagementStatement:
    speaker: str
    title: str | None
    content: str
    """Verbatim -- never rewritten, summarized, or paraphrased."""
    categories: tuple[CommentaryCategory, ...]
    confidence: float | None
    """Alpha Vantage's own reported per-statement sentiment, passed
    through unmodified -- `None` when the provider did not report one
    for this statement, never a default or an Atlas-computed guess."""


@dataclass(frozen=True)
class EarningsCallTranscript:
    quarter: str
    """Alpha Vantage's own format, e.g. `"2026Q2"`."""
    fiscal_date_ending: date | None
    published_at: date
    statements: tuple[ManagementStatement, ...]
    """In original transcript order -- never reordered by category."""


@dataclass(frozen=True)
class EarningsCallKnowledge:
    transcripts: tuple[EarningsCallTranscript, ...]
    """Chronological, oldest first. Empty, never fabricated, when no
    `TRANSCRIPT` record has been ingested yet."""


def _parse_confidence(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def extract_earnings_call_knowledge(business_records: tuple[BusinessRecord, ...]) -> EarningsCallKnowledge:
    """Pure, no I/O: groups every `TRANSCRIPT` record by its own
    `quarter` metadata, orders statements within a quarter by their own
    `statement_index` (the real ordering the provider fetched them in,
    never re-sorted by content), and classifies each statement's
    `content` via `_classify`. Generates no investment conclusion --
    organizes already-real, already-ingested facts into knowledge."""
    transcript_records = [r for r in business_records if r.document_type is SourceKind.TRANSCRIPT]

    by_quarter: dict[str, list[BusinessRecord]] = {}
    for record in transcript_records:
        quarter = record.metadata.get("quarter")
        if not isinstance(quarter, str):
            continue
        by_quarter.setdefault(quarter, []).append(record)

    transcripts: list[EarningsCallTranscript] = []
    for quarter, records in by_quarter.items():
        records.sort(key=lambda r: r.metadata.get("statement_index", 0))
        statements = tuple(
            ManagementStatement(
                speaker=str(r.metadata.get("speaker") or "unknown"),
                title=r.metadata.get("title") or None,
                content=str(r.metadata.get("content") or ""),
                categories=_classify(str(r.metadata.get("content") or "")),
                confidence=_parse_confidence(r.metadata.get("sentiment")),
            )
            for r in records
        )
        transcripts.append(
            EarningsCallTranscript(
                quarter=quarter,
                fiscal_date_ending=records[0].period_end,
                published_at=records[0].published_at.date(),
                statements=statements,
            )
        )

    transcripts.sort(key=lambda t: t.fiscal_date_ending or t.published_at)
    return EarningsCallKnowledge(transcripts=tuple(transcripts))


class EmphasisChange(str, Enum):
    """How much management said about one category, this quarter vs.
    the previous one -- a statement-count comparison, never a claim
    about what was said."""

    INCREASED_EMPHASIS = "increased_emphasis"
    DECREASED_EMPHASIS = "decreased_emphasis"
    STABLE_EMPHASIS = "stable_emphasis"
    NEWLY_PRESENT = "newly_present"
    NO_LONGER_PRESENT = "no_longer_present"
    INSUFFICIENT_DATA = "insufficient_data"


class SentimentTrend(str, Enum):
    """The average of Alpha Vantage's own reported sentiment for a
    category's statements, this quarter vs. the previous one -- mirrors
    `historical_valuation.ValuationTrend`'s own naming and "categorical
    bucket over a disclosed threshold" discipline."""

    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    INSUFFICIENT_DATA = "insufficient_data"


_EMPHASIS_CHANGE_THRESHOLD = 0.3
"""The relative statement-count change, as a fraction of the prior
quarter's own count, that counts as a real emphasis change rather than
noise -- disclosed, not fabricated (mirrors `historical_valuation
._TREND_THRESHOLD`'s own role)."""
_SENTIMENT_CHANGE_THRESHOLD = 0.1
"""The average-confidence gap that counts as a real sentiment change."""


def _emphasis_change(previous_count: int, current_count: int) -> EmphasisChange:
    if previous_count == 0 and current_count == 0:
        return EmphasisChange.INSUFFICIENT_DATA
    if previous_count == 0:
        return EmphasisChange.NEWLY_PRESENT
    if current_count == 0:
        return EmphasisChange.NO_LONGER_PRESENT
    relative_change = (current_count - previous_count) / previous_count
    if relative_change > _EMPHASIS_CHANGE_THRESHOLD:
        return EmphasisChange.INCREASED_EMPHASIS
    if relative_change < -_EMPHASIS_CHANGE_THRESHOLD:
        return EmphasisChange.DECREASED_EMPHASIS
    return EmphasisChange.STABLE_EMPHASIS


def _sentiment_trend(previous_average: float | None, current_average: float | None) -> SentimentTrend:
    if previous_average is None or current_average is None:
        return SentimentTrend.INSUFFICIENT_DATA
    delta = current_average - previous_average
    if delta > _SENTIMENT_CHANGE_THRESHOLD:
        return SentimentTrend.RISING
    if delta < -_SENTIMENT_CHANGE_THRESHOLD:
        return SentimentTrend.FALLING
    return SentimentTrend.STABLE


@dataclass(frozen=True)
class CommentaryCategoryChange:
    category: CommentaryCategory
    previous_statement_count: int
    current_statement_count: int
    previous_average_confidence: float | None
    current_average_confidence: float | None
    emphasis_change: EmphasisChange
    sentiment_trend: SentimentTrend


@dataclass(frozen=True)
class EarningsCallChangeIntelligence:
    previous_quarter: str | None
    current_quarter: str | None
    category_changes: tuple[CommentaryCategoryChange, ...]
    """Empty exactly when fewer than two transcripts are known --
    `INSUFFICIENT_DATA`, honestly, rather than a single-quarter
    baseline compared against nothing."""


def _average_confidence(statements: tuple[ManagementStatement, ...]) -> float | None:
    values = [s.confidence for s in statements if s.confidence is not None]
    if not values:
        return None
    return sum(values) / len(values)


def compute_change_intelligence(knowledge: EarningsCallKnowledge) -> EarningsCallChangeIntelligence:
    """Compares the two most recent transcripts only -- Phase 4's own
    "previous quarter -> current quarter" framing, never a longer
    rolling window this sprint does not ask for."""
    if len(knowledge.transcripts) < 2:
        quarter = knowledge.transcripts[-1].quarter if knowledge.transcripts else None
        return EarningsCallChangeIntelligence(previous_quarter=None, current_quarter=quarter, category_changes=())

    previous, current = knowledge.transcripts[-2], knowledge.transcripts[-1]
    changes: list[CommentaryCategoryChange] = []
    for category in CommentaryCategory:
        previous_statements = tuple(s for s in previous.statements if category in s.categories)
        current_statements = tuple(s for s in current.statements if category in s.categories)
        changes.append(
            CommentaryCategoryChange(
                category=category,
                previous_statement_count=len(previous_statements),
                current_statement_count=len(current_statements),
                previous_average_confidence=_average_confidence(previous_statements),
                current_average_confidence=_average_confidence(current_statements),
                emphasis_change=_emphasis_change(len(previous_statements), len(current_statements)),
                sentiment_trend=_sentiment_trend(
                    _average_confidence(previous_statements), _average_confidence(current_statements)
                ),
            )
        )

    return EarningsCallChangeIntelligence(
        previous_quarter=previous.quarter, current_quarter=current.quarter, category_changes=tuple(changes)
    )

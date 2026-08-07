"""Data model for the Portfolio Status report (ATLAS-015).

Every field here is either read verbatim from an existing record (Alpha
holding, Core Decision/Outcome/Observation, Alpha trade log entry) or a
deterministic count/threshold check over those records — never a score,
never a ranking, never AI-generated. See `atlas/alpha/portfolio_status
/__init__.py` for why this is not "Portfolio Intelligence" in the
`PortfolioIntelligenceCapability` sense.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class AttentionCategory(str, Enum):
    """The six deterministic gaps this module checks for. Each one is a
    state that already exists in Alpha/Core data -- nothing here is
    inferred or guessed. `MISSING_CASE` is the only one that halts
    further checks for a holding (nothing else can be evaluated without
    a Case to look inside)."""

    MISSING_CASE = "MISSING_CASE"
    DECISION_WITHOUT_OUTCOME = "DECISION_WITHOUT_OUTCOME"
    OUTCOME_WITHOUT_EXECUTION = "OUTCOME_WITHOUT_EXECUTION"
    AWAITING_RECONCILIATION = "AWAITING_RECONCILIATION"
    VERY_OLD_CASE = "VERY_OLD_CASE"
    OBSERVATION_WITHOUT_DECISION = "OBSERVATION_WITHOUT_DECISION"


@dataclass(frozen=True)
class AttentionItem:
    """One deterministic "needs a look" finding, always tied to a held
    ticker. `age_days` is populated only for `VERY_OLD_CASE`; every
    other category leaves it `None` rather than a fabricated number."""

    ticker: str
    category: AttentionCategory
    case_id: str | None
    age_days: int | None = None


@dataclass(frozen=True)
class ReviewQueueItem:
    """A ticker with at least one `AttentionItem`, in priority order.
    Priority is `reason_count` descending, then ticker ascending -- a
    fixed, deterministic sort, not a learned or AI ranking (explicitly
    out of scope for this sprint)."""

    ticker: str
    case_id: str | None
    reason_count: int
    top_category: AttentionCategory


@dataclass(frozen=True)
class PortfolioSummaryMetrics:
    """Concise counts for the top of the Portfolio page. Every field is
    either read straight from `AlphaPortfolioState`/`PortfolioSummary`
    (holdings_count, largest position, concentration, unallocated) or a
    count of `AttentionItem`s of one specific category (open_decisions =
    DECISION_WITHOUT_OUTCOME count, pending_outcomes =
    OUTCOME_WITHOUT_EXECUTION count, pending_executions =
    AWAITING_RECONCILIATION count) -- no new computation beyond counting
    what `AttentionItem` already found."""

    holdings_count: int
    largest_position_ticker: str | None
    largest_position_weight_percent: float | None
    number_of_investment_cases: int
    open_decisions: int
    pending_outcomes: int
    pending_executions: int
    concentration_level: str | None
    unallocated_percent: float | None


@dataclass(frozen=True)
class PortfolioHealthMetrics:
    """Known-data summary, not a score. `unknown_instrument_tickers` is a
    basic well-formedness check on the ticker string already persisted
    (letters/digits, optional "." or "-" share-class suffix) -- Atlas
    has no backend-side instrument registry (that resolution happens
    once, client-side, at Portfolio Import time; see
    `frontend/src/portfolio-import/instrumentRegistry.ts`), so this can
    only catch a ticker that looks structurally wrong, never confirm one
    is "real". It is deliberately conservative: everything that already
    passed Portfolio Import's own resolution will pass this too."""

    holdings_with_case_count: int
    holdings_count: int
    most_recent_decision_at: datetime | None
    outstanding_workflow_items: int
    allocated_percent: float | None
    unknown_instrument_tickers: tuple[str, ...]


@dataclass(frozen=True)
class PortfolioStatusReport:
    """The full report `PortfolioStatusService.build_report()` returns."""

    exists: bool
    summary: PortfolioSummaryMetrics | None
    attention_items: tuple[AttentionItem, ...]
    review_queue: tuple[ReviewQueueItem, ...]
    health: PortfolioHealthMetrics | None

    @classmethod
    def empty(cls) -> "PortfolioStatusReport":
        return cls(exists=False, summary=None, attention_items=(), review_queue=(), health=None)

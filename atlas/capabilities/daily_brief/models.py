"""Daily Brief capability models.

All types are immutable (frozen dataclasses). No external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DailyBriefPriority(str, Enum):
    """Explainable priority level for Daily Brief items.

    Priority means "deserves attention", not "requires action".
    """

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


@dataclass(frozen=True)
class DailyBriefItem:
    """A single item within a Daily Brief section."""

    title: str
    detail: str
    priority: DailyBriefPriority = DailyBriefPriority.LOW


@dataclass(frozen=True)
class DailyBriefObservation:
    """A calm, observational note with no implied action."""

    title: str
    detail: str


@dataclass(frozen=True)
class DailyBriefUnknown:
    """An unresolved question or missing piece of understanding."""

    question: str
    context: str = ""


@dataclass(frozen=True)
class DailyBriefEvidenceLink:
    """A reference to a specific piece of evidence or research."""

    ticker: str
    description: str


@dataclass(frozen=True)
class DailyBriefSection:
    """A structured section within a Daily Brief report."""

    title: str
    items: tuple[DailyBriefItem, ...]
    narrative: str = ""


@dataclass(frozen=True)
class DailyBriefSummary:
    """Opening summary of the daily brief."""

    bottom_line: str
    overall_priority: DailyBriefPriority
    item_count: int
    has_meaningful_developments: bool


@dataclass(frozen=True)
class DailyBriefInput:
    """All inputs to the Daily Brief capability.

    All fields are optional. The capability produces a calm no-developments
    report when nothing is supplied.
    """

    portfolio_summary: object | None = None
    research_notes: tuple = ()
    company_reports: tuple = ()
    watchlist_report: object | None = None
    discovery_report: object | None = None
    knowledge_node_count: int = 0
    open_research_questions: tuple[str, ...] = ()
    date_label: str = ""


@dataclass(frozen=True)
class DailyBriefReport:
    """Complete deterministic Daily Brief report."""

    title: str
    summary: DailyBriefSummary
    sections: tuple[DailyBriefSection, ...]
    unknowns: tuple[DailyBriefUnknown, ...]
    evidence_gaps: tuple[DailyBriefEvidenceLink, ...]
    next_research_steps: tuple[str, ...]
    knowledge_node_count: int = 0

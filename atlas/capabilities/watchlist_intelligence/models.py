from dataclasses import dataclass
from enum import Enum

from atlas.capabilities.company_analysis import CompanyAnalysisReport
from atlas.domains.knowledge import KnowledgeFact
from atlas.domains.research import ResearchProject
from atlas.shared import Company


class WatchlistStatus(str, Enum):
    """Research maturity state for a watchlist item."""

    OBSERVING = "observing"
    RESEARCHING = "researching"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"
    THESIS_FORMING = "thesis_forming"
    READY_FOR_REVIEW = "ready_for_review"
    PAUSED = "paused"
    ARCHIVED = "archived"


class WatchlistPriority(str, Enum):
    """Calm attention priority for watchlist items."""

    REVIEW = "deserves review"
    NEEDS_EVIDENCE = "needs more evidence"
    HAS_QUESTIONS = "has unresolved questions"
    INCOMPLETE = "research appears incomplete"
    MONITOR = "continue observing"
    PAUSED = "paused"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class WatchlistEvidenceLink:
    """Traceable evidence link used in watchlist intelligence."""

    id: str
    source: str
    description: str
    reference_id: str | None = None


@dataclass(frozen=True)
class WatchlistQuestion:
    """Question surfaced for a watchlist item."""

    id: str
    question: str
    status: str
    evidence_links: tuple[WatchlistEvidenceLink, ...] = ()


@dataclass(frozen=True)
class WatchlistUnknown:
    """Missing or unresolved information in a watchlist item."""

    title: str
    detail: str
    ticker: str
    evidence_links: tuple[WatchlistEvidenceLink, ...] = ()


@dataclass(frozen=True)
class WatchlistSignal:
    """Explainable signal used for prioritisation."""

    title: str
    detail: str
    score: int
    evidence_links: tuple[WatchlistEvidenceLink, ...] = ()


@dataclass(frozen=True)
class WatchlistObservation:
    """Structured observation about a watchlist item."""

    ticker: str
    title: str
    detail: str
    priority: WatchlistPriority
    signals: tuple[WatchlistSignal, ...] = ()
    unknowns: tuple[WatchlistUnknown, ...] = ()


@dataclass(frozen=True)
class WatchlistItem:
    """Company or idea being followed by Atlas."""

    id: str
    ticker: str
    name: str = ""
    status: WatchlistStatus = WatchlistStatus.OBSERVING
    company: Company | None = None
    research_project: ResearchProject | None = None
    knowledge_facts: tuple[KnowledgeFact, ...] = ()
    company_analysis: CompanyAnalysisReport | None = None
    manual_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class WatchlistIntelligenceInput:
    """Input for deterministic watchlist intelligence."""

    name: str
    items: tuple[WatchlistItem, ...] = ()


@dataclass(frozen=True)
class WatchlistIntelligenceReport:
    """Structured non-advisory watchlist intelligence report."""

    name: str
    overview: str
    observations: tuple[WatchlistObservation, ...]
    companies_needing_attention: tuple[WatchlistObservation, ...]
    open_questions: tuple[WatchlistQuestion, ...]
    evidence_gaps: tuple[WatchlistUnknown, ...]
    unknowns: tuple[WatchlistUnknown, ...]
    suggested_next_research_steps: tuple[str, ...]

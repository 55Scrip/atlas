from dataclasses import dataclass
from enum import Enum

from atlas.capabilities.company_analysis import CompanyAnalysisReport
from atlas.capabilities.watchlist_intelligence import WatchlistIntelligenceReport
from atlas.domains.knowledge import KnowledgeFact
from atlas.domains.research import ResearchProject


class DiscoveryPriority(str, Enum):
    """Research attention priority, not investment attractiveness."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


@dataclass(frozen=True)
class DiscoveryEvidenceLink:
    """Traceable evidence link used by Discovery."""

    id: str
    source: str
    description: str
    reference_id: str | None = None


@dataclass(frozen=True)
class DiscoveryReason:
    """Explainable reason a candidate appeared."""

    title: str
    detail: str
    evidence_links: tuple[DiscoveryEvidenceLink, ...] = ()


@dataclass(frozen=True)
class DiscoverySignal:
    """Deterministic signal used for priority."""

    title: str
    detail: str
    score: int
    evidence_links: tuple[DiscoveryEvidenceLink, ...] = ()


@dataclass(frozen=True)
class DiscoveryUnknown:
    """Unknown or evidence gap that should guide research."""

    title: str
    detail: str
    evidence_links: tuple[DiscoveryEvidenceLink, ...] = ()


@dataclass(frozen=True)
class DiscoveryQuestion:
    """Suggested research question for a discovery candidate."""

    question: str
    source: str
    evidence_links: tuple[DiscoveryEvidenceLink, ...] = ()


@dataclass(frozen=True)
class DiscoveryContext:
    """Context linking a candidate to existing Atlas structures."""

    related_knowledge_fact_ids: tuple[str, ...] = ()
    related_research_project_ids: tuple[str, ...] = ()
    related_watchlist_status: str | None = None
    related_company_analysis_ticker: str | None = None


@dataclass(frozen=True)
class DiscoveryCandidate:
    """Company, theme, or idea that may deserve further research."""

    identifier: str
    title: str
    reasons: tuple[DiscoveryReason, ...]
    supporting_evidence_links: tuple[DiscoveryEvidenceLink, ...]
    related_knowledge_facts: tuple[KnowledgeFact, ...]
    related_research_questions: tuple[DiscoveryQuestion, ...]
    related_watchlist_status: str | None
    unknowns: tuple[DiscoveryUnknown, ...]
    suggested_next_research_questions: tuple[DiscoveryQuestion, ...]
    priority: DiscoveryPriority
    confidence: str
    context: DiscoveryContext


@dataclass(frozen=True)
class DiscoveryInput:
    """Input for deterministic discovery."""

    knowledge_facts: tuple[KnowledgeFact, ...] = ()
    research_projects: tuple[ResearchProject, ...] = ()
    company_analysis_reports: tuple[CompanyAnalysisReport, ...] = ()
    watchlist_intelligence_reports: tuple[WatchlistIntelligenceReport, ...] = ()
    themes: tuple[str, ...] = ()


@dataclass(frozen=True)
class DiscoveryReport:
    """Structured non-advisory discovery report."""

    summary: str
    candidates: tuple[DiscoveryCandidate, ...]
    evidence_links: tuple[DiscoveryEvidenceLink, ...]
    unknowns: tuple[DiscoveryUnknown, ...]

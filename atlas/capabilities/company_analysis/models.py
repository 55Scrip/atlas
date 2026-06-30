from dataclasses import dataclass

from atlas.domains.decision import Evidence
from atlas.domains.knowledge import KnowledgeFact
from atlas.domains.research import ResearchProject
from atlas.shared import Company


@dataclass(frozen=True)
class CompanyAnalysisEvidenceLink:
    """Traceable evidence link used in company analysis."""

    id: str
    source: str
    description: str
    reference_id: str | None = None


@dataclass(frozen=True)
class CompanyAnalysisObservation:
    """Calm structured company observation."""

    title: str
    detail: str
    evidence_links: tuple[CompanyAnalysisEvidenceLink, ...] = ()


@dataclass(frozen=True)
class CompanyAnalysisRisk:
    """Structured risk surfaced by company analysis."""

    title: str
    detail: str
    evidence_links: tuple[CompanyAnalysisEvidenceLink, ...] = ()


@dataclass(frozen=True)
class CompanyAnalysisUnknown:
    """Missing or unresolved information that limits understanding."""

    title: str
    detail: str
    evidence_links: tuple[CompanyAnalysisEvidenceLink, ...] = ()


@dataclass(frozen=True)
class CompanyAnalysisConfidence:
    """Categorical confidence with explanation."""

    level: str
    explanation: str
    drivers: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class CompanyAnalysisSection:
    """Structured section in a company analysis report."""

    title: str
    observations: tuple[CompanyAnalysisObservation, ...] = ()
    risks: tuple[CompanyAnalysisRisk, ...] = ()
    unknowns: tuple[CompanyAnalysisUnknown, ...] = ()
    narrative: str = ""


@dataclass(frozen=True)
class CompanyAnalysisInput:
    """Input for deterministic company analysis."""

    company: Company
    business_description: str = ""
    knowledge_facts: tuple[KnowledgeFact, ...] = ()
    research_project: ResearchProject | None = None
    decision_evidence: tuple[Evidence, ...] = ()


@dataclass(frozen=True)
class CompanyAnalysisReport:
    """Non-advisory structured company analysis report."""

    company: Company
    sections: tuple[CompanyAnalysisSection, ...]
    evidence_links: tuple[CompanyAnalysisEvidenceLink, ...]
    risks: tuple[CompanyAnalysisRisk, ...]
    unknowns: tuple[CompanyAnalysisUnknown, ...]
    confidence: CompanyAnalysisConfidence
    what_could_change_the_view: tuple[str, ...]

from dataclasses import dataclass
from enum import Enum

from atlas.shared import ResearchNote


class ResearchStatus(str, Enum):
    """Maturity of research understanding, not investment action."""

    NOT_STARTED = "not_started"
    RESEARCHING = "researching"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"
    THESIS_FORMING = "thesis_forming"
    READY_FOR_REVIEW = "ready_for_review"
    ARCHIVED = "archived"


class ResearchQuestionStatus(str, Enum):
    """Lifecycle state for a research question."""

    OPEN = "open"
    RESEARCHING = "researching"
    RESOLVED = "resolved"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class ResearchEvidenceReference:
    """Reference to evidence used in a research project."""

    id: str
    source_id: str
    description: str
    url: str = ""
    knowledge_fact_id: str | None = None


@dataclass(frozen=True)
class ResearchQuestion:
    """Question that captures what remains unknown."""

    id: str
    question: str
    related_topic: str
    status: ResearchQuestionStatus = ResearchQuestionStatus.OPEN
    evidence_reference_ids: tuple[str, ...] = ()
    notes: str = ""
    created_at: str = ""
    resolved_at: str | None = None
    resolution_notes: str = ""


@dataclass(frozen=True)
class ResearchAssumption:
    """Assumption that should remain visible while research develops."""

    id: str
    statement: str
    explanation: str
    evidence_reference_ids: tuple[str, ...] = ()
    confidence: int = 50

    def __post_init__(self) -> None:
        object.__setattr__(self, "confidence", max(0, min(100, self.confidence)))


@dataclass(frozen=True)
class ThesisFragment:
    """Incomplete piece of investment reasoning under development."""

    id: str
    claim: str
    supporting_evidence_reference_ids: tuple[str, ...] = ()
    assumption_ids: tuple[str, ...] = ()
    confidence: int = 50
    open_question_ids: tuple[str, ...] = ()
    status: ResearchStatus = ResearchStatus.THESIS_FORMING

    def __post_init__(self) -> None:
        object.__setattr__(self, "confidence", max(0, min(100, self.confidence)))


@dataclass(frozen=True)
class ResearchProject:
    """Container for ongoing investment research."""

    id: str
    title: str
    topic: str
    status: ResearchStatus = ResearchStatus.NOT_STARTED
    notes: tuple[ResearchNote, ...] = ()
    questions: tuple[ResearchQuestion, ...] = ()
    assumptions: tuple[ResearchAssumption, ...] = ()
    thesis_fragments: tuple[ThesisFragment, ...] = ()
    evidence_references: tuple[ResearchEvidenceReference, ...] = ()
    created_at: str = ""


@dataclass(frozen=True)
class ResearchSummary:
    """Deterministic summary of research maturity."""

    project_id: str
    project_title: str
    number_of_notes: int
    number_of_open_questions: int
    number_of_resolved_questions: int
    number_of_assumptions: int
    thesis_maturity: str
    missing_evidence_warnings: tuple[str, ...]
    overall_research_status: ResearchStatus


class ResearchIssueSeverity(str, Enum):
    """Severity for structured research validation issues."""

    INFO = "Info"
    WARNING = "Warning"
    ERROR = "Error"


@dataclass(frozen=True)
class ResearchValidationIssue:
    """Structured validation issue for research artifacts."""

    code: str
    message: str
    severity: ResearchIssueSeverity
    item_id: str | None = None


@dataclass(frozen=True)
class ResearchValidationResult:
    """Validation result that reports issues without crashing callers."""

    is_valid: bool
    issues: tuple[ResearchValidationIssue, ...]

"""Research domain boundary.

Owns research notes, questions, assumptions, thesis fragments, evidence
references, summaries, and validation.
"""

from atlas.shared import ResearchNote

from atlas.domains.research.models import (
    ResearchAssumption,
    ResearchEvidenceReference,
    ResearchIssueSeverity,
    ResearchProject,
    ResearchQuestion,
    ResearchQuestionStatus,
    ResearchStatus,
    ResearchSummary,
    ResearchValidationIssue,
    ResearchValidationResult,
    ThesisFragment,
)
from atlas.domains.research.summary import summarize_research
from atlas.domains.research.validation import (
    is_valid_status_transition,
    validate_research_project,
)

__all__ = [
    "ResearchAssumption",
    "ResearchEvidenceReference",
    "ResearchIssueSeverity",
    "ResearchNote",
    "ResearchProject",
    "ResearchQuestion",
    "ResearchQuestionStatus",
    "ResearchStatus",
    "ResearchSummary",
    "ResearchValidationIssue",
    "ResearchValidationResult",
    "ThesisFragment",
    "is_valid_status_transition",
    "summarize_research",
    "validate_research_project",
]

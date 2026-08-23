"""HTTP response schemas for the Knowledge Strategy API. Wire format is
camelCase via the shared Core `CamelModel` (ADR-004), matching every
other Alpha schema module. Every field is a direct read of an
already-computed assessment; nothing recomputed here.
"""
from __future__ import annotations

from atlas.alpha.knowledge_strategy.completion import ResearchCompletionAssessment
from atlas.alpha.knowledge_strategy.evaluation import KnowledgeGapAssessment
from atlas.core.infrastructure.api.serialization import CamelModel


class KnowledgeGapAssessmentView(CamelModel):
    domain: str
    relevance: str
    reasons: list[str]

    @classmethod
    def from_domain(cls, assessment: KnowledgeGapAssessment) -> "KnowledgeGapAssessmentView":
        return cls(
            domain=assessment.domain.value,
            relevance=assessment.relevance.value,
            reasons=[reason.value for reason in assessment.reasons],
        )


class ResearchStrategyView(CamelModel):
    ticker: str
    case_id: str | None
    gaps: list[KnowledgeGapAssessmentView]
    """Every current knowledge gap, ordered highest research priority
    first -- what Atlas would research next and why, without actually
    running any provider."""
    completion: str

    @classmethod
    def from_domain(
        cls,
        ticker: str,
        case_id: str | None,
        gaps: tuple[KnowledgeGapAssessment, ...],
        completion: ResearchCompletionAssessment,
    ) -> "ResearchStrategyView":
        return cls(
            ticker=ticker,
            case_id=case_id,
            gaps=[KnowledgeGapAssessmentView.from_domain(gap) for gap in gaps],
            completion=completion.outcome.value,
        )

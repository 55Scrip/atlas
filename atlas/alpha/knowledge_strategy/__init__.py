"""The Knowledge Strategy Engine -- decides *what research is worth
performing*, as a dependency-free layer beneath `knowledge_
orchestration` (which decides *how* to perform it). See `relevance.py`,
`evaluation.py`, and `completion.py` for the three phases this package
implements.
"""
from __future__ import annotations

from atlas.alpha.knowledge_strategy.completion import (
    ResearchCompletionAssessment,
    ResearchCompletionOutcome,
    assess_research_completion,
)
from atlas.alpha.knowledge_strategy.evaluation import (
    RELEVANCE_RANK,
    KnowledgeGapAssessment,
    assess_knowledge_gaps,
)
from atlas.alpha.knowledge_strategy.relevance import (
    DOMAIN_RELEVANCE,
    DecisionRelevance,
    DomainRelevance,
    ImpactReasonCode,
    relevance_of,
    reasons_for,
)

__all__ = [
    "DecisionRelevance",
    "ImpactReasonCode",
    "DomainRelevance",
    "DOMAIN_RELEVANCE",
    "relevance_of",
    "reasons_for",
    "KnowledgeGapAssessment",
    "RELEVANCE_RANK",
    "assess_knowledge_gaps",
    "ResearchCompletionOutcome",
    "ResearchCompletionAssessment",
    "assess_research_completion",
]

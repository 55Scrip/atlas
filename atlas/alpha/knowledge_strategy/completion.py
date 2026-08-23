"""Research Completion Strategy (Knowledge Strategy Engine, Phase 5).

Outcome-oriented, not exhaustive: names when additional research is no
longer worthwhile, using the exact five outcomes the sprint brief
itself names. Distinct from `knowledge_orchestration.planner
.SufficiencyAssessment` (which still gates *execution* -- whether
`AcquisitionPlan.items` is empty -- and is left completely unmodified
by this sprint): this is a richer, additional explanation surfaced
alongside that gate, not a replacement for it.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from atlas.alpha.knowledge_strategy.evaluation import KnowledgeGapAssessment
from atlas.alpha.knowledge_strategy.relevance import DecisionRelevance

__all__ = ["ResearchCompletionOutcome", "ResearchCompletionAssessment", "assess_research_completion"]

_DECISION_CRITICAL = (DecisionRelevance.CRITICAL, DecisionRelevance.HIGH)


class ResearchCompletionOutcome(str, Enum):
    DECISION_READY = "decision_ready"
    """No knowledge gap remains at all."""
    CRITICAL_RESEARCH_COMPLETED = "critical_research_completed"
    """Research just ran and closed every decision-critical
    (`CRITICAL`/`HIGH`) gap -- only lower-tier gaps remain, if any."""
    REMAINING_GAPS_NOT_DECISION_CRITICAL = "remaining_gaps_not_decision_critical"
    """No decision-critical gap existed before this call either --
    whatever remains was never worth pursuing by default."""
    AWAIT_FUTURE_EXTERNAL_INFORMATION = "await_future_external_information"
    """A decision-critical gap remains and nothing blocked acquiring it
    -- there is simply no registered provider for it in this build of
    Atlas yet; nothing more to do until that changes."""
    RESEARCH_BLOCKED_BY_UNAVAILABLE_SOURCES = "research_blocked_by_unavailable_sources"
    """A decision-critical gap remains because a provider that could
    have filled it failed (e.g. a missing API key) -- a real, named
    obstacle, not silent stalling."""


@dataclass(frozen=True)
class ResearchCompletionAssessment:
    outcome: ResearchCompletionOutcome


def assess_research_completion(
    remaining_gaps: tuple[KnowledgeGapAssessment, ...],
    *,
    research_was_performed: bool,
    any_decision_critical_step_blocked: bool,
) -> ResearchCompletionAssessment:
    decision_critical_remaining = [g for g in remaining_gaps if g.relevance in _DECISION_CRITICAL]

    if not decision_critical_remaining:
        if not remaining_gaps:
            return ResearchCompletionAssessment(ResearchCompletionOutcome.DECISION_READY)
        if research_was_performed:
            return ResearchCompletionAssessment(ResearchCompletionOutcome.CRITICAL_RESEARCH_COMPLETED)
        return ResearchCompletionAssessment(ResearchCompletionOutcome.REMAINING_GAPS_NOT_DECISION_CRITICAL)

    if any_decision_critical_step_blocked:
        return ResearchCompletionAssessment(ResearchCompletionOutcome.RESEARCH_BLOCKED_BY_UNAVAILABLE_SOURCES)

    return ResearchCompletionAssessment(ResearchCompletionOutcome.AWAIT_FUTURE_EXTERNAL_INFORMATION)

"""ProvisionalReflectionResponse — provisional application state (ATLAS-009).

Held only in a local variable inside conversation/cli.py's own loop —
never a field on ConversationSession. Represents ATLAS-009-D §7's
"provisional application state": real in that the investor made a
genuine choice, but not yet a lasting domain fact, because there is not
yet a decision_id to anchor it to.
"""
from __future__ import annotations

from dataclasses import dataclass

from atlas.core.application.decision_coach.coaching_question import CoachingQuestion
from atlas.core.application.decision_reflection.reasoning_context import ReasoningContext
from atlas.core.application.decision_reflection.reflection import DecisionReflection
from atlas.core.domain.reflection_response.value_objects import (
    PatternMembershipSnapshot,
    ProvenanceSnapshot,
)


@dataclass(frozen=True)
class ProvisionalReflectionResponse:
    response_text: str  # raw, exactly as read from input_fn — never stripped or altered
    provenance: ProvenanceSnapshot


def _to_pattern_membership_snapshot(pattern) -> PatternMembershipSnapshot:
    return PatternMembershipSnapshot(
        strategy_name=pattern.strategy_name,
        member_decision_ids=pattern.member_decision_ids,
    )


def build_provenance_snapshot(
    reflection: DecisionReflection,
    coaching_question: CoachingQuestion,
    context: ReasoningContext,
) -> ProvenanceSnapshot:
    """Copy plain values out of the ephemeral reflection/coaching_question
    objects at the moment of capture — never a reference to those
    objects themselves (ATLAS-009-D §4, §6).
    """
    strategy_signature_patterns: tuple[PatternMembershipSnapshot, ...] = ()
    if reflection.strategy_signature is not None:
        strategy_signature_patterns = tuple(
            _to_pattern_membership_snapshot(pattern)
            for pattern in reflection.strategy_signature.member_patterns
        )
    return ProvenanceSnapshot(
        reflection_description=reflection.description,
        coaching_question_text=coaching_question.text,
        grounding_pattern=_to_pattern_membership_snapshot(reflection.pattern),
        strategy_signature_patterns=strategy_signature_patterns,
        reasoning_context_subject=context.subject,
        reasoning_context_decision_type=context.decision_type,
        reasoning_context_confidence=context.confidence,
    )

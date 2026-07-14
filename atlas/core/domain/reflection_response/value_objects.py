"""Value objects for the ReflectionResponse aggregate (ATLAS-009).

ResponseText is the one value object in this codebase where validation
must not become transformation (ATLAS-009-D invariant 10) — see its own
docstring below.

PatternMembershipSnapshot and ProvenanceSnapshot hold only plain values
(strings, ints, tuples of DecisionId) copied out of ephemeral objects
(RecognizedPattern, RecognizedStrategySignature, DecisionReflection,
CoachingQuestion) at the moment of capture — never a reference to those
objects, and never re-derivable by looking them up again later
(ATLAS-009-D §4).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.reflection_response.exceptions import (
    MissingCoachingQuestionTextError,
    MissingReflectionDescriptionError,
    MissingResponseTextError,
)


@dataclass(frozen=True)
class ReflectionResponseId:
    """Identity of a ReflectionResponse. Generated once, at capture, and never reused."""

    value: uuid.UUID = field(default_factory=uuid.uuid4)

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class ResponseText:
    """The investor's own words, preserved exactly as given.

    Deliberately does not normalize the way Subject/InvestmentCase/Statement
    do elsewhere in this codebase. ATLAS-009-D invariant 10 requires the
    investor's own words be preserved without Atlas rewriting their
    meaning — stripping whitespace, correcting casing, or collapsing
    internal spacing would each be a small rewrite. `value.strip()` is
    used only to check for emptiness below; `value` itself is never
    reassigned.
    """

    value: str

    def __post_init__(self) -> None:
        if self.value is None or not self.value.strip():
            raise MissingResponseTextError(
                "ResponseText.value must not be empty or whitespace-only"
            )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PatternMembershipSnapshot:
    """A snapshot of one Pattern's grouping strategy and member Decisions,
    as they were at the moment a Decision Reflection was shown — not a
    reference to the RecognizedPattern object itself, which is ephemeral
    and may never be recomputed identically again.
    """

    strategy_name: str
    member_decision_ids: tuple[DecisionId, ...]


@dataclass(frozen=True)
class ProvenanceSnapshot:
    """An immutable record of exactly what the investor saw at the
    coaching occasion that prompted a Reflection Response.

    reflection_description is the exact sentence the investor actually
    read — not reconstructed from grounding_pattern/strategy_signature_patterns,
    and never regenerated later, even if a future increment changes how
    RecognizedPattern/RecognizedStrategySignature/DecisionReflection
    generate their own description text (ATLAS-009-D §4, §6).
    """

    reflection_description: str
    coaching_question_text: str
    grounding_pattern: PatternMembershipSnapshot
    strategy_signature_patterns: tuple[PatternMembershipSnapshot, ...]
    reasoning_context_subject: str | None
    reasoning_context_decision_type: str | None
    reasoning_context_confidence: int | None

    def __post_init__(self) -> None:
        if not self.reflection_description or not self.reflection_description.strip():
            raise MissingReflectionDescriptionError(
                "ProvenanceSnapshot.reflection_description must not be empty"
            )
        if not self.coaching_question_text or not self.coaching_question_text.strip():
            raise MissingCoachingQuestionTextError(
                "ProvenanceSnapshot.coaching_question_text must not be empty"
            )

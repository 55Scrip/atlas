"""Reflection Understanding data model (ATLAS-013).

Reflection Understanding's identity is purely extensional (ATLAS-013-D
Chapter 6): individuated only by its interpretive content and the
Reflection Response material it concerns — no occasion, act, or
articulation-event individuates it further. No synthetic id field is
introduced; equality and hash are defined directly over (content, the
unordered set of concerned ids), realizing extensional identity through
plain dataclass semantics rather than an id this concept does not have.

`concerns` holds the complete, unmodified ReflectionResponse objects
(not just ids) so the full material a Reflection Understanding is about
remains traceable directly from the value itself — never requiring a
later re-lookup against Reflection History, which ATLAS-013A-D's own
"never reconstructed afterward" invariant forbids.

ReflectionUnderstandingFormationQuery is responsible for owner-scoped
reachability, deduplication, and canonical (recorded_at, id.value)
sorting *before* constructing this value. This class does not perform
any of that itself, and never reorders or deduplicates its own input —
it only protects, by rejecting invalid input outright, the structural
invariants it can verify directly: at least one concerned Reflection
Response, no duplicate ReflectionResponseId, and canonical ascending
order. This is validation, not transformation, the same discipline
ResponseText already established for its own field.
"""
from __future__ import annotations

from dataclasses import dataclass

from atlas.core.application.reflection_understanding_formation.exceptions import (
    ConcernedMaterialNotCanonicallyOrderedError,
    DuplicateConcernedReflectionResponseError,
    MissingInterpretiveContentError,
    NoConcernedMaterialError,
)
from atlas.core.domain.reflection_response.entity import ReflectionResponse


@dataclass(frozen=True)
class InterpretiveContent:
    """New interpretive content formed about Reflection Response
    material, preserved exactly as given.

    Mirrors ResponseText's own discipline exactly: `value.strip()` is
    used only to check for emptiness below; `value` itself is never
    reassigned. Articulation must never sharpen, soften, or otherwise
    transform the epistemic force or qualification the underlying
    judgment actually carried (ATLAS-013A-D Chapter 9 §9).
    """

    value: str

    def __post_init__(self) -> None:
        if self.value is None or not self.value.strip():
            raise MissingInterpretiveContentError(
                "InterpretiveContent.value must not be empty or whitespace-only"
            )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, eq=False)
class ReflectionUnderstanding:
    """New, explicit, traceable interpretive content about relationships
    within Reflection Response material, together with the complete
    material it concerns.

    Identity is extensional: two instances with equal content and an
    equal set of concerned ids are the same Reflection Understanding,
    regardless of the order or duplication present in how `concerns` was
    originally supplied to the query that built them. `eq=False`
    suppresses the dataclass-generated field-by-field comparison (which
    would compare `concerns` positionally, as a tuple) in favor of the
    hand-written extensional comparison below.
    """

    content: InterpretiveContent
    concerns: tuple[ReflectionResponse, ...]

    def __post_init__(self) -> None:
        if not self.concerns:
            raise NoConcernedMaterialError(
                "ReflectionUnderstanding.concerns must not be empty — "
                "Formation constitutively requires Reflection Response material"
            )

        ids = [entry.id for entry in self.concerns]
        if len(ids) != len(set(ids)):
            raise DuplicateConcernedReflectionResponseError(
                "ReflectionUnderstanding.concerns must not contain the same "
                "ReflectionResponseId more than once"
            )

        canonical_order = tuple(
            sorted(self.concerns, key=lambda entry: (entry.recorded_at, entry.id.value))
        )
        if self.concerns != canonical_order:
            raise ConcernedMaterialNotCanonicallyOrderedError(
                "ReflectionUnderstanding.concerns must already be ordered by "
                "(recorded_at, id.value) ascending — this value never reorders "
                "its own input"
            )

    def _concerned_ids(self) -> frozenset:
        return frozenset(entry.id for entry in self.concerns)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ReflectionUnderstanding):
            return NotImplemented
        return self.content == other.content and self._concerned_ids() == other._concerned_ids()

    def __hash__(self) -> int:
        return hash((self.content, self._concerned_ids()))

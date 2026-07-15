"""Domain errors for Reflection Understanding Formation (ATLAS-013).

Two groups of errors live here:

- Errors ReflectionUnderstandingFormationQuery raises while validating a
  requested act before construction (unreachable material, a missing
  explicit request, absent content or qualification).
- Errors ReflectionUnderstanding itself raises from its own
  __post_init__, protecting the structural invariants it can verify
  directly (non-empty, deduplicated, canonically ordered concerned
  material) rather than relying exclusively on the query to have
  enforced them beforehand.
"""
from __future__ import annotations


class ReflectionUnderstandingFormationError(Exception):
    """Base class for all Reflection Understanding Formation errors."""


class NoConcernedMaterialError(ReflectionUnderstandingFormationError):
    """Raised when no Reflection Response material is named at all.

    A deliberate, disclosed difference from Reflection Exploration, where
    an empty scope is a valid outcome: ATLAS-013A-D Chapter 3 establishes
    that Formation constitutively requires Reflection Response material —
    an act concerning no material is not about anything, so it is
    rejected rather than treated as an empty-but-valid result.
    """


class DuplicateConcernedReflectionResponseError(ReflectionUnderstandingFormationError):
    """Raised by ReflectionUnderstanding's own construction when its
    concerned material contains the same ReflectionResponseId more than
    once. The query is responsible for deduplicating before construction;
    this is the value object protecting its own set-semantics invariant
    directly, rather than trusting every caller to have done so."""


class ConcernedMaterialNotCanonicallyOrderedError(ReflectionUnderstandingFormationError):
    """Raised by ReflectionUnderstanding's own construction when its
    concerned material is not already sorted by (recorded_at, id.value)
    ascending. The query is responsible for sorting before construction;
    this value object never reorders its own input — it only rejects
    input that arrives out of canonical order."""


class UnreachableReflectionResponseError(ReflectionUnderstandingFormationError):
    """Raised when a supplied id is not present in the investor's own
    Reflection History — whether because it does not exist at all, or
    because it belongs to a different investor. Deliberately not
    distinguished, mirroring Reflection Comparison and Reflection
    Exploration. Raised for the entire request; no partial result is
    ever returned."""


class FormationNotExplicitlyRequestedError(ReflectionUnderstandingFormationError):
    """Raised when explicitly_requested is not True.

    Checked independently of, and before, any content or authorship
    attribution is examined — a substance contribution must never be
    treated as proof that Formation was explicitly requested
    (ATLAS-013A-D Chapter 1)."""


class MissingInterpretiveContentError(ReflectionUnderstandingFormationError):
    """Raised by InterpretiveContent's own construction when its value is
    empty or whitespace-only. Mirrors ResponseText's own discipline:
    validation only, never transformation."""


class MissingEpistemicQualificationError(ReflectionUnderstandingFormationError):
    """Raised by EpistemicQualification's own construction when a
    qualification is supplied but is empty or whitespace-only. Does not
    apply when no qualification is supplied at all — None is a distinct,
    valid case meaning no qualification was articulated, not an invalid
    empty one."""

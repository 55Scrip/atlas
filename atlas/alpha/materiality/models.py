"""Result shapes for the Materiality Engine (Atlas Intelligence Sprint
-- Materiality & Priority Engine). See `engine.py`'s own module
docstring for the full derivation rules and the audit this package's
classification is grounded in.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from atlas.alpha.coverage import DimensionCoverage
from atlas.alpha.stance import StanceReason

__all__ = ["MaterialityLevel", "MaterialEvidence", "MaterialityAssessment"]


class MaterialityLevel(str, Enum):
    """Deliverable 2's own six-member vocabulary. A fixed classification
    of an already-real reason code, never a score -- there is no
    numeric distance between `CRITICAL` and `HIGH`, only a declared
    order (`engine.py`'s own `_LEVEL_ORDER`), the same "fixed order,
    never invented" discipline every prior Sprint's own tie-break
    already establishes."""

    CRITICAL = "critical"
    """A fundamental blocker or a severe, real red flag -- Atlas
    genuinely cannot (or should seriously hesitate to) reach a
    conclusion without addressing this first."""
    HIGH = "high"
    """A strong, real directional signal or a significant caveat --
    would change how an investor reads this case if missed."""
    MEDIUM = "medium"
    """A real, relevant signal, but one that alone would not change an
    investor's read of the case."""
    LOW = "low"
    """A real but mild signal -- worth knowing, not worth leading with."""
    BACKGROUND = "background"
    """A real, routine fact (e.g. "nothing changed") -- true, but not
    something an investor needs surfaced first."""
    UNKNOWN = "unknown"
    """Reserved: a reason code this engine's own fixed classification
    does not yet name. Never constructed today -- every real
    `StanceReasonCode` this engine can receive is classified (see
    `engine.py`'s own `_STANCE_REASON_MATERIALITY` completeness check);
    named so a future new reason code does not silently fall through
    unclassified."""


@dataclass(frozen=True)
class MaterialEvidence:
    """One real `StanceReason`, already produced by Stance/Explainability,
    paired with its own fixed materiality classification -- never a new
    fact, never a recomputed conclusion."""

    reason: StanceReason
    materiality: MaterialityLevel


@dataclass(frozen=True)
class MaterialityAssessment:
    """Deliverable 3's own four outputs, plus each bucket's full,
    materiality-ordered membership (most material first) -- the
    "important evidence first, background collapsed" data a caller
    needs for Deliverable 5's own presentation rule, computed once,
    here, never re-sorted by a caller."""

    supporting_evidence: tuple[MaterialEvidence, ...]
    contradicting_evidence: tuple[MaterialEvidence, ...]
    limiting_factors: tuple[MaterialEvidence, ...]
    top_supporting_evidence: MaterialEvidence | None
    top_contradicting_evidence: MaterialEvidence | None
    top_limiting_factor: MaterialEvidence | None
    top_missing_evidence: DimensionCoverage | None
    """Reused verbatim from `Explanation.most_valuable_missing_information`
    (Atlas Intelligence Sprint 3) -- that field already is a fixed-
    priority "top missing evidence" pick; this engine does not
    recompute a second one."""

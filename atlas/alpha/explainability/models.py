"""Result shapes for the Explainability Engine (Atlas Intelligence
Sprint 3 -- Decision Explainability & Evidence Trace). See this
package's `engine.py` module docstring for the full derivation rules.
"""
from __future__ import annotations

from dataclasses import dataclass

from atlas.alpha.coverage import ConfidenceReason, DimensionCoverage
from atlas.alpha.stance import StanceReason

__all__ = ["Explanation", "ComparisonEvidence"]


@dataclass(frozen=True)
class Explanation:
    """The one unified "why / why not / what's missing / what would
    help most" shape this Sprint asks every major conclusion to expose.
    Every field is a real, already-computed fact reclassified from
    `Stance`/`CoverageAssessment` (Sprints 1/2) -- this dataclass adds
    no new computation of its own beyond that reclassification and the
    one genuinely new derived fact, `most_valuable_missing_information`.
    """

    supporting_evidence: tuple[StanceReason, ...]
    """Reused verbatim from `Stance.supporting_signals` -- real signals
    that point favorably."""
    contradicting_evidence: tuple[StanceReason, ...]
    """A `Stance.reasoning` subset -- real, *directional* negative
    signals (a weak Portfolio Fit, high risk, a weakened thesis).
    Deliberately excludes the *gating* reasons below: a directional
    negative is evidence Atlas found and weighed; a gate is why Atlas
    could not weigh anything more decisively at all -- two different
    facts an investor asks two different questions about."""
    limiting_factors: tuple[StanceReason, ...]
    """A `Stance.reasoning` subset -- the *gating* reasons (insufficient
    conviction, contradicting evidence present, confidence too low) that
    kept this conclusion from being more decisive. Answers "why not a
    stronger conclusion," never "what evidence argues against it" (that
    is `contradicting_evidence` above)."""
    missing_evidence: tuple[DimensionCoverage, ...]
    """The real `DimensionCoverage` entries (Sprint 1) behind `Stance
    .missing_information`'s own dimension keys -- richer than that flat
    list, since each one already carries its own real gap-kind
    reasoning (Sprint 1's `assess_coverage`), never re-derived here."""
    confidence_drivers: tuple[ConfidenceReason, ...]
    """Reused verbatim from `CoverageAssessment.reasoning` (Sprint 1)."""
    most_valuable_missing_information: DimensionCoverage | None
    """Deliverable 9 -- the single `missing_evidence` entry a real,
    fixed, documented dependency order (see `engine.py`'s own
    `_MISSING_INFORMATION_PRIORITY`) ranks highest. `None` only when
    `missing_evidence` is empty. Never a numeric score: a fixed
    priority list over a closed dimension vocabulary, the same
    "declared order, never invented" discipline `atlas.analysis_engine
    .risk.projection.risk_projection`'s own tie-break order already
    establishes."""


@dataclass(frozen=True)
class ComparisonEvidence:
    """Deliverable 7 (Compare Integration) -- per-dimension classification
    of two already-computed `Explanation`s against each other. Computes
    nothing about either company; only cross-references which real
    reason codes each one's own `supporting_evidence`/
    `contradicting_evidence` already names."""

    favoring_a: tuple[StanceReason, ...]
    """Reason codes present in A's `supporting_evidence` and absent from
    B's (or present in B's `contradicting_evidence`) -- a real point in
    A's favor B does not share."""
    favoring_b: tuple[StanceReason, ...]
    shared: tuple[StanceReason, ...]
    """Reason codes both companies' `supporting_evidence` (or both
    `contradicting_evidence`) name in common -- real facts true of both,
    neither a differentiator."""
    missing_for_both: tuple[str, ...]
    """Dimension keys present in both companies' `missing_evidence` --
    real gaps neither company's analysis can speak to yet."""

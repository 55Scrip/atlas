"""Explainability Engine (Atlas Intelligence Sprint 3 -- Decision
Explainability & Evidence Trace).

This module computes **nothing** new about any company. It reads an
already-computed `Stance` (Sprint 2) and `CoverageAssessment` (Sprint
1) and reclassifies their existing fields into the five named buckets
Deliverable 2 asks for -- Supporting Evidence, Contradicting Evidence,
Missing Evidence, Limiting Factors, Confidence Drivers -- via fixed set
membership over `StanceReasonCode`, never a new judgment about any
individual case.

**Why Contradicting Evidence and Limiting Factors are two different
buckets, not one.** `Stance.limiting_signals` (Sprint 2) already mixes
two genuinely different facts: a real, directional negative signal
Atlas found and weighed (a weak Portfolio Fit, a high-severity risk, a
weakened thesis) versus a *gate* that kept Atlas from being more
decisive at all (insufficient conviction, contradicting evidence,
confidence too low). An investor asking "why not a stronger
conclusion" wants the gate; an investor asking "what argues against
this" wants the directional negative. Collapsing them into one list
answers neither question precisely -- see `_GATE_CODES`/
`_NEGATIVE_CODES` below for the fixed classification.

**Why `most_valuable_missing_information` is a fixed priority list, not
a score.** Every other "which one first" decision in this codebase
already uses a declared, fixed order rather than an invented weight --
`atlas.analysis_engine.risk.projection.risk_projection`'s own
`_TIE_BREAK_ORDER` is the direct precedent. `_MISSING_INFORMATION_PRIORITY`
below is that same discipline, grounded in the real, already-audited
data-flow this codebase's own evaluators establish (Growth feeds
Business Risk and Long-Term Outlook; Capital Allocation feeds Financial
Risk; FCF Yield Relative feeds Valuation Risk, both Outlook horizons,
and Valuation Support -- the single highest-leverage dimension) --
never a numeric importance model.
"""
from __future__ import annotations

from atlas.alpha.coverage import CoverageAssessment, DimensionCoverage
from atlas.alpha.stance import Stance, StanceReasonCode

from .models import ComparisonEvidence, Explanation

__all__ = ["explain", "compare_evidence"]

#: Reasons that name a *gate* -- why Atlas could not be more decisive at
#: all, independent of any single directional signal.
_GATE_CODES: frozenset[StanceReasonCode] = frozenset(
    {
        StanceReasonCode.NO_COMPANY_DATA,
        StanceReasonCode.CONTRADICTING_EVIDENCE_PRESENT,
        StanceReasonCode.CONVICTION_INSUFFICIENT,
        StanceReasonCode.CONFIDENCE_VERY_LIMITED,
        StanceReasonCode.CONFIDENCE_LIMITED,
        StanceReasonCode.CONFIDENCE_MODERATE,
    }
)

#: Reasons that name a real, directional negative signal Atlas actually
#: weighed (as opposed to a gate that stopped it from weighing more).
_NEGATIVE_CODES: frozenset[StanceReasonCode] = frozenset(
    {
        StanceReasonCode.THESIS_WEAKENED,
        StanceReasonCode.DECISION_SUPPORT_UNFAVORABLE,
        StanceReasonCode.PORTFOLIO_FIT_WEAK,
        StanceReasonCode.HIGH_RISK_PRESENT,
    }
)

#: Highest-leverage dimension first -- resolving it also resolves the
#: most other, derived dimensions (see module docstring). Dimensions
#: not listed here (the structurally-locked ones, per Sprint 1's own
#: audit) never appear in `missing_evidence` in practice, but are
#: ordered last for total-ness rather than raising on an unlisted key.
_MISSING_INFORMATION_PRIORITY: tuple[str, ...] = (
    "fcf_yield_relative",
    "growth",
    "capital_allocation",
    "thesis_risk",
    "business_risk",
    "financial_risk",
    "valuation_risk",
)


def _priority_rank(dimension: DimensionCoverage) -> int:
    try:
        return _MISSING_INFORMATION_PRIORITY.index(dimension.dimension)
    except ValueError:
        return len(_MISSING_INFORMATION_PRIORITY)


def explain(stance: Stance, coverage: CoverageAssessment) -> Explanation:
    """Deterministic: identical inputs always produce an identical
    `Explanation`. Reads `stance.reasoning`/`.supporting_signals`/
    `.limiting_signals`/`.missing_information`, and `coverage
    .dimensions`/`.reasoning` -- nothing else, and never mutates or
    re-evaluates either.
    """
    contradicting = tuple(r for r in stance.limiting_signals if r.code in _NEGATIVE_CODES)
    limiting = tuple(r for r in stance.reasoning if r.code in _GATE_CODES)
    missing = tuple(d for d in coverage.dimensions if d.dimension in stance.missing_information)
    most_valuable = min(missing, key=_priority_rank) if missing else None

    return Explanation(
        supporting_evidence=stance.supporting_signals,
        contradicting_evidence=contradicting,
        limiting_factors=limiting,
        missing_evidence=missing,
        confidence_drivers=coverage.reasoning,
        most_valuable_missing_information=most_valuable,
    )


def compare_evidence(explanation_a: Explanation, explanation_b: Explanation) -> ComparisonEvidence:
    """Deliverable 7 -- reads the two already-computed `Explanation`s
    verbatim, never recomputes either. A reason code counts as
    "favoring" one side when it names a real positive for that side (in
    `supporting_evidence`) that the other side either lacks or names as
    a real negative (in `contradicting_evidence`) -- never merely
    "present for A, absent for B" alone, which would count an
    irrelevant code difference as a preference."""
    codes_a_supporting = {r.code for r in explanation_a.supporting_evidence}
    codes_b_supporting = {r.code for r in explanation_b.supporting_evidence}
    codes_a_contradicting = {r.code for r in explanation_a.contradicting_evidence}
    codes_b_contradicting = {r.code for r in explanation_b.contradicting_evidence}

    favoring_a = tuple(
        r for r in explanation_a.supporting_evidence if r.code not in codes_b_supporting or r.code in codes_b_contradicting
    )
    favoring_b = tuple(
        r for r in explanation_b.supporting_evidence if r.code not in codes_a_supporting or r.code in codes_a_contradicting
    )
    shared = tuple(r for r in explanation_a.supporting_evidence if r.code in codes_b_supporting) + tuple(
        r for r in explanation_a.contradicting_evidence if r.code in codes_b_contradicting
    )
    missing_dimensions_a = {d.dimension for d in explanation_a.missing_evidence}
    missing_dimensions_b = {d.dimension for d in explanation_b.missing_evidence}
    missing_for_both = tuple(sorted(missing_dimensions_a & missing_dimensions_b))

    return ComparisonEvidence(
        favoring_a=favoring_a,
        favoring_b=favoring_b,
        shared=shared,
        missing_for_both=missing_for_both,
    )

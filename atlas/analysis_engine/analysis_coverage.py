"""Analysis Coverage (Internal Alpha Fix Sprint 1, Part 2 -- confirmed
root cause IA-003) -- a small, deliberately separate concept from
Conviction (`conviction.py`).

Analysis Coverage answers "how much does Atlas actually know about this
company" -- purely a function of company data and the analysis Atlas has
been able to compute from it. **It never reads investor evidence at
all** -- no `EvidenceCoverageLevel`, no Observations, no Decision. That
is Conviction's own, deliberately separate question ("how strongly does
the available analysis support an investment conclusion," which
Conviction's own module docstring explains requires both real company
analysis *and* real investor evidence coverage by design).

The Internal Alpha finding this module fixes: `PortfolioHoldingAnalysis
.conviction` reads `"insufficient_evidence"` for every holding that has
no investor-recorded Observations, even when the same holding has
`confidence: full` Growth/Capital Allocation/Financial Risk/Valuation
findings built from twenty years of real filings. That is not a bug in
Conviction -- Conviction is answering exactly the question it was built
to answer. It is a *missing* signal: nothing anywhere previously
answered "does Atlas actually know this company," independent of
whether the investor has logged Observations about it yet. This module
is that missing signal, not a replacement for Conviction and not a
second Conviction. `atlas.alpha.portfolio_cockpit` now surfaces both,
side by side, so "Atlas has analyzed this company deeply" and "the
investor has formed a documented conviction" are never conflated into
one column that can only ever say one of them.

Categorical, three levels, **never numeric, never a percentage, never
averaged**. Reuses signals `atlas.analysis_engine.pipeline.assemble
_analysis` already computes for Conviction's own inputs
(`business_conclusive`, `valuation_conclusive`) plus one new,
already-existing predicate this codebase already built for exactly this
kind of question -- `atlas.analysis_engine.business_data.completeness
.assess_data_completeness` (Company Data Foundation v1). No new
computation is introduced beyond combining these three already-real
signals into one small, ordered decision table -- the same style
`conviction.calculate_conviction` and
`atlas.domains.portfolio.calculations.concentration_level` already
established for "deterministic classification, never an invented
score."
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = [
    "AnalysisCoverageLevel",
    "AnalysisCoverageReasonCode",
    "AnalysisCoverageAssessment",
    "calculate_analysis_coverage",
]


class AnalysisCoverageLevel(str, Enum):
    #: No persisted company data at all -- `assess_data_completeness
    #: .is_minimally_complete` is `False`. "Atlas still knows very
    #: little" -- the honest, literal truth: nothing.
    NO_COVERAGE = "no_coverage"
    #: Real company data exists, but Growth/Capital Allocation
    #: (`business_conclusive`) and/or the one real Valuation method
    #: (`valuation_conclusive`) have not both reached a genuine
    #: categorical conclusion yet -- e.g. a company with an identity
    #: profile and one fundamentals period, not yet enough for a Growth
    #: trend.
    PARTIAL_COVERAGE = "partial_coverage"
    #: Real company data exists *and* both Business Analysis and
    #: Valuation reached genuine conclusions from it. "Atlas has
    #: analyzed this company deeply."
    SUBSTANTIAL_COVERAGE = "substantial_coverage"


class AnalysisCoverageReasonCode(str, Enum):
    """Every reason that contributed to an Analysis Coverage
    assessment -- `AnalysisCoverageAssessment.reasons` always names
    every applicable code, the same "complete answer, not just the
    first branch that matched" discipline `ConvictionReasonCode`
    already established."""

    NO_COMPANY_DATA = "no_company_data"
    HAS_COMPANY_DATA = "has_company_data"
    BUSINESS_ANALYSIS_CONCLUSIVE = "business_analysis_conclusive"
    BUSINESS_ANALYSIS_NOT_YET_CONCLUSIVE = "business_analysis_not_yet_conclusive"
    VALUATION_CONCLUSIVE = "valuation_conclusive"
    VALUATION_NOT_YET_CONCLUSIVE = "valuation_not_yet_conclusive"


@dataclass(frozen=True)
class AnalysisCoverageAssessment:
    level: AnalysisCoverageLevel
    reasons: tuple[AnalysisCoverageReasonCode, ...]


def calculate_analysis_coverage(
    *,
    has_company_data: bool,
    business_conclusive: bool,
    valuation_conclusive: bool,
) -> AnalysisCoverageAssessment:
    """Deterministic: identical inputs always produce an identical
    `AnalysisCoverageAssessment`. No wall-clock read, no randomness, no
    partial credit.

    `has_company_data` is expected to be `assess_data_completeness
    (business_records).is_minimally_complete` -- callers should not
    invent their own definition of "has data." `business_conclusive`/
    `valuation_conclusive` are expected to be the exact same values
    already computed for `conviction.calculate_conviction`'s own
    call -- this function reads them, never recomputes them.
    """
    if not has_company_data:
        return AnalysisCoverageAssessment(
            level=AnalysisCoverageLevel.NO_COVERAGE,
            reasons=(AnalysisCoverageReasonCode.NO_COMPANY_DATA,),
        )

    business_reason = (
        AnalysisCoverageReasonCode.BUSINESS_ANALYSIS_CONCLUSIVE
        if business_conclusive
        else AnalysisCoverageReasonCode.BUSINESS_ANALYSIS_NOT_YET_CONCLUSIVE
    )
    valuation_reason = (
        AnalysisCoverageReasonCode.VALUATION_CONCLUSIVE
        if valuation_conclusive
        else AnalysisCoverageReasonCode.VALUATION_NOT_YET_CONCLUSIVE
    )
    reasons = (AnalysisCoverageReasonCode.HAS_COMPANY_DATA, business_reason, valuation_reason)

    level = (
        AnalysisCoverageLevel.SUBSTANTIAL_COVERAGE
        if business_conclusive and valuation_conclusive
        else AnalysisCoverageLevel.PARTIAL_COVERAGE
    )
    return AnalysisCoverageAssessment(level=level, reasons=reasons)

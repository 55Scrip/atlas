"""Result shapes for the Portfolio Fit Engine. See this package's own
`__init__.py` for the full design rationale.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.alpha.coverage import CoverageAssessment

__all__ = [
    "FitRating",
    "FitVerdictReasonCode",
    "FitDimensionKind",
    "FitTrend",
    "FitDimension",
    "PortfolioFitAssessment",
    "FitComparison",
]


class FitRating(str, Enum):
    """The one qualitative vocabulary used everywhere in this engine --
    for every dimension and for the overall verdict alike. Deliberately
    not a number: no field anywhere in this package holds a score,
    a percentage, or a confidence value. `UNAVAILABLE` is not a sixth
    "fit" tier -- it means the underlying signal has not been evaluated
    (`EvaluationState.NOT_EVALUATED`/`INSUFFICIENT_INPUT`), and is
    always paired with a disclosed reason, never silently omitted."""

    EXCELLENT = "excellent"
    GOOD = "good"
    NEUTRAL = "neutral"
    WEAK = "weak"
    POOR = "poor"
    UNAVAILABLE = "unavailable"


class FitVerdictReasonCode(str, Enum):
    """Implementation Sprint B1.2 (Engine Reason Localization Contract)
    -- names *why* `engine.py::_overall_fit` reached its verdict, a
    closed, 8-member set matching that function's own 8 return
    branches exactly (verified against the real source, not assumed).
    Exists because `FitRating` alone cannot distinguish two verdicts
    that reach the same rating for different reasons -- `RISK_GATE`
    and `MULTIPLE_POOR` both produce `FitRating.POOR`, but name a
    different fact. `overall_reasoning` (the pre-rendered English
    sentence) is unchanged by this addition -- this is a new, additive
    field alongside it, not a replacement."""

    NO_DIMENSION_EVALUATED = "no_dimension_evaluated"
    NO_COMPANY_LEVEL_ANALYSIS = "no_company_level_analysis"
    RISK_GATE = "risk_gate"
    MULTIPLE_POOR = "multiple_poor"
    MORE_WEAK_POOR_THAN_GOOD_EXCELLENT = "more_weak_poor_than_good_excellent"
    MOSTLY_EXCELLENT = "mostly_excellent"
    MORE_GOOD_EXCELLENT_THAN_WEAK_POOR = "more_good_excellent_than_weak_poor"
    MIXED = "mixed"


class FitDimensionKind(str, Enum):
    """The closed set of dimensions this engine evaluates. Diversification
    Fit and Position Size Impact (both named as examples in the sprint
    brief) are deliberately not separate members here -- see `engine.py`'s
    module docstring for why they were folded into `ALLOCATION` rather
    than invented as parallel computations over the same inputs."""

    BUSINESS = "business"
    VALUATION = "valuation"
    RISK = "risk"
    ALLOCATION = "allocation"
    EXPECTED_CONTRIBUTION = "expected_contribution"
    CASH_IMPACT = "cash_impact"


class FitTrend(str, Enum):
    """Whether this Case's fit has moved, sourced directly from the
    existing `ChangeIntelligence.thesis_impact` -- this engine stores no
    history of its own to compute a trend from (Deliverable 9: no
    persistence), so trend is only ever as available as Change
    Intelligence's own snapshot comparison already is."""

    IMPROVING = "improving"
    DECLINING = "declining"
    MIXED = "mixed"
    UNCHANGED = "unchanged"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class FitDimension:
    kind: FitDimensionKind
    rating: FitRating
    reasoning: tuple[str, ...]
    """Short, factual sentences citing the underlying signal this rating
    came from (e.g. "3 of 6 business categories rated Strong") -- never
    free-form generated prose, matching this codebase's template-free-but-
    structured-source convention (`OpenQuestionKind`'s own docstring)."""
    unavailable_reason: str | None = None
    """Set only when `rating is FitRating.UNAVAILABLE` -- what upstream
    signal was missing, never a silent gap."""


@dataclass(frozen=True)
class PortfolioFitAssessment:
    case_id: str
    ticker: str
    is_existing_holding: bool
    current_weight_percent: float | None
    """The holding's real weight if `is_existing_holding`, else `None`
    -- never a projected/assumed weight (Deliverable 1: no trade-size
    input exists to project one)."""
    overall: FitRating
    overall_reasoning: tuple[str, ...]
    overall_reasoning_code: FitVerdictReasonCode | None
    """Implementation Sprint B1.2 -- the semantic counterpart to
    `overall_reasoning` above (unchanged, still the pre-rendered
    English sentence for any consumer that has not adopted this field
    yet). `None` only when `overall_reasoning` is itself empty, which
    `_overall_fit` never produces -- see `engine.py`'s own return
    contract; typed optional rather than asserted non-null so this
    dataclass makes no assumption about a future branch it cannot see."""
    overall_reasoning_count: int | None
    """The one real count two of `overall_reasoning_code`'s 8 branches
    carry (`MULTIPLE_POOR`'s Poor count, `MOSTLY_EXCELLENT`'s
    Excellent-of-evaluated count) -- `None` for every other branch,
    never a fabricated number."""
    dimensions: tuple[FitDimension, ...]
    trend: FitTrend
    data_gaps: tuple[str, ...]
    """Every input this assessment could not use, named explicitly --
    the disclosure this whole engine is built around ("Om något saknas
    ska det tydligt redovisas istället för att uppfinna nya modeller")."""
    coverage: CoverageAssessment
    """Atlas Intelligence Sprint 1 (Data Coverage & Confidence Engine):
    the same per-dimension coverage and qualitative confidence every
    other surface exposes for this Case, reused verbatim here so
    Discovery's candidate cards and Portfolio's own Fit sections can
    show it without a second fetch. Never read by, or fed into, any
    `FitRating` above -- presentation only, per this Sprint's own
    "never ranking, never recommendation" instruction."""
    generated_at: datetime


@dataclass(frozen=True)
class FitComparison:
    """Deliverable 4 -- a pure comparison of two already-computed
    assessments. Computes nothing about either company; it only reads
    the two `overall` ratings (and, for the explanation, which
    dimensions differ) that `engine.assess_portfolio_fit` already
    produced independently for each."""

    assessment_a: PortfolioFitAssessment
    assessment_b: PortfolioFitAssessment
    preferred_ticker: str | None
    """`None` only when both assessments tie on `overall` -- never a
    forced tiebreak dressed up as a preference."""
    reasoning: tuple[str, ...]

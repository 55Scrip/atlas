"""Result shapes for the Coverage & Confidence Engine (Atlas Intelligence
Sprint 1). See this package's `engine.py` module docstring for the full
derivation rules and why nothing here recomputes any analysis.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from atlas.analysis_engine.analysis_coverage import AnalysisCoverageLevel

__all__ = [
    "DimensionCoverageLevel",
    "ConfidenceLevel",
    "ConfidenceReasonCode",
    "ConfidenceReason",
    "DimensionCoverage",
    "CoverageAssessment",
]


class DimensionCoverageLevel(str, Enum):
    """Per-dimension coverage, Deliverable 2's own five-member
    vocabulary. Deliberately not a number, not a percentage -- the same
    "categorical, never averaged" doctrine `AnalysisCoverageLevel`
    already established one layer up.

    `AVAILABLE` / `PARTIALLY_AVAILABLE` / `UNAVAILABLE` all mean "this
    dimension has a real evaluator and could, in principle, become more
    complete with more data." `NOT_APPLICABLE` means something
    structurally different: no evaluator exists yet for this dimension
    in this build of Atlas (e.g. Business Model, Competitive Position --
    permanently `insufficient_input` today because no external data
    source is wired in, per `atlas.analysis_engine.business`'s own
    module docstring). Conflating the two would tell an investor "Atlas
    is missing data about your company" when the true fact is "Atlas
    does not yet build this kind of analysis for any company" -- exactly
    the kind of false-precision this Sprint exists to remove.

    `INSUFFICIENT_EVIDENCE` is reserved for the one dimension today whose
    gap is about the *investor's own* recorded evidence rather than
    company/market data -- Thesis Risk. See `engine.py::_classify_risk`.
    """

    AVAILABLE = "available"
    PARTIALLY_AVAILABLE = "partially_available"
    UNAVAILABLE = "unavailable"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    NOT_APPLICABLE = "not_applicable"


class ConfidenceLevel(str, Enum):
    """Deliverable 3's qualitative confidence ladder -- how much an
    investor should trust Atlas's *own* understanding of a case, derived
    purely from how complete that understanding currently is (dimension
    coverage counts, contradiction presence, thesis staleness). Never a
    percentage, never an average, never fed by investor evidence
    coverage or Conviction -- see `engine.py`'s own module docstring for
    why this is a deliberately separate concept from both."""

    HIGH = "high"
    MODERATE = "moderate"
    LIMITED = "limited"
    VERY_LIMITED = "very_limited"


class ConfidenceReasonCode(str, Enum):
    """Every fact that contributed to `overall_confidence` -- closed
    vocabulary, matching `atlas.analysis_engine.conviction
    .ConvictionReasonCode`'s own established pattern exactly: real
    English/Swedish sentence-writing belongs at the presentation layer,
    never generated here. `count`/`total` on `ConfidenceReason` (below)
    carry whatever real number a given code names -- this engine
    counts, it never writes prose from that count."""

    NO_COMPANY_DATA = "no_company_data"
    DIMENSIONS_CONCLUSIVE = "dimensions_conclusive"
    """Paired with `count` (dimensions that reached `AVAILABLE` or
    `PARTIALLY_AVAILABLE`) and `total` (every live, non-`NOT_APPLICABLE`
    dimension)."""
    DIMENSIONS_UNAVAILABLE = "dimensions_unavailable"
    """Paired with `count`: how many live dimensions are `UNAVAILABLE`
    or `INSUFFICIENT_EVIDENCE`."""
    DIMENSIONS_PARTIAL = "dimensions_partial"
    """Paired with `count`: how many live dimensions are
    `PARTIALLY_AVAILABLE`."""
    CONTRADICTING_EVIDENCE_PRESENT = "contradicting_evidence_present"
    THESIS_STALE = "thesis_stale"


@dataclass(frozen=True)
class ConfidenceReason:
    code: ConfidenceReasonCode
    count: int | None = None
    total: int | None = None


@dataclass(frozen=True)
class DimensionCoverage:
    dimension: str
    """A stable key from the real taxonomy the dimension was evaluated
    under -- a `BusinessCategory`/`ValuationMethodKind`/`RiskCategory`
    value, e.g. `"growth"`, `"fcf_yield_relative"`, `"financial_risk"`.
    Never a free-form label; the presentation layer owns translation."""
    level: DimensionCoverageLevel
    reasoning: tuple[str, ...]
    """Every applicable gap-kind value (already-real
    `BusinessDataGapKind`/`ValuationDataGapKind`/`RiskDataGapKind`
    members, as plain strings) that produced this level -- never
    free-form prose, matching `FitDimension.reasoning`'s own
    structured-not-generated convention. Empty exactly when `level` is
    `AVAILABLE` with no gap at all."""


@dataclass(frozen=True)
class CoverageAssessment:
    dimensions: tuple[DimensionCoverage, ...]
    overall_coverage: AnalysisCoverageLevel
    """Reused verbatim from `CanonicalAnalysis.analysis_coverage.level`
    -- this engine never recomputes a second whole-case coverage
    rollup. See `engine.py`'s own module docstring."""
    overall_confidence: ConfidenceLevel
    missing_dimensions: tuple[str, ...]
    """Dimension keys whose level is `UNAVAILABLE` or
    `INSUFFICIENT_EVIDENCE` -- real gaps that more data or more investor
    evidence could genuinely close."""
    not_applicable_dimensions: tuple[str, ...]
    """Dimension keys whose level is `NOT_APPLICABLE` -- capabilities
    this build of Atlas does not evaluate for any company yet, not a
    per-company data gap."""
    reasoning: tuple[ConfidenceReason, ...]
    """Every real, counted fact behind `overall_confidence` -- closed
    reason codes plus their real counts, never a pre-written sentence
    (this codebase's own `ConvictionReasonCode` precedent: the
    presentation layer owns the sentence, in whichever language the
    investor reads)."""

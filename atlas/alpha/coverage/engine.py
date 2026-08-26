"""Coverage & Confidence Engine (Atlas Intelligence Sprint 1 --
Deliverables 2/3/4).

Answers two questions Atlas has never explicitly answered before, for
any single case:

    1. Coverage -- for each real analysis dimension, does Atlas
       currently have enough to say something (`DimensionCoverageLevel`)?
    2. Confidence -- given all of that, how much should an investor
       trust Atlas's own understanding of this case right now
       (`ConfidenceLevel`)?

This module computes **nothing** that is not already sitting on a
`CanonicalAnalysis` it is handed. It reads `.status`/`.missing_evidence`
off already-computed `BusinessFinding`/`ValuationFinding`/`RiskFinding`
objects, reads `.analysis_coverage`/`.valuation_support` verbatim, and
classifies -- an ordered decision table over counts and booleans, the
same style `atlas.analysis_engine.conviction.calculate_conviction` and
`atlas.analysis_engine.analysis_coverage.calculate_analysis_coverage`
already established for "deterministic classification, never an
invented score." No randomness, no AI, no wall-clock read, no weights,
no percentage, no average.

**Why this is a new, Alpha-only, purely-orchestration module rather
than a Core concept**: `atlas.analysis_engine` already has three
deliberately separate whole-case concepts -- Analysis Coverage ("how
much does Atlas know about the company," company-data-only),
Confidence (`EvidenceCoverageLevel`, "has the investor backed their
Observations with real Evidence"), and Conviction ("does everything --
company analysis AND investor evidence -- support a conclusion"). This
engine adds the missing *per-dimension* tier underneath Analysis
Coverage, and reuses `AnalysisCoverageLevel` verbatim as this engine's
own "Overall Coverage" rather than inventing a second whole-case
rollup. It deliberately does **not** touch Conviction or
`EvidenceCoverageLevel` -- see `ConfidenceLevel`'s own docstring in
`models.py` for why this Sprint's "Confidence" is a fourth, distinct
concept, not a renaming of either.

**Dimension scope.** Only dimensions with a real `BusinessFinding`/
`ValuationFinding`/`RiskFinding` object are represented -- the three
locked Valuation scenario methods and the six `RiskCategory` members
that never produce a Finding at all are omitted entirely, never
synthesized as a placeholder "dimension" with no real backing (that
would itself be a kind of fabrication). Every dimension this engine
does name maps 1:1 to a real, already-computed Finding.

**Why `Finding.confidence` (`EvidenceCoverageLevel`) is never read
here.** An Internal Alpha audit (Atlas Intelligence Sprint 1,
Deliverable 1) found this field is semantically overloaded across the
pipeline -- genuinely evidence-coverage-derived for Thesis Risk, but a
mistyped *company-data*-coverage signal for Growth/Capital Allocation/
FCF Yield/Business Risk/Financial Risk/Valuation Risk, and inverted by
a real bug in `valuation/cash_flow.py`'s insufficiency branch (`NONE`
and `PARTIAL` are swapped there). Coverage classification below instead
reads only `.status` and `.missing_evidence` -- both unambiguous,
already-serialized-elsewhere fields -- so this engine inherits neither
issue.
"""
from __future__ import annotations

from atlas.analysis_engine.business_contracts import BusinessCategoryStatus, BusinessDataGapKind
from atlas.analysis_engine.models import CanonicalAnalysis
from atlas.analysis_engine.risk.contracts import RiskDataGapKind, RiskStatus
from atlas.analysis_engine.valuation.contracts import ValuationDataGapKind, ValuationStatus
from atlas.analysis_engine.valuation.support import ValuationSupportGapKind, ValuationSupportStatus

from .models import (
    ConfidenceLevel,
    ConfidenceReason,
    ConfidenceReasonCode,
    CoverageAssessment,
    DimensionCoverage,
    DimensionCoverageLevel,
)

__all__ = ["assess_coverage"]

_BUSINESS_INCONCLUSIVE = (BusinessCategoryStatus.NOT_EVALUATED, BusinessCategoryStatus.INSUFFICIENT_INPUT)
_VALUATION_INCONCLUSIVE = (ValuationStatus.NOT_EVALUATED, ValuationStatus.INSUFFICIENT_INPUT)
_RISK_INCONCLUSIVE = (RiskStatus.NOT_EVALUATED, RiskStatus.INSUFFICIENT_INPUT)


def _classify_business(
    status: BusinessCategoryStatus, missing_evidence: tuple[BusinessDataGapKind, ...]
) -> tuple[DimensionCoverageLevel, tuple[str, ...]]:
    reasons = tuple(g.value for g in missing_evidence)
    if status not in _BUSINESS_INCONCLUSIVE:
        level = DimensionCoverageLevel.PARTIALLY_AVAILABLE if missing_evidence else DimensionCoverageLevel.AVAILABLE
        return level, reasons
    if BusinessDataGapKind.NO_EXTERNAL_DATA_SOURCE_CONNECTED in missing_evidence:
        return DimensionCoverageLevel.NOT_APPLICABLE, reasons
    return DimensionCoverageLevel.UNAVAILABLE, reasons


def _classify_valuation(status: ValuationStatus, missing_evidence: tuple[ValuationDataGapKind, ...]) -> tuple[DimensionCoverageLevel, tuple[str, ...]]:
    reasons = tuple(g.value for g in missing_evidence)
    if status not in _VALUATION_INCONCLUSIVE:
        level = DimensionCoverageLevel.PARTIALLY_AVAILABLE if missing_evidence else DimensionCoverageLevel.AVAILABLE
        return level, reasons
    if ValuationDataGapKind.MISSING_SCENARIO_ASSUMPTIONS in missing_evidence:
        return DimensionCoverageLevel.NOT_APPLICABLE, reasons
    return DimensionCoverageLevel.UNAVAILABLE, reasons


def _classify_risk(status: RiskStatus, missing_evidence: tuple[RiskDataGapKind, ...]) -> tuple[DimensionCoverageLevel, tuple[str, ...]]:
    reasons = tuple(g.value for g in missing_evidence)
    if status not in _RISK_INCONCLUSIVE:
        level = DimensionCoverageLevel.PARTIALLY_AVAILABLE if missing_evidence else DimensionCoverageLevel.AVAILABLE
        return level, reasons
    if RiskDataGapKind.NO_EVIDENCE_TO_EVALUATE in missing_evidence:
        return DimensionCoverageLevel.INSUFFICIENT_EVIDENCE, reasons
    return DimensionCoverageLevel.UNAVAILABLE, reasons


def has_contradiction(analysis: CanonicalAnalysis) -> bool:
    """Real, already-established contradiction signals only -- never a
    new interpretation. Thesis Risk `HIGH` means investor evidence
    genuinely contradicts a recorded Observation
    (`atlas.analysis_engine.risk.thesis_risk`'s own docstring);
    `ValuationSupportGapKind.CONFLICTING_VALUATION_PROOFS` means two
    independent valuation proof paths disagreed
    (`atlas.analysis_engine.valuation.synthesis`). Deliberately excludes
    a Business/Financial Risk vs. Valuation Risk divergence (the
    "value trap" pattern) -- `valuation_risk.py`'s own module docstring
    names that as a *future* consumer's job, and calling two
    independently-legitimate risk signals a "contradiction" would be
    this engine inventing an interpretation Core never made."""
    thesis_risk = next((f for f in analysis.risk_analysis.findings if f.category.value == "thesis_risk"), None)
    if thesis_risk is not None and thesis_risk.status is RiskStatus.HIGH:
        return True
    support = analysis.valuation_support
    if support.status is ValuationSupportStatus.INSUFFICIENT_INPUT and support.gap is ValuationSupportGapKind.CONFLICTING_VALUATION_PROOFS:
        return True
    return False


def _derive_confidence(
    dimensions: tuple[DimensionCoverage, ...], *, is_thesis_stale: bool, has_contradiction: bool
) -> tuple[ConfidenceLevel, tuple[ConfidenceReason, ...]]:
    live = tuple(d for d in dimensions if d.level is not DimensionCoverageLevel.NOT_APPLICABLE)
    if not live:
        return ConfidenceLevel.VERY_LIMITED, (ConfidenceReason(ConfidenceReasonCode.NO_COMPANY_DATA),)

    available = tuple(d for d in live if d.level is DimensionCoverageLevel.AVAILABLE)
    partial = tuple(d for d in live if d.level is DimensionCoverageLevel.PARTIALLY_AVAILABLE)
    gaps = tuple(
        d for d in live if d.level in (DimensionCoverageLevel.UNAVAILABLE, DimensionCoverageLevel.INSUFFICIENT_EVIDENCE)
    )

    reasons: list[ConfidenceReason] = [
        ConfidenceReason(ConfidenceReasonCode.DIMENSIONS_CONCLUSIVE, count=len(available) + len(partial), total=len(live)),
    ]
    if gaps:
        reasons.append(ConfidenceReason(ConfidenceReasonCode.DIMENSIONS_UNAVAILABLE, count=len(gaps)))
    if partial:
        reasons.append(ConfidenceReason(ConfidenceReasonCode.DIMENSIONS_PARTIAL, count=len(partial)))
    if has_contradiction:
        reasons.append(ConfidenceReason(ConfidenceReasonCode.CONTRADICTING_EVIDENCE_PRESENT))
    if is_thesis_stale:
        reasons.append(ConfidenceReason(ConfidenceReasonCode.THESIS_STALE))

    if not available and not partial:
        # Trust Hardening Sprint: this is the identical real-world fact
        # the `if not live` branch above already exists to name --
        # "Atlas has no real conclusion for this company from any
        # dimension" -- just reached via `UNAVAILABLE`/
        # `INSUFFICIENT_EVIDENCE` dimensions instead of `NOT_APPLICABLE`
        # ones. `_classify_business`/`_classify_valuation`/`_classify_risk`
        # only produce `NOT_APPLICABLE` for a few specific, named gap
        # kinds (e.g. `NO_EXTERNAL_DATA_SOURCE_CONNECTED`); a company
        # with genuinely zero ingested data (BTC, INVE-B -- confirmed
        # live, this sprint) classifies as `UNAVAILABLE` instead, so
        # `not live` was never true for them and this branch's own
        # `NO_COMPANY_DATA` signal never reached `stance.engine`'s
        # "real red flag vs. no data at all" gate -- the exact,
        # traced cause of a zero-data holding rendering as a red flag
        # identical to one with a genuine, evidence-backed contradiction.
        # Naming the fact once, here, correctly, fixes every downstream
        # reader (`stance`, `decision_reliability`, `explainability`,
        # `materiality`) that already keys off this one reason code.
        reasons.append(ConfidenceReason(ConfidenceReasonCode.NO_COMPANY_DATA))
        return ConfidenceLevel.VERY_LIMITED, tuple(reasons)
    if has_contradiction:
        return ConfidenceLevel.LIMITED, tuple(reasons)
    if len(gaps) > len(available) + len(partial):
        return ConfidenceLevel.LIMITED, tuple(reasons)
    if partial or gaps or is_thesis_stale:
        return ConfidenceLevel.MODERATE, tuple(reasons)
    return ConfidenceLevel.HIGH, tuple(reasons)


def assess_coverage(analysis: CanonicalAnalysis, *, is_thesis_stale: bool) -> CoverageAssessment:
    """Deterministic: identical inputs always produce an identical
    `CoverageAssessment`. Reads `analysis.business_analysis.findings`,
    `.valuation_engine.findings`, `.risk_analysis.findings`,
    `.analysis_coverage`, and `.valuation_support` -- nothing else, and
    never mutates or re-evaluates any of them.
    """
    dimensions: list[DimensionCoverage] = []

    for f in analysis.business_analysis.findings:
        level, reasons = _classify_business(f.status, f.missing_evidence)
        dimensions.append(DimensionCoverage(dimension=f.kind.value, level=level, reasoning=reasons))

    for f in analysis.valuation_engine.findings:
        level, reasons = _classify_valuation(f.status, f.missing_evidence)
        dimensions.append(DimensionCoverage(dimension=f.kind.value, level=level, reasoning=reasons))

    for f in analysis.risk_analysis.findings:
        level, reasons = _classify_risk(f.status, f.missing_evidence)
        dimensions.append(DimensionCoverage(dimension=f.category.value, level=level, reasoning=reasons))

    dimensions_t = tuple(dimensions)
    contradiction = has_contradiction(analysis)
    confidence, confidence_reasons = _derive_confidence(
        dimensions_t, is_thesis_stale=is_thesis_stale, has_contradiction=contradiction
    )

    return CoverageAssessment(
        dimensions=dimensions_t,
        overall_coverage=analysis.analysis_coverage.level,
        overall_confidence=confidence,
        missing_dimensions=tuple(
            d.dimension
            for d in dimensions_t
            if d.level in (DimensionCoverageLevel.UNAVAILABLE, DimensionCoverageLevel.INSUFFICIENT_EVIDENCE)
        ),
        not_applicable_dimensions=tuple(d.dimension for d in dimensions_t if d.level is DimensionCoverageLevel.NOT_APPLICABLE),
        reasoning=confidence_reasons,
    )

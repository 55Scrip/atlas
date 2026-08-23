"""Evidence Quality Engine (Atlas Intelligence Sprint 4 -- Evidence
Quality & Conflict Resolution).

**Deliverable 1's audit, in one place.** Every evidence source this
engine reads was traced back to its real origin before any code was
written here:

- `BusinessFact`/`ValuationFact` (`atlas.analysis_engine.business_facts`/
  `.valuation.facts`) already carry real `published_at`/`extracted_at`
  timestamps and a real `source_record_id` -- freshness and dominance
  are directly derivable, nothing invented.
- `atlas.analysis_engine.business_data.versioning` already prevents
  exact duplicates at ingestion (`DuplicateRecord`) and already groups
  republished documents by `lineage_id` with an immutable
  `supersedes` chain -- every real caller (including this engine's own
  `service.py`) already filters to `latest_versions()` before this
  engine ever sees a record, so a genuinely superseded document version
  is a state this engine can name (`EvidenceQualityLevel.SUPERSEDED`)
  but never actually construct today -- documented, not silently
  dropped.
- **The one real, load-bearing gap this audit found**:
  `extract_facts_from_records`/`extract_valuation_facts_from_records`
  already detect when two source records report a different value for
  the same `(company, kind, period)` -- and silently drop the entire
  group, with zero signal surfaced anywhere about what was dropped or
  why (see each function's own module docstring: "Conflicting facts
  are excluded, not guessed"). This engine is the first place in the
  codebase that surfaces what that drop discards, by independently
  calling the same *public*, unmodified, per-record `extract_facts`/
  `extract_valuation_facts` functions and performing the identical
  `(kind, period)` grouping check Core already performs internally --
  never a second, different conflict rule, never a change to Core's own
  behavior (per this sprint's "do not redesign Core" instruction).
- A `BusinessFinding`/`RiskFinding`/`ValuationFinding` reaching a real
  conclusion (`status` outside its own `NOT_EVALUATED`/
  `INSUFFICIENT_INPUT` pair) while its own `supporting_evidence`/
  `supporting_facts` tuple is empty is a real, already-representable
  state this engine names (`UNSUPPORTED`) but never re-derives the
  underlying conclusion itself.
- Investor-recorded evidence (`Evidence`/`Observation`/`Decision`)
  already has its own real staleness concept
  (`InvestmentCaseCompositionService._is_thesis_stale`, reusing
  `VERY_OLD_CASE_THRESHOLD_DAYS`) and Sprint 1's own `ConfidenceReasonCode
  .THESIS_STALE` already surfaces it on every Coverage assessment --
  this engine deliberately does not re-derive a second staleness signal
  for that layer, only for the company-data layer neither Sprint 1 nor
  this engine's own investor-facing Confidence signal currently grades
  by age at all.

**Not built, and why**: "two valuation methods disagree" (Deliverable
4's own example) has no real second, independent valuation method to
disagree with yet -- `atlas.analysis_engine.valuation` ships exactly
one real method (`fcf_yield_relative`) plus three scenario projections
that share its own inputs, not an independent cross-check. Building a
second method to make this example true would be new investment
analysis, forbidden by this sprint's own "never perform new investment
analysis" instruction. Likewise, cross-engine trend conflicts ("coverage
improved while stance weakened") would require a second, independent
snapshot-comparison mechanism this codebase does not persist beyond
`ChangeIntelligence`'s own already-built comparison -- duplicating that
capability here would violate this sprint's "remove duplicated... only
remove confirmed-unused code" instruction in spirit. Both are named
explicitly in the Final Report's Open Questions, not silently skipped.

Everything below is deterministic: identical inputs always produce a
deeply equal `EvidenceQualityReport`. No wall-clock read (`evaluated_at`
is always caller-supplied), no randomness, no invented score.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from atlas.analysis_engine.business_contracts import BusinessCategoryStatus
from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.extraction import extract_facts
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.models import CanonicalAnalysis
from atlas.analysis_engine.risk.contracts import RiskStatus
from atlas.analysis_engine.valuation.contracts import ValuationStatus
from atlas.analysis_engine.valuation.facts import ValuationFact, ValuationFactKind, extract_valuation_facts
from atlas.alpha.portfolio_status.service import VERY_OLD_CASE_THRESHOLD_DAYS

from .models import (
    EvidenceConflict,
    EvidenceConflictStatus,
    EvidenceDominance,
    EvidenceFreshness,
    EvidenceQualityLevel,
    EvidenceQualityReport,
    EvidenceWarningCode,
    FactQuality,
    UnsupportedFinding,
)

__all__ = ["assess_evidence_quality"]

_BUSINESS_INCONCLUSIVE = (BusinessCategoryStatus.NOT_EVALUATED, BusinessCategoryStatus.INSUFFICIENT_INPUT)
_VALUATION_INCONCLUSIVE = (ValuationStatus.NOT_EVALUATED, ValuationStatus.INSUFFICIENT_INPUT)
_RISK_INCONCLUSIVE = (RiskStatus.NOT_EVALUATED, RiskStatus.INSUFFICIENT_INPUT)

#: Bucket boundaries derived as whole multiples of the one existing,
#: real threshold this codebase already has (90 days) -- see
#: `EvidenceFreshness`'s own docstring. Never a second, freestanding
#: set of day-counts.
_RECENT_THRESHOLD_DAYS = VERY_OLD_CASE_THRESHOLD_DAYS
_OLD_THRESHOLD_DAYS = VERY_OLD_CASE_THRESHOLD_DAYS * 2
_STALE_THRESHOLD_DAYS = VERY_OLD_CASE_THRESHOLD_DAYS * 4

#: Fixed priority order for the one overall `EvidenceQualityLevel` --
#: first match wins, the same "declared order, never invented" tie-break
#: discipline `risk_projection`'s own `_TIE_BREAK_ORDER` established.
_QUALITY_PRIORITY: tuple[EvidenceQualityLevel, ...] = (
    EvidenceQualityLevel.NOT_APPLICABLE,
    EvidenceQualityLevel.CONFLICTING,
    EvidenceQualityLevel.UNSUPPORTED,
    EvidenceQualityLevel.STALE,
    EvidenceQualityLevel.INCOMPLETE,
    EvidenceQualityLevel.OLD,
    EvidenceQualityLevel.RECENT,
    EvidenceQualityLevel.FRESH,
)

_KNOWN_FACT_KIND_COUNT = len(BusinessFactKind) + len(ValuationFactKind)


def _freshness_from_age_days(age_days: float | None) -> EvidenceFreshness:
    if age_days is None:
        return EvidenceFreshness.NOT_APPLICABLE
    if age_days < _RECENT_THRESHOLD_DAYS:
        return EvidenceFreshness.FRESH
    if age_days < _OLD_THRESHOLD_DAYS:
        return EvidenceFreshness.RECENT
    if age_days < _STALE_THRESHOLD_DAYS:
        return EvidenceFreshness.OLD
    return EvidenceFreshness.STALE


_FRESHNESS_SEVERITY: dict[EvidenceFreshness, int] = {
    EvidenceFreshness.FRESH: 0,
    EvidenceFreshness.RECENT: 1,
    EvidenceFreshness.OLD: 2,
    EvidenceFreshness.STALE: 3,
    EvidenceFreshness.NOT_APPLICABLE: -1,
}


def _worst_freshness(values: tuple[EvidenceFreshness, ...]) -> EvidenceFreshness:
    live = tuple(v for v in values if v is not EvidenceFreshness.NOT_APPLICABLE)
    if not live:
        return EvidenceFreshness.NOT_APPLICABLE
    return max(live, key=lambda v: _FRESHNESS_SEVERITY[v])


def _detect_conflicts(records: tuple[BusinessRecord, ...], *, evaluated_at: datetime) -> tuple[EvidenceConflict, ...]:
    """Independently reproduces the exact `(fact_kind, period)` grouping
    check `extract_facts_from_records`/`extract_valuation_facts_from_records`
    already perform internally to decide what to drop -- calling only
    the public, per-record, unmodified `extract_facts`/
    `extract_valuation_facts` (never the private drop logic itself, and
    never a different rule)."""
    groups: dict[tuple[str, str], dict[float, set[str]]] = defaultdict(lambda: defaultdict(set))
    units: dict[tuple[str, str], str] = {}

    for record in records:
        for fact in extract_facts(record, evaluated_at=evaluated_at):
            key = (fact.kind.value, fact.period)
            groups[key][fact.value].add(fact.source_record_id)
            units[key] = fact.unit
        for fact in extract_valuation_facts(record, evaluated_at=evaluated_at):
            key = (fact.kind.value, fact.period)
            groups[key][fact.value].add(fact.source_record_id)
            units[key] = fact.unit

    conflicts: list[EvidenceConflict] = []
    for (kind, period), values_to_records in sorted(groups.items()):
        if len(values_to_records) < 2:
            continue
        source_record_ids = tuple(sorted({rid for ids in values_to_records.values() for rid in ids}))
        conflicts.append(
            EvidenceConflict(
                fact_kind=kind,
                period=period,
                unit=units[(kind, period)],
                values=tuple(sorted(values_to_records)),
                source_record_ids=source_record_ids,
            )
        )
    return tuple(conflicts)


def _fact_quality_by_kind(
    business_facts: tuple[BusinessFact, ...], valuation_facts: tuple[ValuationFact, ...], *, evaluated_at: datetime
) -> tuple[FactQuality, ...]:
    """Freshness/dominance computed only from facts that actually
    survive Core's own conflict-drop -- the facts real analysis is
    currently using, never a conflicting group in isolation. Takes
    `InvestmentCaseComposition.business_facts`/`.market_facts` directly
    (Product Sprint 14's own already-computed, already-conflict-free
    re-derivation of `extract_facts_from_records`/
    `extract_valuation_facts_from_records`) rather than a third,
    redundant recomputation."""
    latest_by_kind: dict[str, datetime] = {}
    latest_period_by_kind: dict[str, str] = {}
    sources_by_kind: dict[str, set[str]] = defaultdict(set)

    for fact in (*business_facts, *valuation_facts):
        kind = fact.kind.value
        sources_by_kind[kind].add(fact.source_record_id)
        if kind not in latest_by_kind or fact.published_at > latest_by_kind[kind]:
            latest_by_kind[kind] = fact.published_at
            latest_period_by_kind[kind] = fact.period

    result: list[FactQuality] = []
    for kind in sorted(sources_by_kind):
        published_at = latest_by_kind[kind]
        age_days = (evaluated_at - published_at).total_seconds() / 86400
        source_ids = sources_by_kind[kind]
        result.append(
            FactQuality(
                fact_kind=kind,
                freshness=_freshness_from_age_days(age_days),
                dominance=EvidenceDominance.SINGLE_SOURCE if len(source_ids) == 1 else EvidenceDominance.CORROBORATED,
                latest_period=latest_period_by_kind[kind],
                latest_published_at=published_at,
                source_record_count=len(source_ids),
            )
        )
    return tuple(result)


def _unsupported_findings(
    business_findings: tuple, valuation_findings: tuple, risk_findings: tuple
) -> tuple[UnsupportedFinding, ...]:
    """A real conclusion (status outside the finding's own
    `NOT_EVALUATED`/`INSUFFICIENT_INPUT` pair) with zero backing
    evidence -- reads `.status`/`.supporting_evidence`/
    `.supporting_facts` verbatim, computes no new conclusion. Takes the
    three finding tuples directly (never the whole `CanonicalAnalysis`)
    so a caller -- test or otherwise -- never needs to satisfy
    `BusinessAnalysisResult`/`RiskAnalysisResult`/`ValuationEngineResult`
    's own "one finding per every category" wrapper-level validation
    just to exercise this one, narrower classification.

    **Live-verification finding (Deliverable 13).** `RiskCategory
    .THESIS_RISK` is deliberately excluded from this check --
    `atlas.analysis_engine.risk.thesis_risk.evaluate_thesis_risk`'s own
    module docstring documents that it *always* constructs
    `supporting_facts=()`, for a genuine `LOW` conclusion exactly as
    much as a `HIGH` one (its real evidentiary backing for `HIGH` lives
    in `contradicting_facts` instead; `LOW`'s "checked, found nothing"
    has structurally nothing positive to cite at all, yet is still a
    fully honest, evidenced conclusion -- the case-wide
    `EvidenceCoverageLevel` gate already had to pass for either status
    to be reached). Checking `supporting_facts` alone against this one
    evaluator's shape produced a systematic false positive on every
    real Case reaching `thesis_risk: LOW`, confirmed live against real
    ingested company data before this exclusion was added. Every other
    Risk category's own evaluator does populate `supporting_facts` for
    a real conclusion, so this exclusion is Thesis-Risk-specific, not a
    blanket loosening of the check."""
    found: list[UnsupportedFinding] = []

    for f in business_findings:
        if f.status not in _BUSINESS_INCONCLUSIVE and not f.supporting_evidence:
            found.append(UnsupportedFinding(category=f.kind.value, status=f.status.value))

    for f in valuation_findings:
        if f.status not in _VALUATION_INCONCLUSIVE and not f.supporting_facts:
            found.append(UnsupportedFinding(category=f.kind.value, status=f.status.value))

    for f in risk_findings:
        if f.category is RiskCategory.THESIS_RISK:
            continue
        if f.status not in _RISK_INCONCLUSIVE and not f.supporting_facts:
            found.append(UnsupportedFinding(category=f.category.value, status=f.status.value))

    return tuple(found)


def assess_evidence_quality(
    records: tuple[BusinessRecord, ...],
    business_facts: tuple[BusinessFact, ...],
    market_facts: tuple[ValuationFact, ...],
    analysis: CanonicalAnalysis,
    *,
    evaluated_at: datetime,
) -> EvidenceQualityReport:
    """Deterministic: identical inputs always produce a deeply equal
    `EvidenceQualityReport`. `records` must already be filtered to
    `business_data.versioning.latest_versions` by the caller -- the
    same precondition `InvestmentCaseCompositionService.build` already
    enforces, and the reason `EvidenceQualityLevel.SUPERSEDED` is a
    real, named, but never-constructed state (see this module's own
    docstring). `business_facts`/`market_facts` should be
    `InvestmentCaseComposition.business_facts`/`.market_facts` verbatim
    -- `records` is used only to detect what Core's own conflict-drop
    discarded (see `_detect_conflicts`'s own docstring), never
    re-extracted into a second, redundant fact set."""
    conflicts = _detect_conflicts(records, evaluated_at=evaluated_at)
    facts = _fact_quality_by_kind(business_facts, market_facts, evaluated_at=evaluated_at)
    unsupported = _unsupported_findings(
        analysis.business_analysis.findings, analysis.valuation_engine.findings, analysis.risk_analysis.findings
    )

    conflict_status = (
        EvidenceConflictStatus.CONFLICTING
        if conflicts
        else (EvidenceConflictStatus.CONSISTENT if facts else EvidenceConflictStatus.NOT_APPLICABLE)
    )
    overall_freshness = _worst_freshness(tuple(f.freshness for f in facts))
    single_source_kinds = tuple(f for f in facts if f.dominance is EvidenceDominance.SINGLE_SOURCE)
    overall_dominance = (
        EvidenceDominance.NOT_APPLICABLE
        if not facts
        else (EvidenceDominance.SINGLE_SOURCE if single_source_kinds else EvidenceDominance.CORROBORATED)
    )
    is_incomplete = bool(facts) and len(facts) < (_KNOWN_FACT_KIND_COUNT / 2)

    candidates: set[EvidenceQualityLevel] = set()
    if not facts and not conflicts:
        candidates.add(EvidenceQualityLevel.NOT_APPLICABLE)
    if conflicts:
        candidates.add(EvidenceQualityLevel.CONFLICTING)
    if unsupported:
        candidates.add(EvidenceQualityLevel.UNSUPPORTED)
    if overall_freshness is EvidenceFreshness.STALE:
        candidates.add(EvidenceQualityLevel.STALE)
    if is_incomplete:
        candidates.add(EvidenceQualityLevel.INCOMPLETE)
    if overall_freshness is EvidenceFreshness.OLD:
        candidates.add(EvidenceQualityLevel.OLD)
    if overall_freshness is EvidenceFreshness.RECENT:
        candidates.add(EvidenceQualityLevel.RECENT)
    if overall_freshness is EvidenceFreshness.FRESH:
        candidates.add(EvidenceQualityLevel.FRESH)
    if not candidates:
        candidates.add(EvidenceQualityLevel.NOT_APPLICABLE)

    quality = next(level for level in _QUALITY_PRIORITY if level in candidates)

    warnings: list[EvidenceWarningCode] = []
    if conflicts:
        warnings.append(EvidenceWarningCode.CONFLICTING_SOURCE_VALUES)
    if overall_freshness in (EvidenceFreshness.STALE, EvidenceFreshness.OLD):
        warnings.append(EvidenceWarningCode.EVIDENCE_STALE)
    if single_source_kinds:
        warnings.append(EvidenceWarningCode.SINGLE_SOURCE_DEPENDENCY)
    if unsupported:
        warnings.append(EvidenceWarningCode.CONCLUSION_WITHOUT_SUPPORT)
    if is_incomplete:
        warnings.append(EvidenceWarningCode.PARTIAL_COVERAGE)
    if not facts and not conflicts:
        warnings.append(EvidenceWarningCode.NO_EVIDENCE)

    return EvidenceQualityReport(
        quality=quality,
        conflict_status=conflict_status,
        freshness=overall_freshness,
        dominance=overall_dominance,
        warnings=tuple(warnings),
        facts=facts,
        conflicts=conflicts,
        unsupported_findings=unsupported,
    )

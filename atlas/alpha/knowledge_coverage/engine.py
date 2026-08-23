"""Knowledge Coverage Engine (Automatic Investment Case Builder
Foundation). Classifies every `KnowledgeDomain`'s current state from
already-composed, already-real data -- `InvestmentCaseComposition`,
the already-computed `EvidenceQualityReport` (`FactQuality` per fact
kind), and the same `latest_versions`-filtered `BusinessRecord`s
`assess_evidence_quality` itself is called with. Nothing here performs
I/O, calls a provider, or recomputes an existing engine's own
conclusion -- purely a reclassification, the same discipline
`atlas.alpha.coverage`/`atlas.alpha.evidence_quality` already follow.

**Extension mechanism (Phase 5).** `_DOMAIN_EXTRACTORS` is a closed
domain -> extractor-function registry, the same shape
`atlas.analysis_engine.business_facts.extraction`'s own
`_METADATA_KEYS` already uses. The engine's one loop iterates every
`KnowledgeDomain` member; a domain **absent** from the registry is
automatically classified `NOT_APPLICABLE` -- the loop itself never
special-cases "not wired yet," it is simply a dict miss. A future
sprint wiring a new domain (e.g. `MANAGEMENT` -- real Management
Intelligence knowledge already exists in `InvestmentCaseComposition`
via `management_credibility_intelligence.py`/`executive_change_
intelligence.py`/etc., but no extractor reads it into Coverage yet --
see `atlas.alpha.investment_case.growth_intelligence`'s own extraction
pattern for the shape a new extractor takes) adds one new extractor
function and one new registry entry; it never touches this loop,
`atlas.alpha.coverage`, or any
Decision-layer package.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from atlas.alpha.coverage.models import DimensionCoverageLevel
from atlas.alpha.evidence_quality.models import EvidenceDominance, EvidenceFreshness, EvidenceQualityReport
from atlas.alpha.investment_case.historical_valuation import ValuationDataQuality
from atlas.alpha.investment_case.models import InvestmentCaseComposition

_MIN_PERIODS_FOR_STATEMENT_INTELLIGENCE = 3
"""(Capability Expansion Sprint 3) Mirrors `_MIN_PERIODS_AVAILABLE`'s
own threshold below -- a fresh, module-level constant rather than a
shared import, since the two governed domains (`FINANCIAL_HISTORY`'s
raw period count vs. these three's own per-field completeness) answer
genuinely different questions even though the number happens to
match."""
from atlas.alpha.portfolio_status.service import VERY_OLD_CASE_THRESHOLD_DAYS
from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.valuation.facts import ValuationFactKind

from .models import (
    DOMAIN_GROUP,
    InvestmentCaseKnowledgeCoverage,
    KnowledgeDomain,
    KnowledgeDomainCoverage,
    MissingKnowledgeReason,
)

__all__ = ["assess_knowledge_coverage"]

#: Bucket boundaries re-derived as whole multiples of the one existing,
#: real threshold this codebase already has -- the identical convention
#: `atlas.alpha.evidence_quality.engine` already follows independently
#: rather than importing that module's own private helper.
_RECENT_THRESHOLD_DAYS = VERY_OLD_CASE_THRESHOLD_DAYS
_OLD_THRESHOLD_DAYS = VERY_OLD_CASE_THRESHOLD_DAYS * 2
_STALE_THRESHOLD_DAYS = VERY_OLD_CASE_THRESHOLD_DAYS * 4

#: A `FinancialPeriod`/`FactQuality` history is considered `AVAILABLE`
#: from 3 fiscal years -- a new, independently documented threshold (no
#: existing "minimum periods" constant was found anywhere else in this
#: codebase to reuse).
_MIN_PERIODS_AVAILABLE = 3

_CAPITAL_ALLOCATION_FACT_KINDS: tuple[BusinessFactKind, ...] = (
    BusinessFactKind.CAPITAL_EXPENDITURE,
    BusinessFactKind.SHARE_BUYBACKS,
    BusinessFactKind.SHARE_ISSUANCE,
    BusinessFactKind.DIVIDENDS,
    BusinessFactKind.DEBT_ISSUANCE,
    BusinessFactKind.DEBT_REPAYMENT,
    BusinessFactKind.SHARES_OUTSTANDING,
)
"""(Capability Expansion Sprint 4) The exact seven `BusinessFactKind`
members `atlas.analysis_engine.capital_allocation.evaluate_capital_
allocation` already reads -- confirmed by reading that evaluator's own
source before this constant was written, not assumed."""

_GROWTH_FACT_KINDS: tuple[BusinessFactKind, ...] = (BusinessFactKind.REVENUE, BusinessFactKind.FREE_CASH_FLOW)
"""(Capability Expansion Sprint 6) The exact two `BusinessFactKind`
members `atlas.analysis_engine.growth.evaluate_growth` already reads --
confirmed by reading that evaluator's own source before this constant
was written, not assumed."""

_DOMAIN_FACT_KINDS: dict[KnowledgeDomain, tuple[str, ...]] = {
    KnowledgeDomain.FINANCIAL_HISTORY: tuple(kind.value for kind in BusinessFactKind),
    KnowledgeDomain.VALUATION: tuple(kind.value for kind in ValuationFactKind),
    KnowledgeDomain.HISTORICAL_VALUATION: tuple(kind.value for kind in ValuationFactKind),
    KnowledgeDomain.CAPITAL_ALLOCATION: tuple(kind.value for kind in _CAPITAL_ALLOCATION_FACT_KINDS),
    KnowledgeDomain.GROWTH: tuple(kind.value for kind in _GROWTH_FACT_KINDS),
}
"""Which already-computed `FactQuality.fact_kind` values roll up into
which `KnowledgeDomain`'s freshness/dominance -- the same closed-
mapping shape `business_facts.extraction`'s own `_METADATA_KEYS` uses.
`HISTORICAL_VALUATION` deliberately shares `VALUATION`'s own entry: it
is built from the identical `ValuationFact` kinds (share price, shares
outstanding) -- more observations of the same two facts, not a new
fact kind -- so it gets the same freshness/dominance signal via the
existing generic `_freshness_dominance_from_facts` path below, rather
than a new dedicated branch. `CAPITAL_ALLOCATION` is the same story,
one layer over: unlike `PROFITABILITY`/`CASH_FLOW`/`BALANCE_SHEET`
(Sprint 3, which deliberately keep their own new fields out of
`BusinessFactKind`), Capital Allocation's own raw facts already are
real, already-consumed `BusinessFactKind` members -- so this domain
also gets its freshness/dominance from the existing generic path,
never a new dedicated branch."""


@dataclass(frozen=True)
class _Presence:
    level: DimensionCoverageLevel
    missing_reasons: tuple[MissingKnowledgeReason, ...]


def _presence_from_company_profile(composition: InvestmentCaseComposition) -> _Presence:
    profile = composition.company_profile
    if profile is None:
        return _Presence(DimensionCoverageLevel.UNAVAILABLE, (MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,))
    if profile.sector is None or profile.industry is None or profile.country is None:
        return _Presence(
            DimensionCoverageLevel.PARTIALLY_AVAILABLE, (MissingKnowledgeReason.DESCRIPTIVE_FIELDS_INCOMPLETE,)
        )
    return _Presence(DimensionCoverageLevel.AVAILABLE, ())


def _presence_from_financial_history(composition: InvestmentCaseComposition) -> _Presence:
    period_count = len(composition.financial_history)
    if period_count == 0:
        return _Presence(DimensionCoverageLevel.UNAVAILABLE, (MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,))
    if period_count < _MIN_PERIODS_AVAILABLE:
        return _Presence(DimensionCoverageLevel.PARTIALLY_AVAILABLE, (MissingKnowledgeReason.INSUFFICIENT_HISTORY,))
    return _Presence(DimensionCoverageLevel.AVAILABLE, ())


def _presence_from_market_facts(composition: InvestmentCaseComposition) -> _Presence:
    if not composition.market_facts:
        return _Presence(DimensionCoverageLevel.UNAVAILABLE, (MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,))
    return _Presence(DimensionCoverageLevel.AVAILABLE, ())


def _presence_from_regulatory_filings(composition: InvestmentCaseComposition) -> _Presence:
    if not composition.regulatory_filings:
        return _Presence(DimensionCoverageLevel.UNAVAILABLE, (MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,))
    return _Presence(DimensionCoverageLevel.AVAILABLE, ())


#: The two form types `atlas.alpha.investment_case.governance_
#: intelligence.extract_governance_knowledge` can actually derive
#: anything from (10-K's own real Item 10/11 sections, DEF 14A's own
#: raw governance-relevant text) -- confirmed by reading that module's
#: own extraction logic, not assumed. A company with only 10-Q/8-K
#: filings ingested has zero governance-relevant source material, even
#: though `REGULATORY_FILINGS` itself would already report `AVAILABLE`.
_GOVERNANCE_RELEVANT_FORM_TYPES = frozenset({"10-K", "DEF 14A"})


def _presence_from_governance(composition: InvestmentCaseComposition) -> _Presence:
    """A cheap, synchronous presence check over already-ingested filing
    *metadata* only -- mirrors `_presence_from_regulatory_filings`
    exactly. It never fetches or parses a filing's own content (that is
    `governance_intelligence.py`'s own, genuinely expensive, on-demand
    job, the same "coverage is a proxy signal, not the full
    computation" boundary `REGULATORY_FILINGS` itself already holds)."""
    if not any(f.form_type in _GOVERNANCE_RELEVANT_FORM_TYPES for f in composition.regulatory_filings):
        return _Presence(DimensionCoverageLevel.UNAVAILABLE, (MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,))
    return _Presence(DimensionCoverageLevel.AVAILABLE, ())


#: (Capability Expansion Sprint 17) The two form types `atlas.alpha.
#: investment_case.risk_factor_intelligence.extract_risk_factor_
#: knowledge` can actually derive anything from -- 10-K's own real Item
#: 1A/7, 10-Q's own real Part II Item 1A/Part I Item 2 -- confirmed by
#: reading that module's own extraction logic, not assumed. Unlike
#: `KnowledgeDomain.GOVERNANCE` (added in Sprint 15), `RISK_FACTORS`
#: already existed in the base `KnowledgeDomain` enum -- this sprint
#: only wires its first real extractor; no new domain.
_RISK_FACTOR_RELEVANT_FORM_TYPES = frozenset({"10-K", "10-Q"})


def _presence_from_risk_factors(composition: InvestmentCaseComposition) -> _Presence:
    """Mirrors `_presence_from_governance` exactly -- a cheap,
    synchronous check over already-ingested filing metadata only, never
    the genuinely expensive fetch/parse `risk_factor_intelligence.py`
    itself performs on demand."""
    if not any(f.form_type in _RISK_FACTOR_RELEVANT_FORM_TYPES for f in composition.regulatory_filings):
        return _Presence(DimensionCoverageLevel.UNAVAILABLE, (MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,))
    return _Presence(DimensionCoverageLevel.AVAILABLE, ())


#: (Capability Expansion Sprint 18) Same two form types as `RISK_
#: FACTOR_RELEVANT_FORM_TYPES` -- `legal_proceedings_intelligence.py`
#: reads 10-K Item 3 directly, and falls back to the same Risk Factors/
#: MD&A sections on both 10-K and 10-Q for incidental legal mentions
#: (10-Q's own Part II Item 1 has no reliable section boundary in this
#: build of Filing Content Intelligence -- a real, disclosed limitation,
#: not something this presence check can see around).
_LEGAL_PROCEEDINGS_RELEVANT_FORM_TYPES = frozenset({"10-K", "10-Q"})


def _presence_from_legal_proceedings(composition: InvestmentCaseComposition) -> _Presence:
    """Mirrors `_presence_from_risk_factors` exactly -- a cheap,
    synchronous check over already-ingested filing metadata only."""
    if not any(f.form_type in _LEGAL_PROCEEDINGS_RELEVANT_FORM_TYPES for f in composition.regulatory_filings):
        return _Presence(DimensionCoverageLevel.UNAVAILABLE, (MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,))
    return _Presence(DimensionCoverageLevel.AVAILABLE, ())


#: (Capability Expansion Sprint 19) `ownership_intelligence.py`'s own
#: real, reachable evidence is almost entirely DEF 14A -- 10-K's own
#: real Item 12 ("Security Ownership of Certain Beneficial Owners and
#: Management") has no item-map entry in this build of Filing Content
#: Intelligence either (most real 10-Ks incorporate it by reference to
#: the proxy rather than reprint it, so this is a smaller practical gap
#: than 10-Q's own missing Item 1 was for Legal Proceedings, but the
#: same real, disclosed limitation in kind). `KnowledgeDomain.
#: OWNERSHIP` already existed in the base enum -- unlike `GOVERNANCE`/
#: `LEGAL_PROCEEDINGS`, this sprint only wires its first real extractor.
_OWNERSHIP_RELEVANT_FORM_TYPES = frozenset({"DEF 14A"})


def _presence_from_ownership(composition: InvestmentCaseComposition) -> _Presence:
    """Mirrors `_presence_from_governance` exactly -- a cheap,
    synchronous check over already-ingested filing metadata only, never
    the genuinely expensive fetch/parse `ownership_intelligence.py`
    itself performs on demand."""
    if not any(f.form_type in _OWNERSHIP_RELEVANT_FORM_TYPES for f in composition.regulatory_filings):
        return _Presence(DimensionCoverageLevel.UNAVAILABLE, (MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,))
    return _Presence(DimensionCoverageLevel.AVAILABLE, ())


#: (Capability Expansion Sprint 20) `executive_compensation_
#: intelligence.py`'s own real, reachable evidence is DEF 14A only --
#: the Summary Compensation Table has no counterpart reliably reachable
#: from a 10-K or 10-Q in this build.
_EXECUTIVE_COMPENSATION_RELEVANT_FORM_TYPES = frozenset({"DEF 14A"})


def _presence_from_executive_compensation(composition: InvestmentCaseComposition) -> _Presence:
    """Mirrors `_presence_from_ownership` exactly -- a cheap,
    synchronous check over already-ingested filing metadata only, never
    the genuinely expensive fetch/parse `executive_compensation_
    intelligence.py` itself performs on demand."""
    if not any(f.form_type in _EXECUTIVE_COMPENSATION_RELEVANT_FORM_TYPES for f in composition.regulatory_filings):
        return _Presence(DimensionCoverageLevel.UNAVAILABLE, (MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,))
    return _Presence(DimensionCoverageLevel.AVAILABLE, ())


def _presence_from_historical_valuation(composition: InvestmentCaseComposition) -> _Presence:
    metrics = composition.historical_valuation.metrics
    if not metrics:
        return _Presence(DimensionCoverageLevel.UNAVAILABLE, (MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,))
    if all(metric.data_quality is not ValuationDataQuality.SUFFICIENT for metric in metrics):
        return _Presence(DimensionCoverageLevel.PARTIALLY_AVAILABLE, (MissingKnowledgeReason.INSUFFICIENT_HISTORY,))
    return _Presence(DimensionCoverageLevel.AVAILABLE, ())


def _presence_from_earnings_call(composition: InvestmentCaseComposition) -> _Presence:
    transcripts = composition.earnings_call.transcripts
    if not transcripts:
        return _Presence(DimensionCoverageLevel.UNAVAILABLE, (MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,))
    if len(transcripts) < 2:
        # Real knowledge exists (a real quarter's own management
        # commentary), but Phase 4's own Change Intelligence -- the
        # thing that makes earnings calls "especially valuable over
        # time" per this sprint's own Phase 4 -- needs at least two to
        # compare.
        return _Presence(DimensionCoverageLevel.PARTIALLY_AVAILABLE, (MissingKnowledgeReason.INSUFFICIENT_HISTORY,))
    return _Presence(DimensionCoverageLevel.AVAILABLE, ())


def _presence_from_growth(composition: InvestmentCaseComposition) -> _Presence:
    revenue_periods = composition.growth_intelligence.revenue.periods_considered
    fcf_periods = composition.growth_intelligence.free_cash_flow.periods_considered
    if revenue_periods == 0 and fcf_periods == 0:
        return _Presence(DimensionCoverageLevel.UNAVAILABLE, (MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,))
    if revenue_periods < _MIN_PERIODS_FOR_STATEMENT_INTELLIGENCE or fcf_periods < _MIN_PERIODS_FOR_STATEMENT_INTELLIGENCE:
        return _Presence(DimensionCoverageLevel.PARTIALLY_AVAILABLE, (MissingKnowledgeReason.INSUFFICIENT_HISTORY,))
    return _Presence(DimensionCoverageLevel.AVAILABLE, ())


def _presence_from_profitability(composition: InvestmentCaseComposition) -> _Presence:
    periods = composition.financial_statement_intelligence.income_statements
    with_margin = [p for p in periods if p.net_margin is not None]
    if not periods:
        return _Presence(DimensionCoverageLevel.UNAVAILABLE, (MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,))
    if len(with_margin) < _MIN_PERIODS_FOR_STATEMENT_INTELLIGENCE:
        return _Presence(DimensionCoverageLevel.PARTIALLY_AVAILABLE, (MissingKnowledgeReason.INSUFFICIENT_HISTORY,))
    return _Presence(DimensionCoverageLevel.AVAILABLE, ())


def _presence_from_cash_flow(composition: InvestmentCaseComposition) -> _Presence:
    periods = composition.financial_statement_intelligence.cash_flow_statements
    with_ocf = [p for p in periods if p.operating_cash_flow is not None]
    if not periods:
        return _Presence(DimensionCoverageLevel.UNAVAILABLE, (MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,))
    if len(with_ocf) < _MIN_PERIODS_FOR_STATEMENT_INTELLIGENCE:
        return _Presence(DimensionCoverageLevel.PARTIALLY_AVAILABLE, (MissingKnowledgeReason.INSUFFICIENT_HISTORY,))
    return _Presence(DimensionCoverageLevel.AVAILABLE, ())


def _presence_from_balance_sheet(composition: InvestmentCaseComposition) -> _Presence:
    periods = composition.financial_statement_intelligence.balance_sheets
    with_equity = [p for p in periods if p.equity is not None]
    if not periods:
        return _Presence(DimensionCoverageLevel.UNAVAILABLE, (MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,))
    if len(with_equity) < _MIN_PERIODS_FOR_STATEMENT_INTELLIGENCE:
        return _Presence(DimensionCoverageLevel.PARTIALLY_AVAILABLE, (MissingKnowledgeReason.INSUFFICIENT_HISTORY,))
    return _Presence(DimensionCoverageLevel.AVAILABLE, ())


def _presence_from_capital_allocation(composition: InvestmentCaseComposition) -> _Presence:
    periods = composition.capital_allocation_intelligence.periods
    if not periods:
        return _Presence(DimensionCoverageLevel.UNAVAILABLE, (MissingKnowledgeReason.NO_SOURCE_DOCUMENT_INGESTED,))
    with_core_signal = [
        p for p in periods
        if p.share_buybacks is not None or p.share_issuance is not None
        or p.debt_issuance is not None or p.debt_repayment is not None
    ]
    if len(with_core_signal) < _MIN_PERIODS_FOR_STATEMENT_INTELLIGENCE:
        return _Presence(DimensionCoverageLevel.PARTIALLY_AVAILABLE, (MissingKnowledgeReason.INSUFFICIENT_HISTORY,))
    return _Presence(DimensionCoverageLevel.AVAILABLE, ())


_DOMAIN_EXTRACTORS: dict[KnowledgeDomain, Callable[[InvestmentCaseComposition], _Presence]] = {
    KnowledgeDomain.COMPANY_PROFILE: _presence_from_company_profile,
    KnowledgeDomain.FINANCIAL_HISTORY: _presence_from_financial_history,
    KnowledgeDomain.VALUATION: _presence_from_market_facts,
    KnowledgeDomain.REGULATORY_FILINGS: _presence_from_regulatory_filings,
    KnowledgeDomain.GOVERNANCE: _presence_from_governance,
    KnowledgeDomain.RISK_FACTORS: _presence_from_risk_factors,
    KnowledgeDomain.LEGAL_PROCEEDINGS: _presence_from_legal_proceedings,
    KnowledgeDomain.OWNERSHIP: _presence_from_ownership,
    KnowledgeDomain.EXECUTIVE_COMPENSATION: _presence_from_executive_compensation,
    KnowledgeDomain.HISTORICAL_VALUATION: _presence_from_historical_valuation,
    KnowledgeDomain.EARNINGS_CALL_ANALYSIS: _presence_from_earnings_call,
    KnowledgeDomain.PROFITABILITY: _presence_from_profitability,
    KnowledgeDomain.CASH_FLOW: _presence_from_cash_flow,
    KnowledgeDomain.BALANCE_SHEET: _presence_from_balance_sheet,
    KnowledgeDomain.CAPITAL_ALLOCATION: _presence_from_capital_allocation,
    KnowledgeDomain.GROWTH: _presence_from_growth,
}


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


def _freshness_dominance_from_facts(
    domain: KnowledgeDomain, evidence_quality: EvidenceQualityReport
) -> tuple[EvidenceFreshness, EvidenceDominance]:
    kinds = _DOMAIN_FACT_KINDS.get(domain, ())
    matching = tuple(f for f in evidence_quality.facts if f.fact_kind in kinds)
    if not matching:
        return EvidenceFreshness.NOT_APPLICABLE, EvidenceDominance.NOT_APPLICABLE
    freshness = _worst_freshness(tuple(f.freshness for f in matching))
    single_source = any(f.dominance is EvidenceDominance.SINGLE_SOURCE for f in matching)
    dominance = EvidenceDominance.SINGLE_SOURCE if single_source else EvidenceDominance.CORROBORATED
    return freshness, dominance


def _freshness_dominance_for_company_profile(
    composition: InvestmentCaseComposition, records: tuple[BusinessRecord, ...], *, evaluated_at: datetime
) -> tuple[EvidenceFreshness, EvidenceDominance]:
    """`CompanyProfile` has no `FactQuality` counterpart (it is not
    extracted via `extract_facts`) -- freshness/dominance are computed
    directly from `company_profile.as_of` and a raw count of
    `COMPANY_PROFILE`-kind records among `records`, the identical
    threshold/severity rules `_freshness_from_age_days` already applies
    to every fact-backed domain."""
    profile = composition.company_profile
    if profile is None:
        return EvidenceFreshness.NOT_APPLICABLE, EvidenceDominance.NOT_APPLICABLE
    age_days = (evaluated_at - profile.as_of).total_seconds() / 86400
    freshness = _freshness_from_age_days(age_days)
    profile_record_count = sum(1 for r in records if r.document_type is SourceKind.COMPANY_PROFILE)
    dominance = EvidenceDominance.SINGLE_SOURCE if profile_record_count <= 1 else EvidenceDominance.CORROBORATED
    return freshness, dominance


def _freshness_dominance_for_regulatory_filings(
    composition: InvestmentCaseComposition, records: tuple[BusinessRecord, ...], *, evaluated_at: datetime
) -> tuple[EvidenceFreshness, EvidenceDominance]:
    """`RegulatoryFiling` has no `FactQuality` counterpart either (it
    is not extracted via `extract_facts`) -- freshness is computed from
    the single most recent filing's own `filed_at` (a real, growing
    filing history should be graded by its most current entry, the
    same "worst/most-recent single value drives the domain" reasoning
    `_freshness_dominance_for_company_profile` already applies), and
    dominance from a raw count of `COMPANY_FILING`-kind records among
    `records` -- multiple distinct filings are not "corroboration" of
    one fact the way multiple sources for one number would be, but
    counting real records is still the same honest signal
    `_freshness_dominance_for_company_profile` already uses for its
    own single-record-type domain."""
    filings = composition.regulatory_filings
    if not filings:
        return EvidenceFreshness.NOT_APPLICABLE, EvidenceDominance.NOT_APPLICABLE
    most_recent = filings[0].filed_at  # extract_regulatory_filings already sorts newest-first
    age_days = (evaluated_at - most_recent).total_seconds() / 86400
    freshness = _freshness_from_age_days(age_days)
    filing_record_count = sum(1 for r in records if r.document_type is SourceKind.COMPANY_FILING)
    dominance = EvidenceDominance.SINGLE_SOURCE if filing_record_count <= 1 else EvidenceDominance.CORROBORATED
    return freshness, dominance


def _freshness_dominance_for_earnings_call(
    composition: InvestmentCaseComposition, records: tuple[BusinessRecord, ...], *, evaluated_at: datetime
) -> tuple[EvidenceFreshness, EvidenceDominance]:
    """`EarningsCallTranscript` has no `FactQuality` counterpart either
    -- freshness is graded from the most recent transcript's own
    `fiscal_date_ending` (a real business event date, the same
    "graded by its most current entry" reasoning `_freshness_dominance_
    for_regulatory_filings` already applies), not from when Atlas
    happened to fetch it. Dominance from a raw count of `TRANSCRIPT`-
    kind records among `records` -- many individual-statement documents
    from the *same* quarter are not independent corroboration of one
    fact, but counting them is still the same honest, real signal
    `_freshness_dominance_for_company_profile`'s own single-record-type
    domain already uses."""
    transcripts = composition.earnings_call.transcripts
    if not transcripts:
        return EvidenceFreshness.NOT_APPLICABLE, EvidenceDominance.NOT_APPLICABLE
    most_recent = transcripts[-1]  # extract_earnings_call_knowledge already sorts oldest-first
    reference_date = most_recent.fiscal_date_ending or most_recent.published_at
    age_days = (evaluated_at.date() - reference_date).days
    freshness = _freshness_from_age_days(float(age_days))
    transcript_record_count = sum(1 for r in records if r.document_type is SourceKind.TRANSCRIPT)
    dominance = EvidenceDominance.SINGLE_SOURCE if transcript_record_count <= 1 else EvidenceDominance.CORROBORATED
    return freshness, dominance


def _freshness_dominance_for_financial_statement_intelligence(
    records: tuple[BusinessRecord, ...], *, evaluated_at: datetime
) -> tuple[EvidenceFreshness, EvidenceDominance]:
    """(Capability Expansion Sprint 3) Shared by `PROFITABILITY`/
    `CASH_FLOW`/`BALANCE_SHEET` -- all three are built from the
    identical `FINANCIAL_STATEMENT` records `FINANCIAL_HISTORY` itself
    reads, but through raw `BusinessRecord.metadata` keys that are not
    `BusinessFactKind` members (see `financial_statement_intelligence
    .py`'s own module docstring for why), so the generic `FactQuality`
    -based path below cannot see them -- this mirrors `_freshness_
    dominance_for_regulatory_filings`'s own "no FactQuality counterpart"
    pattern instead: freshness from the most recent statement's own
    `period_end`, dominance from a raw count of matching records."""
    statement_records = [r for r in records if r.document_type is SourceKind.FINANCIAL_STATEMENT]
    if not statement_records:
        return EvidenceFreshness.NOT_APPLICABLE, EvidenceDominance.NOT_APPLICABLE
    most_recent_end = max(r.period_end or r.published_at.date() for r in statement_records)
    age_days = (evaluated_at.date() - most_recent_end).days
    freshness = _freshness_from_age_days(float(age_days))
    dominance = EvidenceDominance.SINGLE_SOURCE if len(statement_records) <= 1 else EvidenceDominance.CORROBORATED
    return freshness, dominance


def _coverage_for_domain(
    domain: KnowledgeDomain,
    composition: InvestmentCaseComposition,
    evidence_quality: EvidenceQualityReport,
    records: tuple[BusinessRecord, ...],
    *,
    evaluated_at: datetime,
) -> KnowledgeDomainCoverage:
    extractor = _DOMAIN_EXTRACTORS.get(domain)
    if extractor is None:
        return KnowledgeDomainCoverage(
            domain=domain,
            group=DOMAIN_GROUP[domain],
            level=DimensionCoverageLevel.NOT_APPLICABLE,
            freshness=EvidenceFreshness.NOT_APPLICABLE,
            dominance=EvidenceDominance.NOT_APPLICABLE,
            missing_reasons=(MissingKnowledgeReason.DOMAIN_NOT_YET_WIRED,),
        )

    presence = extractor(composition)
    if domain is KnowledgeDomain.COMPANY_PROFILE:
        freshness, dominance = _freshness_dominance_for_company_profile(composition, records, evaluated_at=evaluated_at)
    elif domain is KnowledgeDomain.REGULATORY_FILINGS:
        freshness, dominance = _freshness_dominance_for_regulatory_filings(composition, records, evaluated_at=evaluated_at)
    elif domain is KnowledgeDomain.EARNINGS_CALL_ANALYSIS:
        freshness, dominance = _freshness_dominance_for_earnings_call(composition, records, evaluated_at=evaluated_at)
    elif domain in (KnowledgeDomain.PROFITABILITY, KnowledgeDomain.CASH_FLOW, KnowledgeDomain.BALANCE_SHEET):
        freshness, dominance = _freshness_dominance_for_financial_statement_intelligence(records, evaluated_at=evaluated_at)
    else:
        freshness, dominance = _freshness_dominance_from_facts(domain, evidence_quality)

    missing_reasons = presence.missing_reasons
    if presence.level is DimensionCoverageLevel.AVAILABLE and freshness is EvidenceFreshness.STALE:
        missing_reasons = (*missing_reasons, MissingKnowledgeReason.EVIDENCE_STALE)

    return KnowledgeDomainCoverage(
        domain=domain,
        group=DOMAIN_GROUP[domain],
        level=presence.level,
        freshness=freshness,
        dominance=dominance,
        missing_reasons=missing_reasons,
    )


def assess_knowledge_coverage(
    composition: InvestmentCaseComposition,
    evidence_quality: EvidenceQualityReport,
    records: tuple[BusinessRecord, ...],
    *,
    evaluated_at: datetime,
) -> InvestmentCaseKnowledgeCoverage:
    """Deterministic: identical inputs always produce a deeply equal
    `InvestmentCaseKnowledgeCoverage`. `records` should be the same
    `latest_versions`-filtered set already passed to
    `assess_evidence_quality` -- never re-fetched or re-filtered here."""
    domains = tuple(
        _coverage_for_domain(domain, composition, evidence_quality, records, evaluated_at=evaluated_at)
        for domain in KnowledgeDomain
    )

    available_count = sum(1 for d in domains if d.level is DimensionCoverageLevel.AVAILABLE)
    partially_available_count = sum(1 for d in domains if d.level is DimensionCoverageLevel.PARTIALLY_AVAILABLE)
    not_applicable_domains = tuple(d.domain for d in domains if d.level is DimensionCoverageLevel.NOT_APPLICABLE)
    missing_domains = tuple(d.domain for d in domains if d.level is DimensionCoverageLevel.UNAVAILABLE)
    applicable_count = len(domains) - len(not_applicable_domains)

    return InvestmentCaseKnowledgeCoverage(
        domains=domains,
        available_count=available_count,
        partially_available_count=partially_available_count,
        applicable_count=applicable_count,
        total_domain_count=len(domains),
        not_applicable_count=len(not_applicable_domains),
        missing_domains=missing_domains,
        not_applicable_domains=not_applicable_domains,
    )

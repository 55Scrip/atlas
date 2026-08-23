"""Result shapes for the Knowledge Coverage Engine (Automatic Investment
Case Builder Foundation). See `engine.py`'s own module docstring for
the full derivation rules.

This package answers a different, lower-level question than
`atlas.alpha.coverage`: not "has Atlas concluded something about this
Case" (evaluator-conclusion coverage, `DimensionCoverageLevel` scoped
to `BusinessCategory`/`ValuationMethodKind`/`RiskCategory`), but "does
Atlas have the raw knowledge to conclude anything about this domain at
all." The two are deliberately kept separate, the same way `coverage`
and `evidence_quality` already are -- this package reuses
`DimensionCoverageLevel`/`EvidenceFreshness`/`EvidenceDominance`
verbatim rather than inventing parallel vocabulary, but classifies a
different, wider set of domains (`KnowledgeDomain`, 36 members) than
either existing engine touches.

(Capability Expansion Sprint 15) `KnowledgeDomain.GOVERNANCE` was added
-- board composition, committees, and voting structure had no existing
domain to live under (`MANAGEMENT` covers executive/management
intelligence, `OWNERSHIP`/`INSTITUTIONAL_OWNERSHIP`/`INSIDER_ACTIVITY`
cover shareholding, not board structure) -- confirmed by reading every
`GOVERNANCE_OWNERSHIP` member fresh before adding a new one, not
assumed. 37 members as of this sprint.

(Capability Expansion Sprint 18) `KnowledgeDomain.LEGAL_PROCEEDINGS`
was added -- 10-K Item 3 / 10-Q Part II Item 1 legal disclosures are a
genuinely distinct evidence source from `RISK_FACTORS` (Item 1A), with
their own filing location and their own disclosure-history semantics
(`legal_proceedings_intelligence.py`) -- confirmed by reading every
`RISK_OPPORTUNITY` member fresh before adding a new one, not assumed.

(Capability Expansion Sprint 20) `KnowledgeDomain.EXECUTIVE_COMPENSATION`
was added -- the existing `MANAGEMENT` domain's own real sources
(`management_credibility_intelligence.py`/`executive_change_
intelligence.py`/etc.) are all earnings-call-derived, a genuinely
different evidence source and disclosure convention from a DEF 14A's
own Summary Compensation Table; wiring compensation presence under the
broader `MANAGEMENT` label would misrepresent what that domain's own
coverage actually means. Confirmed by reading every `GOVERNANCE_
OWNERSHIP` member fresh before adding a new one, not assumed. 39
members as of this sprint.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from atlas.alpha.coverage.models import DimensionCoverageLevel
from atlas.alpha.evidence_quality.models import EvidenceDominance, EvidenceFreshness

__all__ = [
    "KnowledgeDomainGroup",
    "KnowledgeDomain",
    "MissingKnowledgeReason",
    "KnowledgeDomainCoverage",
    "InvestmentCaseKnowledgeCoverage",
]


class KnowledgeDomainGroup(str, Enum):
    """The 8 logical groupings every `KnowledgeDomain` belongs to --
    purely an organizational fact for presentation (mirrors
    `atlas.alpha.daily_brief_agenda.models.AgendaGroup`'s own role next
    to `AgendaItemKind`), never itself a coverage signal."""

    COMPANY_OVERVIEW = "company_overview"
    FINANCIALS = "financials"
    GOVERNANCE_OWNERSHIP = "governance_ownership"
    VALUATION = "valuation"
    EVENTS_FILINGS = "events_filings"
    MACRO_EXTERNAL_EXPOSURE = "macro_external_exposure"
    RISK_OPPORTUNITY = "risk_opportunity"
    CASE_MEMORY = "case_memory"


class KnowledgeDomain(str, Enum):
    """The complete long-term knowledge structure of an Investment
    Case -- a closed, growing taxonomy (the same "add a member, never
    branch on a string" discipline `SourceKind`/`BusinessFactKind`
    already establish). 39 members today; 16 have a real extractor
    wired in this build of Atlas (see `engine.py`'s own
    `_DOMAIN_EXTRACTORS` for the current, authoritative list) --
    every other member is honestly `NOT_APPLICABLE` until a future
    sprint wires a provider for it (see `engine.py`'s own module
    docstring for the concrete extension mechanism). This sprint
    establishes the framework, not the complete dataset."""

    # -- COMPANY_OVERVIEW --
    COMPANY_PROFILE = "company_profile"
    BUSINESS_MODEL = "business_model"
    REVENUE_SEGMENTS = "revenue_segments"
    GEOGRAPHIC_EXPOSURE = "geographic_exposure"
    INDUSTRY = "industry"
    COMPETITORS = "competitors"
    COMPETITIVE_ADVANTAGES = "competitive_advantages"
    # -- FINANCIALS --
    FINANCIAL_HISTORY = "financial_history"
    GROWTH = "growth"
    PROFITABILITY = "profitability"
    CASH_FLOW = "cash_flow"
    BALANCE_SHEET = "balance_sheet"
    CAPITAL_ALLOCATION = "capital_allocation"
    SHAREHOLDER_RETURNS = "shareholder_returns"
    # -- GOVERNANCE_OWNERSHIP --
    MANAGEMENT = "management"
    GOVERNANCE = "governance"
    EXECUTIVE_COMPENSATION = "executive_compensation"
    OWNERSHIP = "ownership"
    INSIDER_ACTIVITY = "insider_activity"
    INSTITUTIONAL_OWNERSHIP = "institutional_ownership"
    # -- VALUATION --
    VALUATION = "valuation"
    HISTORICAL_VALUATION = "historical_valuation"
    ANALYST_EXPECTATIONS = "analyst_expectations"
    # -- EVENTS_FILINGS --
    EARNINGS = "earnings"
    EARNINGS_CALL_ANALYSIS = "earnings_call_analysis"
    REGULATORY_FILINGS = "regulatory_filings"
    IMPORTANT_NEWS = "important_news"
    # -- MACRO_EXTERNAL_EXPOSURE --
    MACRO_EXPOSURE = "macro_exposure"
    GEOPOLITICAL_EXPOSURE = "geopolitical_exposure"
    COMMODITY_EXPOSURE = "commodity_exposure"
    CURRENCY_EXPOSURE = "currency_exposure"
    AI_EXPOSURE = "ai_exposure"
    # -- RISK_OPPORTUNITY --
    RISK_FACTORS = "risk_factors"
    LEGAL_PROCEEDINGS = "legal_proceedings"
    OPPORTUNITIES = "opportunities"
    # -- CASE_MEMORY --
    MONITORING_STATUS = "monitoring_status"
    HISTORICAL_OBSERVATIONS = "historical_observations"
    EXISTING_EVIDENCE = "existing_evidence"
    KNOWLEDGE_REFERENCES = "knowledge_references"


DOMAIN_GROUP: dict[KnowledgeDomain, KnowledgeDomainGroup] = {
    KnowledgeDomain.COMPANY_PROFILE: KnowledgeDomainGroup.COMPANY_OVERVIEW,
    KnowledgeDomain.BUSINESS_MODEL: KnowledgeDomainGroup.COMPANY_OVERVIEW,
    KnowledgeDomain.REVENUE_SEGMENTS: KnowledgeDomainGroup.COMPANY_OVERVIEW,
    KnowledgeDomain.GEOGRAPHIC_EXPOSURE: KnowledgeDomainGroup.COMPANY_OVERVIEW,
    KnowledgeDomain.INDUSTRY: KnowledgeDomainGroup.COMPANY_OVERVIEW,
    KnowledgeDomain.COMPETITORS: KnowledgeDomainGroup.COMPANY_OVERVIEW,
    KnowledgeDomain.COMPETITIVE_ADVANTAGES: KnowledgeDomainGroup.COMPANY_OVERVIEW,
    KnowledgeDomain.FINANCIAL_HISTORY: KnowledgeDomainGroup.FINANCIALS,
    KnowledgeDomain.GROWTH: KnowledgeDomainGroup.FINANCIALS,
    KnowledgeDomain.PROFITABILITY: KnowledgeDomainGroup.FINANCIALS,
    KnowledgeDomain.CASH_FLOW: KnowledgeDomainGroup.FINANCIALS,
    KnowledgeDomain.BALANCE_SHEET: KnowledgeDomainGroup.FINANCIALS,
    KnowledgeDomain.CAPITAL_ALLOCATION: KnowledgeDomainGroup.FINANCIALS,
    KnowledgeDomain.SHAREHOLDER_RETURNS: KnowledgeDomainGroup.FINANCIALS,
    KnowledgeDomain.MANAGEMENT: KnowledgeDomainGroup.GOVERNANCE_OWNERSHIP,
    KnowledgeDomain.GOVERNANCE: KnowledgeDomainGroup.GOVERNANCE_OWNERSHIP,
    KnowledgeDomain.EXECUTIVE_COMPENSATION: KnowledgeDomainGroup.GOVERNANCE_OWNERSHIP,
    KnowledgeDomain.OWNERSHIP: KnowledgeDomainGroup.GOVERNANCE_OWNERSHIP,
    KnowledgeDomain.INSIDER_ACTIVITY: KnowledgeDomainGroup.GOVERNANCE_OWNERSHIP,
    KnowledgeDomain.INSTITUTIONAL_OWNERSHIP: KnowledgeDomainGroup.GOVERNANCE_OWNERSHIP,
    KnowledgeDomain.VALUATION: KnowledgeDomainGroup.VALUATION,
    KnowledgeDomain.HISTORICAL_VALUATION: KnowledgeDomainGroup.VALUATION,
    KnowledgeDomain.ANALYST_EXPECTATIONS: KnowledgeDomainGroup.VALUATION,
    KnowledgeDomain.EARNINGS: KnowledgeDomainGroup.EVENTS_FILINGS,
    KnowledgeDomain.EARNINGS_CALL_ANALYSIS: KnowledgeDomainGroup.EVENTS_FILINGS,
    KnowledgeDomain.REGULATORY_FILINGS: KnowledgeDomainGroup.EVENTS_FILINGS,
    KnowledgeDomain.IMPORTANT_NEWS: KnowledgeDomainGroup.EVENTS_FILINGS,
    KnowledgeDomain.MACRO_EXPOSURE: KnowledgeDomainGroup.MACRO_EXTERNAL_EXPOSURE,
    KnowledgeDomain.GEOPOLITICAL_EXPOSURE: KnowledgeDomainGroup.MACRO_EXTERNAL_EXPOSURE,
    KnowledgeDomain.COMMODITY_EXPOSURE: KnowledgeDomainGroup.MACRO_EXTERNAL_EXPOSURE,
    KnowledgeDomain.CURRENCY_EXPOSURE: KnowledgeDomainGroup.MACRO_EXTERNAL_EXPOSURE,
    KnowledgeDomain.AI_EXPOSURE: KnowledgeDomainGroup.MACRO_EXTERNAL_EXPOSURE,
    KnowledgeDomain.RISK_FACTORS: KnowledgeDomainGroup.RISK_OPPORTUNITY,
    KnowledgeDomain.LEGAL_PROCEEDINGS: KnowledgeDomainGroup.RISK_OPPORTUNITY,
    KnowledgeDomain.OPPORTUNITIES: KnowledgeDomainGroup.RISK_OPPORTUNITY,
    KnowledgeDomain.MONITORING_STATUS: KnowledgeDomainGroup.CASE_MEMORY,
    KnowledgeDomain.HISTORICAL_OBSERVATIONS: KnowledgeDomainGroup.CASE_MEMORY,
    KnowledgeDomain.EXISTING_EVIDENCE: KnowledgeDomainGroup.CASE_MEMORY,
    KnowledgeDomain.KNOWLEDGE_REFERENCES: KnowledgeDomainGroup.CASE_MEMORY,
}
"""Every `KnowledgeDomain` member's group -- a static fact, not a
computed one, so it lives beside both enums rather than in `engine.py`.
`engine.py`'s own test suite asserts this dict is exhaustive."""


class MissingKnowledgeReason(str, Enum):
    """A closed, presence-only reason vocabulary -- the same
    `EvidenceWarningCode` discipline: the presentation layer owns every
    sentence, this only names the real, structural fact behind a gap."""

    DOMAIN_NOT_YET_WIRED = "domain_not_yet_wired"
    """No extractor/provider exists in this build of Atlas for this
    domain at all -- framework-honest, not a per-Case gap. Always the
    sole reason for every `NOT_APPLICABLE` domain."""
    NO_SOURCE_DOCUMENT_INGESTED = "no_source_document_ingested"
    """A real extractor exists, but this Case has zero relevant
    `BusinessRecord` ingested yet."""
    INSUFFICIENT_HISTORY = "insufficient_history"
    """A real extractor exists and at least one record is ingested, but
    fewer periods/records exist than this domain needs to be complete."""
    DESCRIPTIVE_FIELDS_INCOMPLETE = "descriptive_fields_incomplete"
    """A record exists but one or more expected fields came back `None`
    from the provider."""
    UNDERLYING_INPUTS_MISSING = "underlying_inputs_missing"
    """A derived domain needs facts from more than one other domain and
    at least one prerequisite is missing."""
    EVIDENCE_STALE = "evidence_stale"
    """Real data exists but its freshness bucket is `OLD` or `STALE` --
    "needs a refresh," distinct from "never ingested.\""""


@dataclass(frozen=True)
class KnowledgeDomainCoverage:
    """One knowledge domain's own current state -- answers all five of
    this Sprint's own Phase 2 questions (available? complete? current?
    reliable? what's missing?) with reused, not invented, vocabulary."""

    domain: KnowledgeDomain
    group: KnowledgeDomainGroup
    level: DimensionCoverageLevel
    freshness: EvidenceFreshness
    dominance: EvidenceDominance
    missing_reasons: tuple[MissingKnowledgeReason, ...]
    """Empty exactly when `level` is `AVAILABLE` -- mirrors
    `DimensionCoverage.reasoning`'s own contract. Always exactly
    `(DOMAIN_NOT_YET_WIRED,)` when `level` is `NOT_APPLICABLE`."""


@dataclass(frozen=True)
class InvestmentCaseKnowledgeCoverage:
    """The whole-Case knowledge-completeness picture -- every domain,
    plus the real counts a presentation layer derives its own
    "X of Y domains available" (and, if wanted, a percentage) from.
    Deliberately carries no percentage/score field itself -- see
    `engine.py`'s own module docstring for why that computation belongs
    one layer up, at the API serialization boundary, always alongside
    the counts it came from."""

    domains: tuple[KnowledgeDomainCoverage, ...]
    """Always all 36 `KnowledgeDomain` members, every call -- never a
    filtered subset."""
    available_count: int
    partially_available_count: int
    applicable_count: int
    """Domains with a real extractor wired in this build of Atlas
    (see `engine.py`'s own `_DOMAIN_EXTRACTORS` for the current count)
    -- the honest denominator for a completeness ratio, never
    `total_domain_count` (that would silently penalize Atlas for not
    yet building a domain no company has ever had, the identical
    `AVAILABLE`-vs-`NOT_APPLICABLE` false-precision `DimensionCoverage
    Level`'s own docstring already warns against)."""
    total_domain_count: int
    not_applicable_count: int
    missing_domains: tuple[KnowledgeDomain, ...]
    """Applicable domains at `UNAVAILABLE` -- real, closeable gaps."""
    not_applicable_domains: tuple[KnowledgeDomain, ...]

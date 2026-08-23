"""The Provider Capability Registry (Knowledge Orchestration Engine,
Phase 2).

Capability is declared **in a registry, keyed by the same plain
`provider_id` string every provider already stamps onto its own
`RawBusinessDocument.provider_id`** -- never on the provider class
itself. This is deliberate: no existing provider (`SecEdgarFundamentals
Provider`, `AlphaVantageMarketDataProvider`, `SecEdgarFilingHistory
Provider`) needs to change at all for the orchestration engine to
reason about it -- the explicit non-goal "must not redesign Knowledge
Providers" is honored by construction, not by convention.

`_DOMAIN_CRITICALITY` is a second, small, independent registry --
which `KnowledgeDomain`s an existing evaluator actually depends on.
Confirmed by reading the real evaluator call graph (`atlas.analysis_
engine.growth`/`.capital_allocation`/`.valuation`/`.risk`), not
guessed: only `FINANCIAL_STATEMENT`-sourced facts (`FINANCIAL_HISTORY`)
and `MARKET_DATA_SNAPSHOT`-sourced facts (`VALUATION`) ever reach
`canonical_analysis`. `COMPANY_PROFILE`/`REGULATORY_FILINGS` are real,
useful knowledge Atlas now has -- but no evaluator reasons from them
today, so they are honestly `OPTIONAL`, not `CRITICAL`.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from atlas.alpha.knowledge_coverage.models import KnowledgeDomain
from atlas.analysis_engine.business_data.sources import SourceKind

__all__ = [
    "AcquisitionCost",
    "AcquisitionPriority",
    "ExecutionConstraint",
    "DomainCriticality",
    "ProviderCapability",
    "PROVIDER_CAPABILITIES",
    "DOMAIN_CRITICALITY",
    "capability_for",
    "criticality_of",
]


class AcquisitionCost(str, Enum):
    """Categorical, never a fabricated number -- the same "no invented
    score" discipline every prior Sprint's own vocabulary follows.
    Roughly: one cheap HTTP call vs. several, vs. a heavier multi-call
    fetch (e.g. companyfacts' own large payload)."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AcquisitionPriority(str, Enum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class ExecutionConstraint(str, Enum):
    """A closed, growing vocabulary of real, structural preconditions a
    provider's own call has today -- not a hypothetical."""

    REQUIRES_IDENTITY = "requires_identity"
    """Real, verified: `atlas.alpha.business_data_refresh.service
    .refresh_company_data` runs the Identity Gate first, using
    whichever providers in *that call's own tuple* implement
    `CompanyProfileProvider`. A provider without this constraint (only
    `alpha_vantage` today) IS itself identity-capable; a provider WITH
    this constraint produces zero real `BusinessRecord`s if called
    alone, without an identity-capable provider alongside it in the
    same `refresh_company_data` call -- see `orchestrator.py`'s own
    module docstring for how this is satisfied."""


class DomainCriticality(str, Enum):
    CRITICAL = "critical"
    """A real, already-wired evaluator depends on this domain's own
    extracted facts to reach `canonical_analysis`."""
    OPTIONAL = "optional"
    """Real, useful knowledge -- but no evaluator reasons from it
    today (confirmed by reading the evaluator call graph, not
    assumed)."""


@dataclass(frozen=True)
class ProviderCapability:
    provider_id: str
    supported_domains: tuple[KnowledgeDomain, ...]
    supported_source_kinds: tuple[SourceKind, ...]
    expected_outputs: tuple[str, ...]
    """Short, human-readable labels -- e.g. `("company identity",)` --
    never consumed programmatically; for `OrchestrationOutcomeView`'s
    own "why this provider ran" explanation."""
    prerequisites: tuple[KnowledgeDomain, ...]
    """Domains that must already be non-`MISSING` before this
    provider's own output is trustworthy to request -- resolved by
    `dependency.py`, never assumed by the planner itself."""
    estimated_cost: AcquisitionCost
    estimated_freshness_days: int | None
    """How often this real-world data realistically changes -- `None`
    when there is no meaningful cadence (e.g. a one-time identity
    fact). Purely informational this sprint; not yet consumed to
    override `knowledge_coverage`'s own `VERY_OLD_CASE_THRESHOLD_DAYS`-
    derived freshness buckets (a future sprint's own decision, not
    this one's -- `KnowledgeDomainCoverage` itself is unmodified)."""
    priority: AcquisitionPriority
    execution_constraints: tuple[ExecutionConstraint, ...]


PROVIDER_CAPABILITIES: dict[str, ProviderCapability] = {
    "alpha_vantage": ProviderCapability(
        provider_id="alpha_vantage",
        supported_domains=(
            KnowledgeDomain.COMPANY_PROFILE, KnowledgeDomain.VALUATION, KnowledgeDomain.HISTORICAL_VALUATION,
            KnowledgeDomain.EARNINGS_CALL_ANALYSIS,
        ),
        supported_source_kinds=(SourceKind.COMPANY_PROFILE, SourceKind.MARKET_DATA_SNAPSHOT, SourceKind.TRANSCRIPT),
        expected_outputs=("company identity", "market snapshot", "historical valuation series", "earnings call transcript"),
        prerequisites=(),
        # (Capability Expansion Sprint 2) Corrected from LOW: this
        # provider now makes up to 4 real HTTP calls in one
        # `refresh_company_data` run (OVERVIEW, GLOBAL_QUOTE,
        # TIME_SERIES_MONTHLY_ADJUSTED, EARNINGS_CALL_TRANSCRIPT) --
        # "several calls," the same tier `sec_edgar` is already held to,
        # not "one cheap HTTP call" alone.
        estimated_cost=AcquisitionCost.MEDIUM,
        estimated_freshness_days=1,
        priority=AcquisitionPriority.HIGH,
        execution_constraints=(),
    ),
    "sec_edgar": ProviderCapability(
        provider_id="sec_edgar",
        supported_domains=(
            KnowledgeDomain.FINANCIAL_HISTORY, KnowledgeDomain.PROFITABILITY, KnowledgeDomain.CASH_FLOW,
            KnowledgeDomain.BALANCE_SHEET, KnowledgeDomain.CAPITAL_ALLOCATION, KnowledgeDomain.GROWTH,
        ),
        supported_source_kinds=(SourceKind.FINANCIAL_STATEMENT,),
        expected_outputs=(
            "annual fundamentals", "income statement detail", "cash flow statement detail", "balance sheet detail",
            "capital allocation history", "growth history",
        ),
        prerequisites=(KnowledgeDomain.COMPANY_PROFILE,),
        estimated_cost=AcquisitionCost.MEDIUM,
        estimated_freshness_days=90,
        priority=AcquisitionPriority.HIGH,
        execution_constraints=(ExecutionConstraint.REQUIRES_IDENTITY,),
    ),
    "sec_edgar_filings": ProviderCapability(
        provider_id="sec_edgar_filings",
        # (Capability Expansion Sprint 15) `GOVERNANCE` added alongside
        # `REGULATORY_FILINGS` -- this is the same provider call, the
        # same ingested `COMPANY_FILING` records; Governance
        # Intelligence's own on-demand extraction (`governance_
        # intelligence.py`) reads the 10-K/DEF 14A filings this
        # provider already fetches, never a separate acquisition step.
        # (Capability Expansion Sprint 17) `RISK_FACTORS` added the
        # identical way -- `risk_factor_intelligence.py` reads the
        # 10-K/10-Q filings this same provider call already fetches.
        # (Capability Expansion Sprint 18) `LEGAL_PROCEEDINGS` added the
        # identical way -- `legal_proceedings_intelligence.py` reads
        # the same 10-K/10-Q filings; no separate acquisition step.
        # (Capability Expansion Sprint 19) `OWNERSHIP` added the
        # identical way -- `ownership_intelligence.py` reads the same
        # DEF 14A filings this provider call already fetches.
        # (Capability Expansion Sprint 20) `EXECUTIVE_COMPENSATION`
        # added the identical way -- `executive_compensation_
        # intelligence.py` reads the same DEF 14A filings.
        supported_domains=(
            KnowledgeDomain.REGULATORY_FILINGS, KnowledgeDomain.GOVERNANCE, KnowledgeDomain.RISK_FACTORS,
            KnowledgeDomain.LEGAL_PROCEEDINGS, KnowledgeDomain.OWNERSHIP, KnowledgeDomain.EXECUTIVE_COMPENSATION,
        ),
        supported_source_kinds=(SourceKind.COMPANY_FILING,),
        expected_outputs=(
            "filing history", "governance-relevant filings", "risk-factor-relevant filings",
            "legal-proceedings-relevant filings", "ownership-relevant filings", "executive-compensation-relevant filings",
        ),
        prerequisites=(KnowledgeDomain.COMPANY_PROFILE,),
        estimated_cost=AcquisitionCost.MEDIUM,
        estimated_freshness_days=30,
        priority=AcquisitionPriority.NORMAL,
        execution_constraints=(ExecutionConstraint.REQUIRES_IDENTITY,),
    ),
}
"""Every provider `atlas.alpha.business_data_refresh.api.dependencies
.get_default_business_data_providers()` returns today has exactly one
entry here -- a future provider is adopted by adding one more entry,
never by touching the planner/dependency/orchestrator logic."""

DOMAIN_CRITICALITY: dict[KnowledgeDomain, DomainCriticality] = {
    KnowledgeDomain.FINANCIAL_HISTORY: DomainCriticality.CRITICAL,
    KnowledgeDomain.VALUATION: DomainCriticality.CRITICAL,
    KnowledgeDomain.CAPITAL_ALLOCATION: DomainCriticality.CRITICAL,
    KnowledgeDomain.GROWTH: DomainCriticality.CRITICAL,
    KnowledgeDomain.COMPANY_PROFILE: DomainCriticality.OPTIONAL,
    KnowledgeDomain.REGULATORY_FILINGS: DomainCriticality.OPTIONAL,
    KnowledgeDomain.GOVERNANCE: DomainCriticality.OPTIONAL,
    KnowledgeDomain.RISK_FACTORS: DomainCriticality.OPTIONAL,
    KnowledgeDomain.LEGAL_PROCEEDINGS: DomainCriticality.OPTIONAL,
    KnowledgeDomain.OWNERSHIP: DomainCriticality.OPTIONAL,
    KnowledgeDomain.EXECUTIVE_COMPENSATION: DomainCriticality.OPTIONAL,
    KnowledgeDomain.HISTORICAL_VALUATION: DomainCriticality.OPTIONAL,
    KnowledgeDomain.EARNINGS_CALL_ANALYSIS: DomainCriticality.OPTIONAL,
    KnowledgeDomain.PROFITABILITY: DomainCriticality.OPTIONAL,
    KnowledgeDomain.CASH_FLOW: DomainCriticality.OPTIONAL,
    KnowledgeDomain.BALANCE_SHEET: DomainCriticality.OPTIONAL,
}
"""A domain absent here (every one of the other 25 `KnowledgeDomain`
members) is never queried by the planner -- there is no registered
extractor for it yet, so asking about its criticality would be
meaningless. Mirrors `knowledge_coverage`'s own "absence is itself the
honest answer" discipline.

(Capability Expansion Sprint 6) `GROWTH` is `CRITICAL` -- its own two
underlying facts (`REVENUE`/`FREE_CASH_FLOW`) already were, and remain,
real `BusinessFactKind` members a real, already-running evaluator
(`atlas.analysis_engine.growth.evaluate_growth`) already reads --
confirmed by reading that evaluator's own source before this entry was
added, the same bar `FINANCIAL_HISTORY`/`VALUATION`/`CAPITAL_ALLOCATION`
are already held to. `growth_intelligence.py` itself introduces no new
`BusinessFactKind` -- it is a pure second-order transformation of
`financial_statement_intelligence`'s own already-covered data, exactly
like Sprint 5's own `FinancialQualityKnowledge` -- but unlike that
sprint, GROWTH's own two source facts are already read by a real
evaluator, so `CRITICAL` (not left unregistered the way Sprint 5 left
`knowledge_orchestration` completely untouched) is the honest answer.

(Capability Expansion Sprint 4) `CAPITAL_ALLOCATION` is `CRITICAL` --
unlike Sprint 3's three `OPTIONAL` domains below, its own seven raw
facts (`CAPITAL_EXPENDITURE`/`SHARE_BUYBACKS`/`SHARE_ISSUANCE`/
`DIVIDENDS`/`DEBT_ISSUANCE`/`DEBT_REPAYMENT`/`SHARES_OUTSTANDING`)
already were, and remain, real `BusinessFactKind` members a real,
already-running evaluator (`atlas.analysis_engine.capital_allocation
.evaluate_capital_allocation`) already reads -- confirmed by reading
that evaluator's own source before this entry was added, the same bar
`FINANCIAL_HISTORY`/`VALUATION` are already held to.

(Capability Expansion Sprint 3) `PROFITABILITY`/`CASH_FLOW`/`BALANCE_
SHEET` are `OPTIONAL` for the identical reason: every new field they
read (`gross_profit`/`ebitda`/`equity`/etc.) is deliberately kept out
of `BusinessFactKind` -- see `financial_statement_intelligence.py`'s
own module docstring -- so no `analysis_engine` evaluator reads any of
them. `FINANCIAL_HISTORY` itself is unaffected and stays `CRITICAL`.

(Capability Expansion Sprint 2) `EARNINGS_CALL_ANALYSIS` is `OPTIONAL`
for the identical reason: no `analysis_engine` evaluator reads it --
this sprint's own Phase 6 keeps the Decision Layer untouched by design.

(Capability Expansion Sprint 1) `HISTORICAL_VALUATION` is `OPTIONAL`:
`evaluate_fcf_yield_relative` still runs and returns a real, valid
`INSUFFICIENT_INPUT` finding without it -- the same bar `COMPANY_
PROFILE`/`REGULATORY_FILINGS` are already held to. Real, useful, and
consumed by that evaluator's own relative classification once present
-- but not strictly required for the evaluator to run at all."""


def capability_for(provider_id: str) -> ProviderCapability | None:
    return PROVIDER_CAPABILITIES.get(provider_id)


def criticality_of(domain: KnowledgeDomain) -> DomainCriticality | None:
    """`None` for a domain with no registered provider at all -- an
    honest "Atlas has no opinion," never defaulted to `OPTIONAL`."""
    return DOMAIN_CRITICALITY.get(domain)

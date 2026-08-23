"""The Decision-Critical Knowledge Model (Knowledge Strategy Engine,
Phases 1 + 2).

Answers a different question than `knowledge_coverage` or `knowledge_
orchestration` do: not "does Atlas have this knowledge" (Coverage) or
"can a provider fill this gap" (Orchestration's own Provider
Capability Registry), but "would having this knowledge actually change
the investment decision." A closed, categorical vocabulary -- never a
fabricated numeric score, the same discipline `DimensionCoverageLevel`/
`EvidenceFreshness`/`DomainCriticality` already establish.

Grounded, not guessed: `CRITICAL` is reserved for domains a real,
already-running evaluator depends on today (confirmed by reading the
same evaluator call graph `knowledge_orchestration.capability`'s own
`DOMAIN_CRITICALITY` was built from -- `atlas.analysis_engine.growth`/
`.capital_allocation`/`.valuation`/`.risk`). Every other tier is an
honest, explained judgment about a domain Atlas does not yet have a
wired extractor for -- `ImpactReasonCode.NOT_YET_CONSUMED_BY_ANY_
EVALUATOR` names that distinction explicitly rather than hiding it
behind a single number. Building this registry does not itself wire
any new extractor or provider -- `knowledge_coverage.engine._DOMAIN_
EXTRACTORS` still has exactly the same 4 entries it had before this
module existed (see that module's own docstring); a domain's presence
here is forward-declared metadata, exercised in practice only for the
handful of domains `knowledge_coverage` can currently ever report as a
gap. This is deliberate -- the explicit non-goal "must not maximize
Knowledge Coverage."
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from atlas.alpha.knowledge_coverage.models import KnowledgeDomain

__all__ = [
    "DecisionRelevance",
    "ImpactReasonCode",
    "DomainRelevance",
    "DOMAIN_RELEVANCE",
    "relevance_of",
    "reasons_for",
]


class DecisionRelevance(str, Enum):
    """Expected decision impact -- not completeness, not cost, not how
    easy a provider would be to run. A `LOW`-relevance domain can still
    be the very next thing `knowledge_orchestration` acquires, if it
    happens to be a hard technical prerequisite for a `CRITICAL` one
    (see `dependency.py`'s own docstring) -- Decision Relevance and
    Dependency Planning answer two different questions on purpose."""

    CRITICAL = "critical"
    """A real, already-running evaluator depends on this domain's own
    extracted facts to reach `canonical_analysis` -- without it, that
    evaluator (and everything downstream of its finding) cannot run at
    all."""
    HIGH = "high"
    """No evaluator consumes it yet, but it plausibly changes valuation,
    thesis, or recommendation confidence in a material way -- the kind
    of gap a professional investor would prioritize researching next."""
    MEDIUM = "medium"
    """A plausible, softer signal -- may refine risk assessment or
    thesis confidence at the margin, or substantially overlaps a domain
    Atlas already has real knowledge about."""
    LOW = "low"
    """Real, useful context -- but does not itself change any of
    valuation, thesis, portfolio fit, risk assessment, or recommendation
    confidence, today, in this build of Atlas."""
    IRRELEVANT = "irrelevant"
    """Not externally researchable at all -- the Case's own internal
    memory of its history, not a fact about the company."""


class ImpactReasonCode(str, Enum):
    """Closed, presence-only -- the same `MissingKnowledgeReason`/
    `PlanReasonCode` discipline: the presentation layer owns every
    sentence (Phase 4's own "Decision Impact Explanation"), this only
    names the real, structural fact behind a relevance assignment. A
    domain may carry more than one -- e.g. a domain can both directly
    feed a core evaluator AND materially change risk assessment."""

    DIRECTLY_FEEDS_CORE_EVALUATOR = "directly_feeds_core_evaluator"
    MAY_MATERIALLY_CHANGE_VALUATION = "may_materially_change_valuation"
    MAY_MATERIALLY_CHANGE_THESIS = "may_materially_change_thesis"
    MAY_MATERIALLY_CHANGE_PORTFOLIO_FIT = "may_materially_change_portfolio_fit"
    MAY_MATERIALLY_CHANGE_RISK_ASSESSMENT = "may_materially_change_risk_assessment"
    MAY_MATERIALLY_CHANGE_RECOMMENDATION_CONFIDENCE = "may_materially_change_recommendation_confidence"
    ALREADY_REPRESENTED_ELSEWHERE = "already_represented_elsewhere"
    """This domain's real decision-relevant substance is already
    captured under a different domain or a different existing engine's
    own output -- researching it separately would be redundant."""
    NOT_YET_CONSUMED_BY_ANY_EVALUATOR = "not_yet_consumed_by_any_evaluator"
    """Confirmed by reading the real evaluator call graph: no evaluator
    in this build of Atlas reads this domain's own facts today."""
    TECHNICAL_PREREQUISITE_ONLY = "technical_prerequisite_only"
    """Required for identity resolution or another structural precondition
    -- not because the information itself changes any conclusion."""
    CASE_INTERNAL_NOT_EXTERNALLY_RESEARCHABLE = "case_internal_not_externally_researchable"
    """This domain describes the Case's own investor-authored history,
    not a fact about the company -- no external provider could ever
    "research" it."""


@dataclass(frozen=True)
class DomainRelevance:
    relevance: DecisionRelevance
    reasons: tuple[ImpactReasonCode, ...]
    """Never empty -- every relevance assignment is explainable (Phase
    2's own requirement: "priority should always be explainable")."""


_FEEDS_EVALUATOR = ImpactReasonCode.DIRECTLY_FEEDS_CORE_EVALUATOR
_CHANGES_VALUATION = ImpactReasonCode.MAY_MATERIALLY_CHANGE_VALUATION
_CHANGES_THESIS = ImpactReasonCode.MAY_MATERIALLY_CHANGE_THESIS
_CHANGES_RISK = ImpactReasonCode.MAY_MATERIALLY_CHANGE_RISK_ASSESSMENT
_CHANGES_CONFIDENCE = ImpactReasonCode.MAY_MATERIALLY_CHANGE_RECOMMENDATION_CONFIDENCE
_REPRESENTED_ELSEWHERE = ImpactReasonCode.ALREADY_REPRESENTED_ELSEWHERE
_NOT_CONSUMED = ImpactReasonCode.NOT_YET_CONSUMED_BY_ANY_EVALUATOR
_PREREQUISITE_ONLY = ImpactReasonCode.TECHNICAL_PREREQUISITE_ONLY
_CASE_INTERNAL = ImpactReasonCode.CASE_INTERNAL_NOT_EXTERNALLY_RESEARCHABLE

_CRITICAL = DecisionRelevance.CRITICAL
_HIGH = DecisionRelevance.HIGH
_MEDIUM = DecisionRelevance.MEDIUM
_LOW = DecisionRelevance.LOW
_IRRELEVANT = DecisionRelevance.IRRELEVANT


DOMAIN_RELEVANCE: dict[KnowledgeDomain, DomainRelevance] = {
    # -- COMPANY_OVERVIEW -- descriptive; no evaluator reads any of these today.
    KnowledgeDomain.COMPANY_PROFILE: DomainRelevance(_LOW, (_PREREQUISITE_ONLY, _NOT_CONSUMED)),
    KnowledgeDomain.BUSINESS_MODEL: DomainRelevance(_LOW, (_NOT_CONSUMED,)),
    KnowledgeDomain.REVENUE_SEGMENTS: DomainRelevance(_MEDIUM, (_CHANGES_THESIS, _NOT_CONSUMED)),
    KnowledgeDomain.GEOGRAPHIC_EXPOSURE: DomainRelevance(_LOW, (_NOT_CONSUMED,)),
    KnowledgeDomain.INDUSTRY: DomainRelevance(_LOW, (_NOT_CONSUMED,)),
    KnowledgeDomain.COMPETITORS: DomainRelevance(_LOW, (_NOT_CONSUMED,)),
    KnowledgeDomain.COMPETITIVE_ADVANTAGES: DomainRelevance(_MEDIUM, (_CHANGES_THESIS, _NOT_CONSUMED)),
    # -- FINANCIALS -- GROWTH/CAPITAL_ALLOCATION directly match a real,
    # already-running evaluator (`growth.py`/`capital_allocation.py`);
    # the rest are real sub-slices of the same underlying facts, not
    # yet tracked as their own coverage domain.
    KnowledgeDomain.FINANCIAL_HISTORY: DomainRelevance(_CRITICAL, (_FEEDS_EVALUATOR, _CHANGES_VALUATION, _CHANGES_RISK)),
    KnowledgeDomain.GROWTH: DomainRelevance(_CRITICAL, (_FEEDS_EVALUATOR, _CHANGES_THESIS, _CHANGES_RISK)),
    KnowledgeDomain.PROFITABILITY: DomainRelevance(_HIGH, (_CHANGES_CONFIDENCE, _NOT_CONSUMED)),
    KnowledgeDomain.CASH_FLOW: DomainRelevance(_HIGH, (_CHANGES_VALUATION, _CHANGES_RISK)),
    KnowledgeDomain.BALANCE_SHEET: DomainRelevance(_MEDIUM, (_CHANGES_RISK, _NOT_CONSUMED)),
    KnowledgeDomain.CAPITAL_ALLOCATION: DomainRelevance(_CRITICAL, (_FEEDS_EVALUATOR, _CHANGES_THESIS, _CHANGES_RISK)),
    KnowledgeDomain.SHAREHOLDER_RETURNS: DomainRelevance(_MEDIUM, (_REPRESENTED_ELSEWHERE, _NOT_CONSUMED)),
    # -- GOVERNANCE_OWNERSHIP -- no evaluator models any of these today.
    KnowledgeDomain.MANAGEMENT: DomainRelevance(_MEDIUM, (_CHANGES_THESIS, _NOT_CONSUMED)),
    # (Capability Expansion Sprint 15) Board/committee/voting structure
    # is real, disclosed evidence a human analyst would read before
    # investing, but no evaluator consumes it -- the same tier as its
    # sibling `MANAGEMENT`, for the same reason.
    KnowledgeDomain.GOVERNANCE: DomainRelevance(_MEDIUM, (_CHANGES_THESIS, _NOT_CONSUMED)),
    # (Capability Expansion Sprint 20) Same tier and same reasoning as
    # its sibling `GOVERNANCE`/`MANAGEMENT` -- real, disclosed executive
    # compensation structure is evidence a human analyst would weigh
    # (incentive alignment, pay-for-performance design), but no
    # evaluator consumes it today.
    KnowledgeDomain.EXECUTIVE_COMPENSATION: DomainRelevance(_MEDIUM, (_CHANGES_THESIS, _NOT_CONSUMED)),
    KnowledgeDomain.OWNERSHIP: DomainRelevance(_LOW, (_NOT_CONSUMED,)),
    KnowledgeDomain.INSIDER_ACTIVITY: DomainRelevance(_LOW, (_NOT_CONSUMED,)),
    KnowledgeDomain.INSTITUTIONAL_OWNERSHIP: DomainRelevance(_LOW, (_NOT_CONSUMED,)),
    # -- VALUATION --
    KnowledgeDomain.VALUATION: DomainRelevance(_CRITICAL, (_FEEDS_EVALUATOR, _CHANGES_VALUATION, _CHANGES_RISK)),
    # (Capability Expansion Sprint 1) Now genuinely wired and genuinely
    # consumed -- `evaluate_fcf_yield_relative` already reads whatever
    # historical `MARKET_DATA_SNAPSHOT` observations exist to reach its
    # own UNDERVALUED/FAIRLY_VALUED/EXPENSIVE classification (confirmed
    # by reading `cash_flow.py`'s own source). Still `HIGH`, not
    # `CRITICAL`: that evaluator still runs and returns a valid finding
    # without it (see `knowledge_orchestration.capability.DOMAIN_
    # CRITICALITY`'s own docstring for the identical reasoning).
    KnowledgeDomain.HISTORICAL_VALUATION: DomainRelevance(_HIGH, (_FEEDS_EVALUATOR, _CHANGES_VALUATION)),
    KnowledgeDomain.ANALYST_EXPECTATIONS: DomainRelevance(_MEDIUM, (_CHANGES_CONFIDENCE, _NOT_CONSUMED)),
    # -- EVENTS_FILINGS --
    KnowledgeDomain.EARNINGS: DomainRelevance(_HIGH, (_CHANGES_VALUATION, _NOT_CONSUMED)),
    KnowledgeDomain.EARNINGS_CALL_ANALYSIS: DomainRelevance(_HIGH, (_CHANGES_THESIS, _CHANGES_CONFIDENCE, _NOT_CONSUMED)),
    KnowledgeDomain.REGULATORY_FILINGS: DomainRelevance(_MEDIUM, (_CHANGES_RISK, _NOT_CONSUMED)),
    KnowledgeDomain.IMPORTANT_NEWS: DomainRelevance(_MEDIUM, (_CHANGES_THESIS, _NOT_CONSUMED)),
    # -- MACRO_EXTERNAL_EXPOSURE -- thematic overlays; none feed an evaluator today.
    KnowledgeDomain.MACRO_EXPOSURE: DomainRelevance(_LOW, (_NOT_CONSUMED,)),
    KnowledgeDomain.GEOPOLITICAL_EXPOSURE: DomainRelevance(_LOW, (_NOT_CONSUMED,)),
    KnowledgeDomain.COMMODITY_EXPOSURE: DomainRelevance(_LOW, (_NOT_CONSUMED,)),
    KnowledgeDomain.CURRENCY_EXPOSURE: DomainRelevance(_LOW, (_NOT_CONSUMED,)),
    KnowledgeDomain.AI_EXPOSURE: DomainRelevance(_LOW, (_NOT_CONSUMED,)),
    # -- RISK_OPPORTUNITY -- largely already produced natively by the real Risk/Decision engines.
    KnowledgeDomain.RISK_FACTORS: DomainRelevance(_MEDIUM, (_REPRESENTED_ELSEWHERE, _CHANGES_RISK)),
    # (Capability Expansion Sprint 18) Same tier and same reasoning as
    # its sibling `RISK_FACTORS` -- a real, disclosed litigation/legal
    # proceeding is real evidence a human analyst would weigh, but
    # `atlas.analysis_engine.risk`'s own evaluators already produce a
    # categorical risk conclusion from structured data, independent of
    # this domain's own raw disclosure text.
    KnowledgeDomain.LEGAL_PROCEEDINGS: DomainRelevance(_MEDIUM, (_REPRESENTED_ELSEWHERE, _CHANGES_RISK)),
    KnowledgeDomain.OPPORTUNITIES: DomainRelevance(_LOW, (_REPRESENTED_ELSEWHERE,)),
    # -- CASE_MEMORY -- the Case's own history, not externally researchable at all.
    KnowledgeDomain.MONITORING_STATUS: DomainRelevance(_IRRELEVANT, (_CASE_INTERNAL,)),
    KnowledgeDomain.HISTORICAL_OBSERVATIONS: DomainRelevance(_IRRELEVANT, (_CASE_INTERNAL,)),
    KnowledgeDomain.EXISTING_EVIDENCE: DomainRelevance(_IRRELEVANT, (_CASE_INTERNAL,)),
    KnowledgeDomain.KNOWLEDGE_REFERENCES: DomainRelevance(_IRRELEVANT, (_CASE_INTERNAL,)),
}
"""Exhaustive: every one of the 36 `KnowledgeDomain` members has an
entry (asserted by this package's own test suite, the same
exhaustiveness discipline `knowledge_coverage.models.DOMAIN_GROUP`'s
own test already establishes)."""


def relevance_of(domain: KnowledgeDomain) -> DecisionRelevance:
    return DOMAIN_RELEVANCE[domain].relevance


def reasons_for(domain: KnowledgeDomain) -> tuple[ImpactReasonCode, ...]:
    return DOMAIN_RELEVANCE[domain].reasons

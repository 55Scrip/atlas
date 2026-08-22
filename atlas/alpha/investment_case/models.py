"""`InvestmentCaseComposition` (ATLAS-027, Phase 9) -- see this
package's own `__init__.py` for the full ownership rationale.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from atlas.alpha.investment_case.business_quality_intelligence import BusinessQualityKnowledge, extract_business_quality
from atlas.alpha.investment_case.capital_allocation_intelligence import CapitalAllocationHistory
from atlas.alpha.investment_case.company_profile import CompanyProfile
from atlas.alpha.investment_case.earnings_call import EarningsCallKnowledge
from atlas.alpha.investment_case.executive_change_intelligence import (
    ExecutiveChangeKnowledge,
    extract_executive_change_intelligence,
)
from atlas.alpha.investment_case.executive_track_record_intelligence import (
    ExecutiveTrackRecordKnowledge,
    extract_executive_track_record,
)
from atlas.alpha.investment_case.financial_history import FinancialPeriod, MarketSnapshot
from atlas.alpha.investment_case.financial_quality_intelligence import FinancialQualityKnowledge, extract_financial_quality
from atlas.alpha.investment_case.growth_intelligence import GrowthKnowledge, extract_growth_knowledge
from atlas.alpha.investment_case.financial_statement_intelligence import FinancialStatementHistory, SegmentInformation
from atlas.alpha.investment_case.historical_valuation import HistoricalValuationKnowledge
from atlas.alpha.investment_case.incentive_intelligence import IncentiveKnowledge, extract_incentive_intelligence
from atlas.alpha.investment_case.management_credibility_intelligence import (
    ManagementCredibilityKnowledge,
    extract_management_credibility,
)
from atlas.alpha.investment_case.management_guidance_intelligence import (
    ManagementGuidanceKnowledge,
    extract_management_guidance,
)
from atlas.alpha.investment_case.regulatory_filings import RegulatoryFiling
from atlas.alpha.portfolio.models import AlphaHolding, AlphaTradeLogEntry
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.investment_case_change import ChangeIntelligence
from atlas.analysis_engine.models import CanonicalAnalysis
from atlas.analysis_engine.valuation.facts import ValuationFact
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.observation.entity import Observation

__all__ = ["CurrentThesis", "InvestmentCaseComposition"]


@dataclass(frozen=True)
class CurrentThesis:
    """The investor's own most recent words, verbatim -- never
    interpreted, scored, or reworded. Mirrors
    `atlas.alpha.case_intelligence`'s own `CurrentThesis` shape (an
    independent, non-analytical derivation each Alpha service is
    expected to make for itself, not a canonical value with one owner
    the way Business/Valuation/Risk/Conviction are)."""

    latest_decision_reason: str | None
    latest_decision_type: str | None
    latest_observation_statement: str | None


@dataclass(frozen=True)
class InvestmentCaseComposition:
    """The canonical Investment Case view: one Case's own identity and
    record history, plus the exact `CanonicalAnalysis` object
    `atlas.analysis_engine.pipeline.assemble_analysis` produced for it.

    `canonical_analysis` already carries Business Analysis, Valuation,
    Risk, Confidence, Conviction, Recommendation, supporting/
    contradicting evidence, missing evidence, and open questions --
    none of those are duplicated as separate fields here. Only what
    `CanonicalAnalysis` does not and should not know about (the linked
    holding, the investor's own recorded history) is added.

    `outcome_history` is deliberately untyped (not `tuple[Outcome,
    ...]`): `atlas.alpha` is forbidden from importing
    `atlas.core.domain.outcome.entity` at all, the same restriction
    `pipeline_bridge.py`'s own `outcomes` parameter documents.
    """

    case_id: str
    holding_context: AlphaHolding | None
    canonical_analysis: CanonicalAnalysis
    current_thesis: CurrentThesis
    decision_history: tuple[Decision, ...]
    observation_history: tuple[Observation, ...]
    outcome_history: tuple
    trade_log: tuple[AlphaTradeLogEntry, ...]
    is_thesis_stale: bool
    """The exact value already passed into `calculate_conviction` for
    this Case (ATLAS-028) -- exposed here so a consumer wanting to
    display staleness (e.g. Portfolio Cockpit) reads it directly rather
    than recomputing the same `VERY_OLD_CASE_THRESHOLD_DAYS` rule a
    second time."""
    generated_at: datetime
    # Investment Case Engine v1 slice: placed after every pre-existing
    # field, each with a default, so every call site built before this
    # slice (test helpers included) keeps constructing a valid
    # `InvestmentCaseComposition` unchanged -- an intentional,
    # backward-compatible dataclass extension, not a reordering of
    # anything that came before it.
    company_profile: CompanyProfile | None = None
    """(Investment Case Engine v1 slice) `None` only when no
    `COMPANY_PROFILE` `BusinessRecord` has been ingested for this
    Case's own ticker yet -- an honest absence, not a placeholder."""
    financial_history: tuple[FinancialPeriod, ...] = ()
    """(Investment Case Engine v1 slice) Every ingested fiscal period's
    raw fundamentals, oldest first. Empty, never fabricated, when no
    `FINANCIAL_STATEMENT` record exists yet."""
    market_snapshot: MarketSnapshot | None = None
    """(Investment Case Engine v1 slice) The most recent current-market
    snapshot, or `None` if none has been ingested yet."""
    change_intelligence: ChangeIntelligence | None = None
    """(Investment Case Monitoring & Change Intelligence v1) `None`
    only when no snapshot repository was wired for this build (see
    `InvestmentCaseCompositionService.__init__`'s own docstring) -- an
    honest "capability unavailable," never a silently-empty "nothing
    changed." When a repository is wired, this is always a real
    `ChangeIntelligence`: either a baseline (`is_baseline=True`, the
    Case's first-ever recorded analysis) or a genuine comparison against
    the previously persisted structured state."""
    business_facts: tuple[BusinessFact, ...] = ()
    """(Product Sprint 14 -- Evidence & Explanation Quality) The same
    real `BusinessFact`s `canonical_analysis.business_analysis`/
    `.risk_analysis` findings were evaluated from -- re-derived once
    more here (a second, cheap, deterministic call to the exact same
    pure `extract_facts_from_records`; nothing recomputed, nothing
    reinterpreted) so `InvestmentCaseAnalysisView.from_domain` can
    resolve a finding's own `supporting_evidence`/`contradicting_evidence`
    reference ids back into the real fact they name, rather than
    serializing the opaque id. Empty only when `build`/`build_many`
    genuinely had no `BusinessRecord`s to extract from."""
    market_facts: tuple[ValuationFact, ...] = ()
    """(Product Sprint 14) The `ValuationFact` counterpart to
    `business_facts` above, for resolving a `ValuationFinding`'s own
    `supporting_facts`/`contradicting_facts` reference ids the same
    way."""
    regulatory_filings: tuple[RegulatoryFiling, ...] = ()
    """(Automatic Knowledge Ingestion Framework, Foundation Provider)
    Every ingested `COMPANY_FILING` record, newest first. Empty, never
    fabricated, when no such record has been ingested yet."""
    historical_valuation: HistoricalValuationKnowledge = field(default_factory=lambda: HistoricalValuationKnowledge(metrics=()))
    """(Capability Expansion Sprint 1: Historical Valuation Intelligence)
    Structured knowledge, never an opinion -- see `historical_valuation
    .py`'s own module docstring. `.metrics` is empty, never fabricated,
    until at least one `ValuationMetricKind` has a valid observation."""
    earnings_call: EarningsCallKnowledge = field(default_factory=lambda: EarningsCallKnowledge(transcripts=()))
    """(Capability Expansion Sprint 2: Earnings Call Intelligence)
    Structured management-communication knowledge -- see `earnings_call
    .py`'s own module docstring. `.transcripts` is empty, never
    fabricated, until at least one quarter's transcript is ingested."""
    financial_statement_intelligence: FinancialStatementHistory = field(
        default_factory=lambda: FinancialStatementHistory(
            income_statements=(), balance_sheets=(), cash_flow_statements=(), segments=SegmentInformation()
        )
    )
    """(Capability Expansion Sprint 3: Financial Statement Intelligence)
    Structured Income Statement/Balance Sheet/Cash Flow Statement
    knowledge -- see `financial_statement_intelligence.py`'s own module
    docstring. Every tuple is empty, never fabricated, until at least
    one `FINANCIAL_STATEMENT` record has been ingested."""
    capital_allocation_intelligence: CapitalAllocationHistory = field(
        default_factory=lambda: CapitalAllocationHistory(periods=())
    )
    """(Capability Expansion Sprint 4: Capital Allocation Intelligence)
    Structured, multi-year knowledge describing how management has
    deployed shareholder capital -- see `capital_allocation_intelligence
    .py`'s own module docstring. `.periods` is empty, never fabricated,
    until at least one `FINANCIAL_STATEMENT` record has been ingested."""
    financial_quality_intelligence: FinancialQualityKnowledge = field(
        default_factory=lambda: extract_financial_quality(
            FinancialStatementHistory(income_statements=(), balance_sheets=(), cash_flow_statements=(), segments=SegmentInformation())
        )
    )
    """(Capability Expansion Sprint 5: Financial Quality Intelligence)
    A pure, second-order transformation of `financial_statement_
    intelligence`'s own already-covered data -- see `financial_quality
    _intelligence.py`'s own module docstring. The default is produced
    by calling the real extraction function with an empty history,
    never a hand-written duplicate of its own honest "insufficient
    data" shape."""
    growth_intelligence: GrowthKnowledge = field(
        default_factory=lambda: extract_growth_knowledge(
            FinancialStatementHistory(income_statements=(), balance_sheets=(), cash_flow_statements=(), segments=SegmentInformation())
        )
    )
    """(Capability Expansion Sprint 6: Growth Intelligence) Structured
    knowledge describing the nature, consistency and durability of
    growth -- see `growth_intelligence.py`'s own module docstring. The
    default is produced by calling the real extraction function with
    an empty history, never a hand-written duplicate of its own honest
    "insufficient data" shape."""
    business_quality_intelligence: BusinessQualityKnowledge = field(
        default_factory=lambda: extract_business_quality(
            FinancialStatementHistory(income_statements=(), balance_sheets=(), cash_flow_statements=(), segments=SegmentInformation()),
            CapitalAllocationHistory(periods=()),
            extract_financial_quality(
                FinancialStatementHistory(income_statements=(), balance_sheets=(), cash_flow_statements=(), segments=SegmentInformation())
            ),
            extract_growth_knowledge(
                FinancialStatementHistory(income_statements=(), balance_sheets=(), cash_flow_statements=(), segments=SegmentInformation())
            ),
        )
    )
    """(Capability Expansion Sprint 7: Business Quality Intelligence) A
    pure, higher-order aggregation over Financial Statement/Capital
    Allocation/Financial Quality/Growth Intelligence's own already-
    computed outputs -- see `business_quality_intelligence.py`'s own
    module docstring. The default is produced by calling the real
    extraction function with every sibling at its own empty default,
    never a hand-written duplicate of its own honest "insufficient
    data" shape."""
    management_credibility_intelligence: ManagementCredibilityKnowledge = field(
        default_factory=lambda: extract_management_credibility(
            EarningsCallKnowledge(transcripts=()),
            FinancialStatementHistory(income_statements=(), balance_sheets=(), cash_flow_statements=(), segments=SegmentInformation()),
            extract_growth_knowledge(
                FinancialStatementHistory(income_statements=(), balance_sheets=(), cash_flow_statements=(), segments=SegmentInformation())
            ),
            CapitalAllocationHistory(periods=()),
        )
    )
    """(Capability Expansion Sprint 8: Management Credibility
    Intelligence) A pure, higher-order aggregation over Earnings Call/
    Financial Statement/Growth/Capital Allocation Intelligence's own
    already-computed outputs -- see `management_credibility_
    intelligence.py`'s own module docstring. The default is produced by
    calling the real extraction function with every sibling at its own
    empty default, never a hand-written duplicate of its own honest
    "insufficient" shape."""
    management_guidance_intelligence: ManagementGuidanceKnowledge = field(
        default_factory=lambda: extract_management_guidance(
            EarningsCallKnowledge(transcripts=()),
            FinancialStatementHistory(income_statements=(), balance_sheets=(), cash_flow_statements=(), segments=SegmentInformation()),
            extract_growth_knowledge(
                FinancialStatementHistory(income_statements=(), balance_sheets=(), cash_flow_statements=(), segments=SegmentInformation())
            ),
            CapitalAllocationHistory(periods=()),
        )
    )
    """(Capability Expansion Sprint 9: Management Guidance Intelligence)
    A pure, higher-order aggregation over Earnings Call/Financial
    Statement/Growth Intelligence's own already-computed outputs -- see
    `management_guidance_intelligence.py`'s own module docstring. The
    default is produced by calling the real extraction function with
    every sibling at its own empty default, never a hand-written
    duplicate of its own honest "insufficient" shape."""
    executive_change_intelligence: ExecutiveChangeKnowledge = field(
        default_factory=lambda: extract_executive_change_intelligence(None, EarningsCallKnowledge(transcripts=()))
    )
    """(Capability Expansion Sprint 10: Executive Change Intelligence) A
    pure, higher-order aggregation over Earnings Call Intelligence's own
    already-classified speaker/title metadata -- see `executive_change_
    intelligence.py`'s own module docstring. The default is produced by
    calling the real extraction function with an empty transcript
    history, never a hand-written duplicate of its own honest
    "insufficient" shape."""
    executive_track_record_intelligence: ExecutiveTrackRecordKnowledge = field(
        default_factory=lambda: extract_executive_track_record(
            extract_executive_change_intelligence(None, EarningsCallKnowledge(transcripts=())),
            FinancialStatementHistory(income_statements=(), balance_sheets=(), cash_flow_statements=(), segments=SegmentInformation()),
            EarningsCallKnowledge(transcripts=()),
            CapitalAllocationHistory(periods=()),
            extract_growth_knowledge(
                FinancialStatementHistory(income_statements=(), balance_sheets=(), cash_flow_statements=(), segments=SegmentInformation())
            ),
            extract_management_credibility(
                EarningsCallKnowledge(transcripts=()),
                FinancialStatementHistory(income_statements=(), balance_sheets=(), cash_flow_statements=(), segments=SegmentInformation()),
                extract_growth_knowledge(
                    FinancialStatementHistory(income_statements=(), balance_sheets=(), cash_flow_statements=(), segments=SegmentInformation())
                ),
                CapitalAllocationHistory(periods=()),
            ),
            extract_management_guidance(
                EarningsCallKnowledge(transcripts=()),
                FinancialStatementHistory(income_statements=(), balance_sheets=(), cash_flow_statements=(), segments=SegmentInformation()),
                extract_growth_knowledge(
                    FinancialStatementHistory(income_statements=(), balance_sheets=(), cash_flow_statements=(), segments=SegmentInformation())
                ),
                CapitalAllocationHistory(periods=()),
            ),
        )
    )
    """(Capability Expansion Sprint 11: Executive Track Record
    Intelligence) A pure, higher-order aggregation over Executive
    Change/Management Guidance/Management Credibility Intelligence's
    own already-computed outputs -- see `executive_track_record_
    intelligence.py`'s own module docstring. The default is produced by
    calling the real extraction function with every sibling at its own
    empty default, never a hand-written duplicate of its own honest
    "insufficient" shape."""
    incentive_intelligence: IncentiveKnowledge = field(default_factory=lambda: extract_incentive_intelligence(()))
    """(Capability Expansion Sprint 12: Incentive Intelligence) A pure
    re-labeling of `RegulatoryFiling`'s own `DEF 14A` records -- see
    `incentive_intelligence.py`'s own module docstring for why every
    other field is always empty in this build. The default is produced
    by calling the real extraction function with an empty filing
    history, never a hand-written duplicate of its own honest
    "unavailable" shape."""

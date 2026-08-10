"""`InvestmentCaseComposition` (ATLAS-027, Phase 9) -- see this
package's own `__init__.py` for the full ownership rationale.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.alpha.investment_case.company_profile import CompanyProfile
from atlas.alpha.investment_case.financial_history import FinancialPeriod, MarketSnapshot
from atlas.alpha.portfolio.models import AlphaHolding, AlphaTradeLogEntry
from atlas.analysis_engine.investment_case_change import ChangeIntelligence
from atlas.analysis_engine.models import CanonicalAnalysis
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

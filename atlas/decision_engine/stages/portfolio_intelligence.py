"""Portfolio Intelligence stage (`DE-003`; Sprint 4).

Real, deterministic evaluator for exactly one dimension:
`HoldingContextFinding`, built entirely from
`DecisionEngineInput.portfolio_holding` (a single optional holding —
never a full portfolio) and `DecisionEngineInput.trade_log`. Every
field is reported verbatim; this module never labels a weight "high,"
"low," "overweight," or "concentrated," and never infers risk,
diversification, suitability, or portfolio quality from it.

`DE-003`'s seven substantive factors (Allocation, Concentration,
Diversification, Correlation, Opportunity Cost, Existing Thesis,
Previous Decisions) are always `INSUFFICIENT_INPUT`
(`PortfolioFinding`) — Sprint 4's own repository-discovery finding,
confirmed and locked by the sprint's own scope: `DecisionEngineInput`
carries no sibling-holdings, sector/country/market-cap, correlation, or
cross-Case data, so none of the seven factors — every one of them
portfolio-wide or cross-Case by its own doctrine definition — can be
honestly computed from a single optional holding. This module never
synthesizes a one-holding "portfolio" to force a computation, and never
imports `atlas.alpha` or `atlas.capabilities.portfolio_intelligence`.
"""
from __future__ import annotations

from atlas.decision_engine.contracts import (
    DecisionEngineInput,
    EvaluationState,
    HoldingContextFinding,
    HoldingLinkage,
    PortfolioDataNotAvailableReason,
    PortfolioDoctrineFactor,
    PortfolioFinding,
    PortfolioIntelligenceResult,
)

_PORTFOLIO_FINDING = PortfolioFinding(
    state=EvaluationState.INSUFFICIENT_INPUT,
    reason=PortfolioDataNotAvailableReason.NO_PORTFOLIO_WIDE_DATA_IN_INPUT,
    factors=tuple(PortfolioDoctrineFactor),
)


def _holding_context(engine_input: DecisionEngineInput) -> HoldingContextFinding:
    holding = engine_input.portfolio_holding
    trade_log = engine_input.trade_log

    if trade_log:
        transaction_types = tuple(sorted({entry.transaction_type for entry in trade_log}))
        timestamps = tuple(entry.executed_at for entry in trade_log)
        earliest_executed_at = min(timestamps)
        latest_executed_at = max(timestamps)
    else:
        transaction_types = ()
        earliest_executed_at = None
        latest_executed_at = None

    if holding is None:
        return HoldingContextFinding(
            linkage=HoldingLinkage.ABSENT,
            trade_count=len(trade_log),
            transaction_types=transaction_types,
            earliest_executed_at=earliest_executed_at,
            latest_executed_at=latest_executed_at,
        )
    return HoldingContextFinding(
        linkage=HoldingLinkage.PRESENT,
        ticker=holding.ticker,
        weight_percent=holding.weight_percent,
        value_absolute=holding.value_absolute,
        reconciliation_status=holding.reconciliation_status,
        trade_count=len(trade_log),
        transaction_types=transaction_types,
        earliest_executed_at=earliest_executed_at,
        latest_executed_at=latest_executed_at,
    )


def evaluate_portfolio_intelligence(
    engine_input: DecisionEngineInput,
) -> PortfolioIntelligenceResult:
    """Deterministic: identical `engine_input` always produces a deeply
    equal result. `min()`/`max()`/`sorted()` do not depend on
    `trade_log`'s original ordering. No timestamp, randomness, UUID
    generation, wall-clock access, global state, or side effect."""
    return PortfolioIntelligenceResult(
        state=EvaluationState.EVALUATED,
        holding_context=_holding_context(engine_input),
        portfolio_factors=_PORTFOLIO_FINDING,
    )

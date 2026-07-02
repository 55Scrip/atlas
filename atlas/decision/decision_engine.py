from atlas.analysis.comparison import ComparisonEngine, ComparisonResult
from atlas.analysis.engine import AtlasInvestmentEngine, InvestmentReport
from atlas.analysis.memory import MemoryComparison, MemoryEngine
from atlas.analysis.portfolio import PortfolioAnalysis, PortfolioIntelligenceEngine
from atlas.analysis.scores import clamp_score
from atlas.capabilities.watchlist_intelligence import WatchlistIntelligenceEngine
from atlas.capabilities.watchlist_intelligence.models import (
    WatchlistIntelligenceInput,
    WatchlistIntelligenceReport,
    WatchlistItem as IntelligenceWatchlistItem,
)
from atlas.decision.decision_context import DecisionContext
from atlas.decision.decision_result import DecisionAction, DecisionResult
from atlas.providers.base import CompanyDataProvider


class AtlasDecisionEngine:
    def __init__(
        self,
        investment_engine: AtlasInvestmentEngine | None = None,
        portfolio_engine: PortfolioIntelligenceEngine | None = None,
        comparison_engine: ComparisonEngine | None = None,
        memory_engine: MemoryEngine | None = None,
    ) -> None:
        self.investment_engine = investment_engine or AtlasInvestmentEngine()
        self.portfolio_engine = portfolio_engine or PortfolioIntelligenceEngine()
        self.comparison_engine = comparison_engine or ComparisonEngine(self.investment_engine)
        self.memory_engine = memory_engine or MemoryEngine()

    def decide(
        self,
        ticker: str,
        provider: CompanyDataProvider,
        context: DecisionContext,
    ) -> DecisionResult:
        normalized_ticker = ticker.upper()
        investment_report = self.investment_engine.analyze_ticker(normalized_ticker, provider)
        portfolio_analysis = self._analyze_portfolio(normalized_ticker, provider, context)
        comparison_result = self._compare(normalized_ticker, provider, context)
        watchlist_analysis = self._watchlist_intelligence(context)
        memory_comparison = self._compare_memory(normalized_ticker, context)

        capital_safe = _capital_is_safe(context)
        has_enough_information = _has_enough_information(context)
        portfolio_fit = _portfolio_fit(portfolio_analysis)
        capital_allocation_quality = _capital_allocation_quality(
            context=context,
            report=investment_report,
            portfolio_analysis=portfolio_analysis,
            capital_safe=capital_safe,
            has_enough_information=has_enough_information,
        )
        decision_quality = _decision_quality(
            report=investment_report,
            portfolio_fit=portfolio_fit,
            capital_allocation_quality=capital_allocation_quality,
            has_enough_information=has_enough_information,
        )
        confidence = _confidence(
            report=investment_report,
            decision_quality=decision_quality,
            has_enough_information=has_enough_information,
            portfolio_analysis=portfolio_analysis,
            comparison_result=comparison_result,
            watchlist_analysis=watchlist_analysis,
            memory_comparison=memory_comparison,
        )
        action = _decide_action(
            report=investment_report,
            context=context,
            portfolio_analysis=portfolio_analysis,
            capital_safe=capital_safe,
            has_enough_information=has_enough_information,
        )

        return DecisionResult(
            ticker=normalized_ticker,
            action=action,
            has_enough_information=has_enough_information,
            decision_quality=decision_quality,
            portfolio_fit=portfolio_fit,
            capital_allocation_quality=capital_allocation_quality,
            confidence=confidence,
            reasoning=_reasoning(
                ticker=normalized_ticker,
                action=action,
                report=investment_report,
                context=context,
                portfolio_analysis=portfolio_analysis,
                comparison_result=comparison_result,
                watchlist_intelligence=watchlist_analysis,
                memory_comparison=memory_comparison,
                capital_safe=capital_safe,
                has_enough_information=has_enough_information,
            ),
            next_best_action=_next_best_action(action, context, capital_safe),
            what_could_change_my_mind=_what_could_change_my_mind(action, investment_report),
            uncertainty=_uncertainty(
                context=context,
                portfolio_analysis=portfolio_analysis,
                comparison_result=comparison_result,
                memory_comparison=memory_comparison,
                has_enough_information=has_enough_information,
            ),
            investment_report=investment_report,
            portfolio_analysis=portfolio_analysis,
            comparison_result=comparison_result,
            watchlist_intelligence=watchlist_analysis,
            memory_comparison=memory_comparison,
        )

    def _analyze_portfolio(
        self,
        ticker: str,
        provider: CompanyDataProvider,
        context: DecisionContext,
    ) -> PortfolioAnalysis | None:
        if context.portfolio is None:
            return None
        return self.portfolio_engine.analyze_ticker(
            portfolio=context.portfolio,
            ticker=ticker,
            provider=provider,
        )

    def _compare(
        self,
        ticker: str,
        provider: CompanyDataProvider,
        context: DecisionContext,
    ) -> ComparisonResult | None:
        tickers = _comparison_tickers(ticker, context)
        if len(tickers) < 2:
            return None
        return self.comparison_engine.compare_tickers(tickers, provider)

    def _watchlist_intelligence(
        self,
        context: DecisionContext,
    ) -> WatchlistIntelligenceReport | None:
        if context.watchlist is None:
            return None
        intelligence_input = WatchlistIntelligenceInput(
            name=context.watchlist.name,
            items=tuple(
                IntelligenceWatchlistItem(id=item.ticker.lower(), ticker=item.ticker)
                for item in context.watchlist.items
            ),
        )
        return WatchlistIntelligenceEngine().analyze(intelligence_input)

    def _compare_memory(
        self,
        ticker: str,
        context: DecisionContext,
    ) -> MemoryComparison | None:
        if context.historical_memory is None:
            return None
        try:
            return self.memory_engine.compare(context.historical_memory, ticker)
        except ValueError:
            return None


def _has_enough_information(context: DecisionContext) -> bool:
    return (
        bool(context.investment_horizon.strip())
        and bool(context.risk_profile.strip())
        and context.available_capital is not None
        and _normalized(context.cash_reserve_status) not in {"", "unknown", "unclear"}
    )


def _capital_is_safe(context: DecisionContext) -> bool:
    if context.available_capital is None or context.available_capital <= 0:
        return False
    horizon = _normalized(context.investment_horizon)
    cash_status = _normalized(context.cash_reserve_status)
    unsafe_cash = {
        "needed",
        "insufficient",
        "low",
        "short term needed",
        "short-term needed",
        "not enough",
        "below target",
    }
    if "short" in horizon or "near" in horizon:
        return False
    return cash_status not in unsafe_cash and cash_status != "unknown"


def _capital_is_explicitly_unsafe(context: DecisionContext) -> bool:
    horizon = _normalized(context.investment_horizon)
    cash_status = _normalized(context.cash_reserve_status)
    unsafe_cash = {
        "needed",
        "insufficient",
        "low",
        "short term needed",
        "short-term needed",
        "not enough",
        "below target",
    }
    no_available_capital = (
        context.available_capital is not None and context.available_capital <= 0
    )
    return (
        no_available_capital
        or "short" in horizon
        or "near" in horizon
        or cash_status in unsafe_cash
    )


def _portfolio_fit(portfolio_analysis: PortfolioAnalysis | None) -> int:
    if portfolio_analysis is None:
        return 50
    return clamp_score(portfolio_analysis.portfolio_score)


def _capital_allocation_quality(
    context: DecisionContext,
    report: InvestmentReport,
    portfolio_analysis: PortfolioAnalysis | None,
    capital_safe: bool,
    has_enough_information: bool,
) -> int:
    if not capital_safe:
        return 20
    base = round(
        (report.risk.score * 0.35)
        + (report.confidence * 0.30)
        + (report.atlas_score * 0.35)
    )
    if portfolio_analysis is not None:
        base = round((base * 0.65) + (portfolio_analysis.portfolio_score * 0.35))
    if "conservative" in _normalized(context.risk_profile) and report.risk.score < 70:
        base -= 12
    if not has_enough_information:
        base -= 15
    return clamp_score(base)


def _decision_quality(
    report: InvestmentReport,
    portfolio_fit: int,
    capital_allocation_quality: int,
    has_enough_information: bool,
) -> int:
    score = round(
        (report.atlas_score * 0.35)
        + (report.confidence * 0.25)
        + (portfolio_fit * 0.20)
        + (capital_allocation_quality * 0.20)
    )
    if not has_enough_information:
        score -= 15
    return clamp_score(score)


def _confidence(
    report: InvestmentReport,
    decision_quality: int,
    has_enough_information: bool,
    portfolio_analysis: PortfolioAnalysis | None,
    comparison_result: ComparisonResult | None,
    watchlist_analysis: WatchlistIntelligenceReport | None,
    memory_comparison: MemoryComparison | None,
) -> int:
    context_bonus = sum(
        4
        for item in (
            portfolio_analysis,
            comparison_result,
            watchlist_analysis,
            memory_comparison,
        )
        if item is not None
    )
    score = round((report.confidence * 0.60) + (decision_quality * 0.40)) + context_bonus
    if not has_enough_information:
        score -= 18
    return clamp_score(score)


def _decide_action(
    report: InvestmentReport,
    context: DecisionContext,
    portfolio_analysis: PortfolioAnalysis | None,
    capital_safe: bool,
    has_enough_information: bool,
) -> DecisionAction:
    if not capital_safe and _capital_is_explicitly_unsafe(context):
        return DecisionAction.AVOID
    if not has_enough_information:
        return DecisionAction.LEARN_MORE
    if _owns_ticker(context, report.company) and report.atlas_score < 60:
        return DecisionAction.REDUCE
    if portfolio_analysis is not None:
        if portfolio_analysis.recommendation.value in {"Avoid", "Reduce"}:
            return DecisionAction.WATCH if report.atlas_score >= 75 else DecisionAction.AVOID
        if portfolio_analysis.portfolio_score < 55:
            return DecisionAction.WATCH
    if report.atlas_score >= 80 and report.risk.score >= 65:
        return DecisionAction.BUY
    if report.atlas_score >= 65:
        return DecisionAction.HOLD
    if report.atlas_score >= 55:
        return DecisionAction.WATCH
    return DecisionAction.AVOID


def _reasoning(
    ticker: str,
    action: DecisionAction,
    report: InvestmentReport,
    context: DecisionContext,
    portfolio_analysis: PortfolioAnalysis | None,
    comparison_result: ComparisonResult | None,
    watchlist_intelligence: WatchlistIntelligenceReport | None,
    memory_comparison: MemoryComparison | None,
    capital_safe: bool,
    has_enough_information: bool,
) -> str:
    reasons = [
        (
            f"Atlas selects {action.value} for {ticker} with an Atlas Score of "
            f"{report.atlas_score}/100, recommendation {report.overall_recommendation}, "
            f"and confidence {report.confidence}/100."
        )
    ]
    if not capital_safe:
        reasons.append(
            "Capital safety blocks a buy decision because the context does not show investable "
            "capital that can remain invested beyond near-term needs."
        )
    if not has_enough_information:
        reasons.append(
            "Information quality is incomplete because investment horizon, risk profile, "
            "available capital, or cash reserve status is missing or unclear."
        )
    if portfolio_analysis is not None:
        reasons.append(
            f"Portfolio fit is {portfolio_analysis.portfolio_score}/100. "
            f"{portfolio_analysis.final_reasoning}"
        )
        reasons.append(_concentration_discussion(portfolio_analysis))
    else:
        reasons.append(
            "No portfolio was supplied, so Atlas cannot fully measure concentration, overlap, "
            "or position-level fit."
        )
    if comparison_result is not None:
        reasons.append(
            f"Comparison context says {comparison_result.best_overall.winner.ticker} is best "
            f"overall. {comparison_result.best_overall.reasoning}"
        )
    if watchlist_intelligence is not None:
        first_ticker = (
            watchlist_intelligence.companies_needing_attention[0].ticker
            if watchlist_intelligence.companies_needing_attention
            else watchlist_intelligence.observations[0].ticker
            if watchlist_intelligence.observations
            else "the watchlist"
        )
        reasons.append(
            f"Watchlist context highlights {first_ticker}. "
            f"{watchlist_intelligence.overview}"
        )
    if memory_comparison is not None:
        reasons.append(memory_comparison.explanation)
    reasons.append(
        "This is deterministic research reasoning, not personal financial advice or a guarantee."
    )
    return " ".join(reasons)


def _next_best_action(
    action: DecisionAction,
    context: DecisionContext,
    capital_safe: bool,
) -> str:
    if not capital_safe:
        return (
            "Keep short-term liquidity separate, confirm the cash reserve is adequate, "
            "and revisit only with capital that can remain invested."
        )
    if action == DecisionAction.LEARN_MORE:
        return "Fill the missing context before allocating capital."
    if action == DecisionAction.BUY:
        return "Consider a measured position size that preserves diversification and liquidity."
    if action == DecisionAction.HOLD:
        return "Maintain the current stance and monitor thesis, valuation, and portfolio fit."
    if action == DecisionAction.REDUCE:
        return (
            "Review position size and consider reducing exposure if concentration or thesis "
            "risk is high."
        )
    if action == DecisionAction.WATCH:
        return "Wait for stronger evidence, a better valuation, or improved portfolio fit."
    return "Avoid allocating new capital until the risk-reward and capital safety profile improve."


def _what_could_change_my_mind(action: DecisionAction, report: InvestmentReport) -> str:
    if action in {DecisionAction.AVOID, DecisionAction.WATCH, DecisionAction.LEARN_MORE}:
        return (
            "A stronger valuation setup, better risk profile, clearer data, improved "
            "portfolio fit, and adequate investable capital could improve the decision."
        )
    return (
        "Deteriorating quality, weaker growth, lower confidence, higher valuation risk, "
        "or worse portfolio concentration could move Atlas away from this decision."
    )


def _uncertainty(
    context: DecisionContext,
    portfolio_analysis: PortfolioAnalysis | None,
    comparison_result: ComparisonResult | None,
    memory_comparison: MemoryComparison | None,
    has_enough_information: bool,
) -> str:
    uncertainties: list[str] = []
    if not has_enough_information:
        uncertainties.append("capital and investor-context inputs are incomplete")
    if portfolio_analysis is None:
        uncertainties.append("portfolio concentration and overlap are not fully measured")
    if comparison_result is None:
        uncertainties.append("opportunity cost versus alternatives is limited")
    if context.watchlist is None:
        uncertainties.append("watchlist context is absent")
    if memory_comparison is None:
        uncertainties.append("historical decision trend is unavailable")
    if not uncertainties:
        return "Atlas has multiple context signals, but outcomes remain uncertain."
    return "Atlas uncertainty includes: " + "; ".join(uncertainties) + "."


def _comparison_tickers(ticker: str, context: DecisionContext) -> tuple[str, ...]:
    tickers = [ticker.upper()]
    if context.watchlist is not None:
        tickers.extend(item.ticker for item in context.watchlist.items)
    tickers.extend(context.comparison_tickers)
    deduped: list[str] = []
    for item in tickers:
        normalized = item.upper()
        if normalized not in deduped:
            deduped.append(normalized)
    return tuple(deduped)


def _concentration_discussion(portfolio_analysis: PortfolioAnalysis) -> str:
    return (
        "Concentration risk is explicit: "
        f"sector concentration {portfolio_analysis.sector_concentration.score}/100, "
        f"country concentration {portfolio_analysis.country_concentration.score}/100, "
        f"market cap concentration {portfolio_analysis.market_cap_concentration.score}/100, "
        f"and overlap {portfolio_analysis.overlap_with_existing_holdings.score}/100."
    )


def _owns_ticker(context: DecisionContext, company_label: str) -> bool:
    if context.portfolio is None:
        return False
    return any(position.ticker in company_label for position in context.portfolio.positions)


def _normalized(value: str) -> str:
    return value.strip().lower().replace("_", " ")

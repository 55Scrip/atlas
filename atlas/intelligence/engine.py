from dataclasses import dataclass

from atlas.analysis.engine import AtlasInvestmentEngine, InvestmentReport
from atlas.analysis.portfolio import Portfolio, PortfolioAnalysis, PortfolioIntelligenceEngine
from atlas.analysis.watchlist import Watchlist
from atlas.capabilities.watchlist_intelligence import WatchlistIntelligenceEngine
from atlas.capabilities.watchlist_intelligence.models import (
    WatchlistIntelligenceInput,
    WatchlistIntelligenceReport,
    WatchlistItem as IntelligenceWatchlistItem,
)
from atlas.decision import AtlasDecisionEngine, DecisionContext, DecisionResult
from atlas.market import (
    MarketHealthEngine,
    MarketHealthReport,
    MarketIndicators,
    MarketRegimeAnalysis,
    MarketRegimeEngine,
    MarketSnapshot,
)
from atlas.providers import CompanyDataProvider
from atlas.risk import RiskAnalysis
from atlas.themes import ThemeAnalysis, ThemeEngine, ThemeInput


@dataclass(frozen=True)
class IntelligenceContext:
    portfolio: Portfolio | None = None
    watchlist: Watchlist | None = None
    theme: str = "AI infrastructure"
    market_snapshot: MarketSnapshot | None = None
    market_health_report: MarketHealthReport | None = None
    risk_analysis: RiskAnalysis | None = None
    investment_horizon: str = "long term"
    risk_profile: str = "balanced"
    available_capital: float | None = None
    cash_reserve_status: str = "unknown"


@dataclass(frozen=True)
class IntelligenceInput:
    ticker: str
    provider: CompanyDataProvider
    context: IntelligenceContext = IntelligenceContext()


@dataclass(frozen=True)
class IntelligenceReport:
    ticker: str
    company: str
    confidence: int
    executive_summary: str
    structural_tailwinds: tuple[str, ...]
    current_market_environment: tuple[str, ...]
    company_positioning: tuple[str, ...]
    portfolio_impact: tuple[str, ...]
    risk_assessment: tuple[str, ...]
    atlas_conclusion: str
    monitoring_items: tuple[str, ...]
    what_could_change_view: tuple[str, ...]
    investment_report: InvestmentReport
    portfolio_analysis: PortfolioAnalysis | None
    watchlist_intelligence: WatchlistIntelligenceReport | None
    risk_analysis: RiskAnalysis | None
    decision_result: DecisionResult
    theme_analysis: ThemeAnalysis
    market_regime_analysis: MarketRegimeAnalysis
    market_health_report: MarketHealthReport


class IntelligenceEngine:
    def __init__(
        self,
        investment_engine: AtlasInvestmentEngine | None = None,
        portfolio_engine: PortfolioIntelligenceEngine | None = None,
        decision_engine: AtlasDecisionEngine | None = None,
        theme_engine: ThemeEngine | None = None,
        market_regime_engine: MarketRegimeEngine | None = None,
        market_health_engine: MarketHealthEngine | None = None,
    ) -> None:
        self.investment_engine = investment_engine or AtlasInvestmentEngine()
        self.portfolio_engine = portfolio_engine or PortfolioIntelligenceEngine()
        self.decision_engine = decision_engine or AtlasDecisionEngine(
            investment_engine=self.investment_engine,
            portfolio_engine=self.portfolio_engine,
        )
        self.theme_engine = theme_engine or ThemeEngine()
        self.market_regime_engine = market_regime_engine or MarketRegimeEngine()
        self.market_health_engine = market_health_engine or MarketHealthEngine()

    def analyze(self, intelligence_input: IntelligenceInput) -> IntelligenceReport:
        ticker = intelligence_input.ticker.upper()
        provider = intelligence_input.provider
        context = intelligence_input.context

        investment_report = self.investment_engine.analyze_ticker(ticker, provider)
        portfolio_analysis = _optional_portfolio_analysis(
            engine=self.portfolio_engine,
            portfolio=context.portfolio,
            ticker=ticker,
            provider=provider,
        )
        watchlist_analysis = _optional_watchlist_intelligence(context.watchlist)
        market_regime = self.market_regime_engine.analyze(
            context.market_snapshot or _default_market_snapshot()
        )
        market_health = context.market_health_report or self.market_health_engine.analyze()
        theme_analysis = self.theme_engine.analyze(ThemeInput(theme=context.theme))
        decision_result = self.decision_engine.decide(
            ticker=ticker,
            provider=provider,
            context=DecisionContext(
                market_regime=market_regime.regime.value,
                portfolio=context.portfolio,
                watchlist=context.watchlist,
                investment_horizon=context.investment_horizon,
                risk_profile=context.risk_profile,
                available_capital=context.available_capital,
                cash_reserve_status=context.cash_reserve_status,
            ),
        )
        confidence = _confidence(
            investment_report=investment_report,
            decision_result=decision_result,
            theme_analysis=theme_analysis,
            market_regime=market_regime,
            market_health=market_health,
            portfolio_analysis=portfolio_analysis,
            watchlist_intelligence=watchlist_analysis,
            risk_analysis=context.risk_analysis,
        )

        return IntelligenceReport(
            ticker=ticker,
            company=investment_report.company,
            confidence=confidence,
            executive_summary=_executive_summary(
                ticker=ticker,
                report=investment_report,
                decision_result=decision_result,
                market_regime=market_regime,
                market_health=market_health,
            ),
            structural_tailwinds=_structural_tailwinds(theme_analysis),
            current_market_environment=_current_market_environment(
                market_regime,
                market_health,
            ),
            company_positioning=_company_positioning(investment_report),
            portfolio_impact=_portfolio_impact(portfolio_analysis),
            risk_assessment=_risk_assessment(
                report=investment_report,
                theme_analysis=theme_analysis,
                market_regime=market_regime,
                market_health=market_health,
                risk_analysis=context.risk_analysis,
            ),
            atlas_conclusion=_atlas_conclusion(
                report=investment_report,
                decision_result=decision_result,
                market_health=market_health,
                portfolio_analysis=portfolio_analysis,
            ),
            monitoring_items=_monitoring_items(
                theme_analysis=theme_analysis,
                market_regime=market_regime,
                market_health=market_health,
                portfolio_analysis=portfolio_analysis,
                risk_analysis=context.risk_analysis,
            ),
            what_could_change_view=_what_could_change_view(
                theme_analysis=theme_analysis,
                market_health=market_health,
                decision_result=decision_result,
            ),
            investment_report=investment_report,
            portfolio_analysis=portfolio_analysis,
            watchlist_intelligence=watchlist_analysis,
            risk_analysis=context.risk_analysis,
            decision_result=decision_result,
            theme_analysis=theme_analysis,
            market_regime_analysis=market_regime,
            market_health_report=market_health,
        )


def render_intelligence_report(report: IntelligenceReport) -> str:
    lines = [
        "Atlas Intelligence Report",
        "",
        f"Company: {report.company}",
        f"Ticker: {report.ticker}",
        f"Confidence: {report.confidence}/100",
        "",
        "Executive Summary",
        report.executive_summary,
        "",
        "Structural Tailwinds",
        *_render_list(report.structural_tailwinds),
        "",
        "Current Market Environment",
        *_render_list(report.current_market_environment),
        "",
        "Company Positioning",
        *_render_list(report.company_positioning),
        "",
        "Portfolio Impact",
        *_render_list(report.portfolio_impact),
        "",
        "Risk Assessment",
        *_render_list(report.risk_assessment),
        "",
        "Atlas Conclusion",
        report.atlas_conclusion,
        "",
        "What Atlas Is Monitoring",
        *_render_list(report.monitoring_items),
        "",
        "What Could Change Atlas' View",
        *_render_list(report.what_could_change_view),
        "",
        "Research Framing",
        "This deterministic synthesis is market context, not personalized financial advice.",
    ]
    return "\n".join(lines)


def _optional_portfolio_analysis(
    engine: PortfolioIntelligenceEngine,
    portfolio: Portfolio | None,
    ticker: str,
    provider: CompanyDataProvider,
) -> PortfolioAnalysis | None:
    if portfolio is None:
        return None
    return engine.analyze_ticker(portfolio=portfolio, ticker=ticker, provider=provider)


def _optional_watchlist_intelligence(
    watchlist: Watchlist | None,
) -> WatchlistIntelligenceReport | None:
    if watchlist is None:
        return None
    intelligence_input = WatchlistIntelligenceInput(
        name=watchlist.name,
        items=tuple(
            IntelligenceWatchlistItem(id=item.ticker.lower(), ticker=item.ticker)
            for item in watchlist.items
        ),
    )
    return WatchlistIntelligenceEngine().analyze(intelligence_input)


def _default_market_snapshot() -> MarketSnapshot:
    return MarketSnapshot(
        indicators=MarketIndicators(
            sp500_drawdown=-0.04,
            nasdaq_drawdown=-0.07,
            vix=19,
            interest_rate_trend="stable",
            inflation_trend="stable",
        ),
        source="deterministic-placeholder",
    )


def _confidence(
    investment_report: InvestmentReport,
    decision_result: DecisionResult,
    theme_analysis: ThemeAnalysis,
    market_regime: MarketRegimeAnalysis,
    market_health: MarketHealthReport,
    portfolio_analysis: PortfolioAnalysis | None,
    watchlist_intelligence: WatchlistIntelligenceReport | None,
    risk_analysis: RiskAnalysis | None,
) -> int:
    base = round(
        investment_report.confidence * 0.35
        + decision_result.confidence * 0.25
        + theme_analysis.confidence * 0.15
        + market_regime.confidence * 0.10
        + market_health.overall_score * 0.15
    )
    context_bonus = sum(
        3
        for item in (portfolio_analysis, watchlist_intelligence, risk_analysis)
        if item is not None
    )
    return min(100, max(0, base + context_bonus))


def _executive_summary(
    ticker: str,
    report: InvestmentReport,
    decision_result: DecisionResult,
    market_regime: MarketRegimeAnalysis,
    market_health: MarketHealthReport,
) -> str:
    return (
        f"Atlas views {ticker} through a company score of {report.atlas_score}/100, "
        f"company confidence of {report.confidence}/100, decision quality of "
        f"{decision_result.decision_quality}/100, a {market_regime.regime.value} "
        f"market regime, and {market_health.overall_market_health.lower()} market "
        "health. The conclusion is expressed as reasoning and uncertainty rather "
        "than a trading instruction."
    )


def _structural_tailwinds(theme_analysis: ThemeAnalysis) -> tuple[str, ...]:
    beneficiaries = ", ".join(
        beneficiary.name for beneficiary in theme_analysis.potential_beneficiaries[:4]
    )
    opportunities = ", ".join(theme_analysis.second_order_winners[:4])
    return (
        f"Positive long-term theme: {theme_analysis.summary}",
        f"Industries benefiting: {', '.join(theme_analysis.affected_industries)}.",
        f"Potential beneficiaries to research: {beneficiaries}.",
        f"Structural opportunities: {opportunities}.",
    )


def _current_market_environment(
    market_regime: MarketRegimeAnalysis,
    market_health: MarketHealthReport,
) -> tuple[str, ...]:
    weakest_group = min(market_health.signal_groups, key=lambda group: group.score)
    return (
        f"Market Regime summary: {market_regime.summary}",
        (
            "Market Health summary: "
            f"{market_health.overall_market_health} health, "
            f"{market_health.overall_risk_level.lower()} risk, "
            f"and {market_health.overall_score}/100 overall score."
        ),
        f"Key current market risk: weakest signal group is {weakest_group.name}.",
        market_health.atlas_view,
    )


def _company_positioning(report: InvestmentReport) -> tuple[str, ...]:
    return (
        f"Strengths: quality {report.quality.score}/100; {report.quality.reasoning}",
        f"Weaknesses: risk profile {report.risk.score}/100; {report.risk.reasoning}",
        f"Quality context: financial strength {report.financial_strength.score}/100.",
        f"Valuation context: valuation {report.valuation.score}/100; {report.valuation.reasoning}",
        f"Growth context: growth {report.growth.score}/100; {report.growth.reasoning}",
    )


def _portfolio_impact(portfolio_analysis: PortfolioAnalysis | None) -> tuple[str, ...]:
    if portfolio_analysis is None:
        return (
            "Diversification: no portfolio was supplied, so fit is not fully measured.",
            "Concentration: sector, country, and market-cap concentration are unknown.",
            "Overlap: existing holding overlap is unknown without portfolio context.",
        )
    return (
        f"Diversification: {portfolio_analysis.diversification_impact.reasoning}",
        f"Concentration: {portfolio_analysis.sector_concentration.reasoning}",
        f"Country exposure: {portfolio_analysis.country_concentration.reasoning}",
        f"Market-cap exposure: {portfolio_analysis.market_cap_concentration.reasoning}",
        f"Overlap: {portfolio_analysis.overlap_with_existing_holdings.reasoning}",
        (
            "Portfolio quality impact: "
            f"{portfolio_analysis.expected_portfolio_quality_impact.reasoning}"
        ),
        f"Portfolio risk impact: {portfolio_analysis.expected_portfolio_risk_impact.reasoning}",
    )


def _risk_assessment(
    report: InvestmentReport,
    theme_analysis: ThemeAnalysis,
    market_regime: MarketRegimeAnalysis,
    market_health: MarketHealthReport,
    risk_analysis: RiskAnalysis | None,
) -> tuple[str, ...]:
    theme_risks = "; ".join(
        f"{risk.name}: {risk.why_it_matters}" for risk in theme_analysis.key_risks[:3]
    )
    macro_risks = "; ".join(market_regime.risks[:3])
    health_risks = "; ".join(market_health.what_could_change_view[:3])
    items = [
        f"Company risks: risk score {report.risk.score}/100; {report.risk.reasoning}",
        f"Macro risks: {macro_risks}",
        f"Market health risks: {health_risks}",
        f"Theme risks: {theme_risks}",
    ]
    if risk_analysis is None:
        items.append("Position sizing risk: no explicit risk sizing input was supplied.")
    else:
        items.extend(
            [
                f"Liquidity risk: {risk_analysis.position_sizing.liquidity_warning}",
                f"Concentration risk: {risk_analysis.position_sizing.concentration_warning}",
                (
                    "Capital deployment context: "
                    f"{risk_analysis.deployment_plan.market_regime_adjustment}"
                ),
            ]
        )
    return tuple(items)


def _atlas_conclusion(
    report: InvestmentReport,
    decision_result: DecisionResult,
    market_health: MarketHealthReport,
    portfolio_analysis: PortfolioAnalysis | None,
) -> str:
    portfolio_sentence = (
        f"Portfolio fit is measured at {portfolio_analysis.portfolio_score}/100."
        if portfolio_analysis is not None
        else "Portfolio fit remains uncertain because no portfolio was supplied."
    )
    return (
        f"Atlas' synthesis is constructive but conditional: company score "
        f"{report.atlas_score}/100, confidence {decision_result.confidence}/100, "
        f"market health {market_health.overall_score}/100. {portfolio_sentence} "
        "Atlas would keep monitoring thesis durability, market stress, valuation, "
        "and capital safety before translating research into any action."
    )


def _monitoring_items(
    theme_analysis: ThemeAnalysis,
    market_regime: MarketRegimeAnalysis,
    market_health: MarketHealthReport,
    portfolio_analysis: PortfolioAnalysis | None,
    risk_analysis: RiskAnalysis | None,
) -> tuple[str, ...]:
    items = [
        *theme_analysis.monitoring_items[:4],
        *market_regime.key_indicators,
        *market_health.signal_groups[0].monitoring_items[:2],
    ]
    if portfolio_analysis is not None:
        items.append(portfolio_analysis.overlap_with_existing_holdings.reasoning)
    if risk_analysis is not None:
        items.append(risk_analysis.position_sizing.cash_reserve_status)
    return tuple(items)


def _what_could_change_view(
    theme_analysis: ThemeAnalysis,
    market_health: MarketHealthReport,
    decision_result: DecisionResult,
) -> tuple[str, ...]:
    return (
        *theme_analysis.what_would_change_view[:3],
        *market_health.what_could_change_view[:3],
        decision_result.uncertainty,
    )


def _render_list(items: tuple[str, ...]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]

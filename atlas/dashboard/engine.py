from dataclasses import dataclass

from atlas.analysis.portfolio import Portfolio, PortfolioIntelligenceEngine
from atlas.economics import EconomicSignalAnalysis, EconomicSignalsEngine
from atlas.market import (
    MarketHealthEngine,
    MarketHealthReport,
    MarketIndicators,
    MarketRegimeAnalysis,
    MarketRegimeEngine,
    MarketSnapshot,
)
from atlas.monitoring import MonitoringEngine
from atlas.principles import PrinciplesCheck, PrinciplesEngine
from atlas.profile import InvestorProfile, InvestorProfileEngine
from atlas.providers import CompanyDataProvider
from atlas.risk_drift import RiskDriftEngine, RiskDriftInput
from atlas.suitability import SuitabilityEngine, SuitabilityInput
from atlas.themes import ThemeAnalysis, ThemeEngine, ThemeInput


@dataclass(frozen=True)
class DashboardInput:
    investor_profile: InvestorProfile | None = None
    portfolio: Portfolio | None = None
    provider: CompanyDataProvider | None = None
    target_ticker: str | None = None
    theme_names: tuple[str, ...] = (
        "AI infrastructure",
        "Semiconductors",
        "Energy transition",
    )
    market_snapshot: MarketSnapshot | None = None


@dataclass(frozen=True)
class DashboardCard:
    title: str
    value: str
    detail: str
    status: str = "Info"


@dataclass(frozen=True)
class DashboardSection:
    title: str
    cards: tuple[DashboardCard, ...]
    narrative: str


@dataclass(frozen=True)
class DashboardSummary:
    title: str
    greeting: str
    sections: tuple[DashboardSection, ...]
    todays_observations: tuple[str, ...]
    monitoring_items: tuple[str, ...]
    suggested_questions: tuple[str, ...]
    principles_check: PrinciplesCheck


class DashboardEngine:
    def __init__(
        self,
        profile_engine: InvestorProfileEngine | None = None,
        portfolio_engine: PortfolioIntelligenceEngine | None = None,
        suitability_engine: SuitabilityEngine | None = None,
        risk_drift_engine: RiskDriftEngine | None = None,
        theme_engine: ThemeEngine | None = None,
        market_health_engine: MarketHealthEngine | None = None,
        market_regime_engine: MarketRegimeEngine | None = None,
        economic_signals_engine: EconomicSignalsEngine | None = None,
        monitoring_engine: MonitoringEngine | None = None,
        principles_engine: PrinciplesEngine | None = None,
    ) -> None:
        self.profile_engine = profile_engine or InvestorProfileEngine()
        self.portfolio_engine = portfolio_engine or PortfolioIntelligenceEngine()
        self.suitability_engine = suitability_engine or SuitabilityEngine()
        self.risk_drift_engine = risk_drift_engine or RiskDriftEngine()
        self.theme_engine = theme_engine or ThemeEngine()
        self.market_health_engine = market_health_engine or MarketHealthEngine()
        self.market_regime_engine = market_regime_engine or MarketRegimeEngine()
        self.economic_signals_engine = economic_signals_engine or EconomicSignalsEngine()
        self.monitoring_engine = monitoring_engine or MonitoringEngine()
        self.principles_engine = principles_engine or PrinciplesEngine()

    def build(self, dashboard_input: DashboardInput | None = None) -> DashboardSummary:
        input_data = dashboard_input or DashboardInput()
        profile = input_data.investor_profile or self.profile_engine.create_default_profile()
        context = self.profile_engine.investor_context(profile)
        market_regime = self.market_regime_engine.analyze(
            input_data.market_snapshot or _default_market_snapshot()
        )
        market_health = self.market_health_engine.analyze()
        economic_signals = self.economic_signals_engine.analyze()
        theme_analyses = tuple(
            self.theme_engine.analyze(ThemeInput(theme=name))
            for name in input_data.theme_names[:3]
        )
        portfolio_section = self._portfolio_section(
            profile=profile,
            portfolio=input_data.portfolio,
            market_regime=market_regime,
            market_health=market_health,
            economic_signals=economic_signals,
            provider=input_data.provider,
            target_ticker=input_data.target_ticker,
        )
        sections = (
            _welcome_section(profile, context),
            portfolio_section,
            _market_section(market_regime, market_health, economic_signals),
            _themes_section(theme_analyses),
        )
        observations = _observations(
            portfolio_section=portfolio_section,
            market_regime=market_regime,
            market_health=market_health,
            economic_signals=economic_signals,
            theme_analyses=theme_analyses,
        )
        monitoring_items = _monitoring_items(
            portfolio=input_data.portfolio,
            market_health=market_health,
            economic_signals=economic_signals,
            theme_analyses=theme_analyses,
        )
        questions = _suggested_questions(input_data.portfolio)
        draft = _dashboard_text_without_principles(
            title="Atlas Home Dashboard",
            greeting=_greeting(profile, context),
            sections=sections,
            observations=observations,
            monitoring_items=monitoring_items,
            suggested_questions=questions,
        )
        principles_check = self.principles_engine.check(draft)
        return DashboardSummary(
            title="Atlas Home Dashboard",
            greeting=_greeting(profile, context),
            sections=sections,
            todays_observations=observations,
            monitoring_items=monitoring_items,
            suggested_questions=questions,
            principles_check=principles_check,
        )

    def _portfolio_section(
        self,
        profile: InvestorProfile,
        portfolio: Portfolio | None,
        market_regime: MarketRegimeAnalysis,
        market_health: MarketHealthReport,
        economic_signals: EconomicSignalAnalysis,
        provider: CompanyDataProvider | None,
        target_ticker: str | None,
    ) -> DashboardSection:
        if portfolio is None:
            suitability = self.suitability_engine.assess(
                SuitabilityInput(investor_profile=profile)
            )
            drift = self.risk_drift_engine.assess(
                RiskDriftInput(
                    original_profile=profile,
                    current_profile=profile,
                    current_market_regime=market_regime,
                    current_market_health=market_health,
                    current_economic_signals=economic_signals,
                )
            )
            return DashboardSection(
                title="Portfolio Overview",
                cards=(
                    DashboardCard(
                        "Portfolio Health",
                        "No portfolio loaded",
                        "Atlas can provide a richer briefing when portfolio context exists.",
                        "Missing Context",
                    ),
                    DashboardCard(
                        "Suitability",
                        suitability.overall_suitability.value,
                        "Suitability is limited without current holdings.",
                        "Review",
                    ),
                    DashboardCard(
                        "Risk Drift",
                        drift.overall_drift_level.value,
                        drift.drift_summary,
                        "Appears stable",
                    ),
                ),
                narrative=(
                    "Portfolio context is not loaded, so Atlas is using investor profile "
                    "and market context only."
                ),
            )

        snapshot = self.monitoring_engine.snapshot_portfolio(portfolio)
        suitability = self.suitability_engine.assess(
            SuitabilityInput(investor_profile=profile, portfolio=portfolio)
        )
        drift = self.risk_drift_engine.assess(
            RiskDriftInput(
                original_profile=profile,
                current_profile=profile,
                current_portfolio=portfolio,
                current_market_regime=market_regime,
                current_market_health=market_health,
                current_economic_signals=economic_signals,
                current_suitability_assessment=suitability,
            )
        )
        largest = max(portfolio.positions, key=lambda position: position.weight)
        concentration = _concentration_level(largest.weight)
        cards = [
            DashboardCard(
                "Portfolio Health",
                f"{snapshot.importance_score}/100",
                snapshot.summary,
                _score_status(snapshot.importance_score),
            ),
            DashboardCard(
                "Suitability",
                suitability.overall_suitability.value,
                _first_or_default(
                    suitability.why_it_fits,
                    "Atlas is evaluating portfolio compatibility with the profile.",
                ),
                "Context",
            ),
            DashboardCard(
                "Risk Drift",
                drift.overall_drift_level.value,
                drift.drift_summary,
                "Review" if drift.overall_drift_level.value != "None" else "Appears stable",
            ),
            DashboardCard(
                "Largest Position",
                f"{largest.ticker} at {largest.weight:.1%}",
                "Atlas is monitoring single-position dependency.",
                _concentration_status(largest.weight),
            ),
            DashboardCard(
                "Concentration Level",
                concentration,
                "Concentration is based on the largest current position.",
                _concentration_status(largest.weight),
            ),
        ]
        if target_ticker and provider:
            portfolio_analysis = self.portfolio_engine.analyze_ticker(
                portfolio=portfolio,
                ticker=target_ticker,
                provider=provider,
            )
            cards.append(
                DashboardCard(
                    "Target Portfolio Fit",
                    f"{portfolio_analysis.portfolio_score}/100",
                    portfolio_analysis.final_reasoning,
                    _score_status(portfolio_analysis.portfolio_score),
                )
            )
        return DashboardSection(
            title="Portfolio Overview",
            cards=tuple(cards),
            narrative=(
                "Atlas reviewed portfolio health, profile compatibility, drift, and "
                "concentration before presenting market context."
            ),
        )


def render_dashboard(summary: DashboardSummary) -> str:
    return _dashboard_text_without_principles(
        title=summary.title,
        greeting=summary.greeting,
        sections=summary.sections,
        observations=summary.todays_observations,
        monitoring_items=summary.monitoring_items,
        suggested_questions=summary.suggested_questions,
    )


def _dashboard_text_without_principles(
    title: str,
    greeting: str,
    sections: tuple[DashboardSection, ...],
    observations: tuple[str, ...],
    monitoring_items: tuple[str, ...],
    suggested_questions: tuple[str, ...],
) -> str:
    lines = [title, "", greeting]
    for section in sections:
        lines.extend(["", section.title, section.narrative])
        for card in section.cards:
            lines.append(f"- {card.title}: {card.value} ({card.status})")
            lines.append(f"  {card.detail}")
    lines.extend(["", "Today's Observations", *_render_list(observations)])
    lines.extend(["", "Atlas Is Monitoring", *_render_list(monitoring_items)])
    lines.extend(["", "Suggested Questions", *_render_list(suggested_questions)])
    lines.extend(
        [
            "",
            "Research Framing",
            (
                "This dashboard is a deterministic briefing for context and education. "
                "It does not provide personalized financial advice."
            ),
        ]
    )
    return "\n".join(lines)


def _welcome_section(profile, context) -> DashboardSection:
    objective = ", ".join(context.investment_goals)
    return DashboardSection(
        title="Welcome",
        cards=(
            DashboardCard(
                "Investor",
                profile.name,
                "Atlas starts from the investor profile before reviewing markets.",
                "Context",
            ),
            DashboardCard(
                "Current Objective",
                objective,
                f"Portfolio purpose: {context.portfolio_purpose}.",
                "Context",
            ),
        ),
        narrative="Atlas has prepared a profile-first briefing for today's review.",
    )


def _market_section(
    regime: MarketRegimeAnalysis,
    health: MarketHealthReport,
    economics: EconomicSignalAnalysis,
) -> DashboardSection:
    return DashboardSection(
        title="Market Overview",
        cards=(
            DashboardCard(
                "Market Regime",
                regime.regime.value,
                regime.summary,
                "Context",
            ),
            DashboardCard(
                "Market Health",
                health.overall_market_health,
                health.atlas_view,
                health.overall_risk_level,
            ),
            DashboardCard(
                "Economic Signals",
                economics.overall_economic_health,
                economics.conclusion,
                f"Risk score {economics.overall_risk_score}/100",
            ),
        ),
        narrative="Atlas reviewed market regime, health, and economic context together.",
    )


def _themes_section(theme_analyses: tuple[ThemeAnalysis, ...]) -> DashboardSection:
    cards = tuple(
        DashboardCard(
            title=analysis.theme.value,
            value="Worth monitoring",
            detail=_theme_detail(analysis),
            status=f"Confidence {analysis.confidence}/100",
        )
        for analysis in theme_analyses
    )
    return DashboardSection(
        title="Themes To Watch",
        cards=cards,
        narrative="Atlas is monitoring structural themes without treating them as trade ideas.",
    )


def _observations(
    portfolio_section: DashboardSection,
    market_regime: MarketRegimeAnalysis,
    market_health: MarketHealthReport,
    economic_signals: EconomicSignalAnalysis,
    theme_analyses: tuple[ThemeAnalysis, ...],
) -> tuple[str, ...]:
    observations = [
        f"Market regime appears {market_regime.regime.value.lower()}.",
        (
            f"Market health is {market_health.overall_market_health.lower()} with "
            f"{market_health.overall_risk_level.lower()} risk."
        ),
        (
            f"Economic signals are {economic_signals.overall_economic_health.lower()} "
            f"with risk score {economic_signals.overall_risk_score}/100."
        ),
        f"{theme_analyses[0].theme.value} remains worth monitoring.",
    ]
    concentration_card = _find_card(portfolio_section, "Concentration Level")
    if concentration_card:
        observations.append(f"Portfolio concentration appears {concentration_card.value.lower()}.")
    else:
        observations.append("Portfolio context is not loaded yet.")
    return tuple(observations[:5])


def _monitoring_items(
    portfolio: Portfolio | None,
    market_health: MarketHealthReport,
    economic_signals: EconomicSignalAnalysis,
    theme_analyses: tuple[ThemeAnalysis, ...],
) -> tuple[str, ...]:
    items = [
        "Power infrastructure",
        "Interest rates",
        "Credit spreads",
        theme_analyses[0].theme.value,
        "Semiconductor supply chain",
    ]
    items.extend(group.monitoring_items[0] for group in market_health.signal_groups[:2])
    items.extend(economic_signals.watching_most_closely[:2])
    if portfolio is not None:
        items.append("Largest position concentration")
    return tuple(dict.fromkeys(items))[:8]


def _suggested_questions(portfolio: Portfolio | None) -> tuple[str, ...]:
    questions = [
        "Has anything important changed?",
        "What risks am I underestimating?",
        "What themes deserve attention?",
        "Has my risk profile drifted?",
    ]
    if portfolio is not None:
        questions.insert(1, "Is my portfolio still aligned with my goals?")
    else:
        questions.insert(1, "What portfolio context should Atlas review first?")
    return tuple(questions)


def _default_market_snapshot() -> MarketSnapshot:
    return MarketSnapshot(
        indicators=MarketIndicators(
            sp500_drawdown=-0.04,
            nasdaq_drawdown=-0.07,
            vix=19,
            interest_rate_trend="stable",
            inflation_trend="stable",
        ),
        source="deterministic-dashboard-placeholder",
    )


def _greeting(profile: InvestorProfile, context) -> str:
    objective = ", ".join(context.investment_goals)
    return (
        f"Good day, {profile.name}. Atlas is focused on {objective} within a "
        f"{context.portfolio_purpose} context."
    )


def _theme_detail(analysis: ThemeAnalysis) -> str:
    bottlenecks = ", ".join(item.name for item in analysis.key_bottlenecks[:3])
    return f"Key bottlenecks: {bottlenecks}."


def _score_status(score: int) -> str:
    if score >= 75:
        return "Appears stable"
    if score >= 55:
        return "Worth monitoring"
    return "May deserve attention"


def _concentration_level(weight: float) -> str:
    if weight >= 0.40:
        return "High"
    if weight >= 0.25:
        return "Moderate"
    return "Low"


def _concentration_status(weight: float) -> str:
    if weight >= 0.40:
        return "May deserve attention"
    if weight >= 0.25:
        return "Worth monitoring"
    return "Appears stable"


def _first_or_default(items: tuple[str, ...], default: str) -> str:
    return items[0] if items else default


def _find_card(section: DashboardSection, title: str) -> DashboardCard | None:
    for card in section.cards:
        if card.title == title:
            return card
    return None


def _render_list(items: tuple[str, ...]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]

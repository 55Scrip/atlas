from dataclasses import dataclass

from atlas.analysis.portfolio import Portfolio
from atlas.dashboard import DashboardEngine, DashboardInput, DashboardSummary
from atlas.economics import EconomicSignalAnalysis, EconomicSignalsEngine
from atlas.market import (
    MarketHealthEngine,
    MarketHealthReport,
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
class DailyBriefInput:
    investor_profile: InvestorProfile | None = None
    portfolio: Portfolio | None = None
    provider: CompanyDataProvider | None = None
    target_ticker: str | None = None
    theme_names: tuple[str, ...] = (
        "AI infrastructure",
        "Semiconductors",
        "Energy transition",
        "Healthcare innovation",
    )
    market_snapshot: MarketSnapshot | None = None
    previous_dashboard: DashboardSummary | None = None


@dataclass(frozen=True)
class DailyBriefItem:
    title: str
    summary: str
    status: str = "Context"


@dataclass(frozen=True)
class DailyBriefSection:
    title: str
    items: tuple[DailyBriefItem, ...]
    narrative: str


@dataclass(frozen=True)
class DailyBriefSummary:
    title: str
    opening_summary: str
    sections: tuple[DailyBriefSection, ...]
    suggested_questions: tuple[str, ...]
    principles_check: PrinciplesCheck


class DailyBriefEngine:
    def __init__(
        self,
        dashboard_engine: DashboardEngine | None = None,
        profile_engine: InvestorProfileEngine | None = None,
        suitability_engine: SuitabilityEngine | None = None,
        risk_drift_engine: RiskDriftEngine | None = None,
        theme_engine: ThemeEngine | None = None,
        market_health_engine: MarketHealthEngine | None = None,
        market_regime_engine: MarketRegimeEngine | None = None,
        economic_signals_engine: EconomicSignalsEngine | None = None,
        monitoring_engine: MonitoringEngine | None = None,
        principles_engine: PrinciplesEngine | None = None,
    ) -> None:
        self.dashboard_engine = dashboard_engine or DashboardEngine()
        self.profile_engine = profile_engine or InvestorProfileEngine()
        self.suitability_engine = suitability_engine or SuitabilityEngine()
        self.risk_drift_engine = risk_drift_engine or RiskDriftEngine()
        self.theme_engine = theme_engine or ThemeEngine()
        self.market_health_engine = market_health_engine or MarketHealthEngine()
        self.market_regime_engine = market_regime_engine or MarketRegimeEngine()
        self.economic_signals_engine = economic_signals_engine or EconomicSignalsEngine()
        self.monitoring_engine = monitoring_engine or MonitoringEngine()
        self.principles_engine = principles_engine or PrinciplesEngine()

    def build(self, daily_input: DailyBriefInput | None = None) -> DailyBriefSummary:
        input_data = daily_input or DailyBriefInput()
        profile = input_data.investor_profile or self.profile_engine.create_default_profile()
        dashboard = self.dashboard_engine.build(
            DashboardInput(
                investor_profile=profile,
                portfolio=input_data.portfolio,
                provider=input_data.provider,
                target_ticker=input_data.target_ticker,
                theme_names=input_data.theme_names[:3],
                market_snapshot=input_data.market_snapshot,
            )
        )
        market_regime = self.market_regime_engine.analyze(
            input_data.market_snapshot or _dashboard_default_market_snapshot()
        )
        market_health = self.market_health_engine.analyze()
        economic_signals = self.economic_signals_engine.analyze()
        theme_analyses = tuple(
            self.theme_engine.analyze(ThemeInput(theme=name))
            for name in input_data.theme_names[:4]
        )
        suitability = self.suitability_engine.assess(
            SuitabilityInput(investor_profile=profile, portfolio=input_data.portfolio)
        )
        risk_drift = self.risk_drift_engine.assess(
            RiskDriftInput(
                original_profile=profile,
                current_profile=profile,
                current_portfolio=input_data.portfolio,
                current_market_regime=market_regime,
                current_market_health=market_health,
                current_economic_signals=economic_signals,
                current_suitability_assessment=suitability,
            )
        )
        sections = (
            _what_changed_section(dashboard, input_data.previous_dashboard, risk_drift),
            _portfolio_notes_section(dashboard, suitability, risk_drift),
            _market_notes_section(market_regime, market_health, economic_signals),
            _themes_section(theme_analyses),
            _risks_section(market_health, economic_signals, theme_analyses, risk_drift),
            _opportunities_section(theme_analyses, market_health),
        )
        opening = _opening_summary(risk_drift.overall_drift_level.value, market_health)
        questions = _suggested_questions(input_data.portfolio)
        draft = _render_daily_brief_without_principles(
            title="Atlas Daily Brief",
            opening_summary=opening,
            sections=sections,
            suggested_questions=questions,
        )
        principles_check = self.principles_engine.check(draft)
        return DailyBriefSummary(
            title="Atlas Daily Brief",
            opening_summary=opening,
            sections=sections,
            suggested_questions=questions,
            principles_check=principles_check,
        )


def render_daily_brief(summary: DailyBriefSummary) -> str:
    return _render_daily_brief_without_principles(
        title=summary.title,
        opening_summary=summary.opening_summary,
        sections=summary.sections,
        suggested_questions=summary.suggested_questions,
    )


def _render_daily_brief_without_principles(
    title: str,
    opening_summary: str,
    sections: tuple[DailyBriefSection, ...],
    suggested_questions: tuple[str, ...],
) -> str:
    lines = [title, "", "Opening Summary", opening_summary]
    for section in sections:
        lines.extend(["", section.title, section.narrative])
        for item in section.items:
            lines.append(f"- {item.title}: {item.summary} ({item.status})")
    lines.extend(["", "Suggested Questions", *_render_list(suggested_questions)])
    lines.extend(
        [
            "",
            "Research Framing",
            (
                "This is a deterministic investment briefing for context and education. "
                "It does not provide personalized financial advice."
            ),
        ]
    )
    return "\n".join(lines)


def _what_changed_section(
    dashboard: DashboardSummary,
    previous_dashboard: DashboardSummary | None,
    risk_drift,
) -> DailyBriefSection:
    if previous_dashboard is None:
        items = (
            DailyBriefItem(
                "Baseline",
                "No previous dashboard snapshot was supplied, so Atlas is using today's baseline.",
                "Not enough information",
            ),
            DailyBriefItem(
                "Risk Drift",
                f"Risk drift appears {risk_drift.overall_drift_level.value.lower()}.",
                "Worth monitoring",
            ),
            DailyBriefItem(
                "Dashboard Signals",
                dashboard.todays_observations[0],
                "Context",
            ),
        )
    else:
        items = tuple(
            DailyBriefItem("Observation", observation, "Changed context")
            for observation in dashboard.todays_observations[:3]
        )
    return DailyBriefSection(
        title="What Changed",
        items=items,
        narrative="Atlas is comparing today's briefing with available baseline context.",
    )


def _portfolio_notes_section(
    dashboard: DashboardSummary,
    suitability,
    risk_drift,
) -> DailyBriefSection:
    portfolio_section = _find_section(dashboard, "Portfolio Overview")
    cards = portfolio_section.cards if portfolio_section else ()
    items = [
        DailyBriefItem(
            card.title,
            f"{card.value}. {card.detail}",
            card.status,
        )
        for card in cards[:5]
    ]
    items.append(
        DailyBriefItem(
            "Suitability Alignment",
            f"Current compatibility appears {suitability.overall_suitability.value.lower()}.",
            "Depends on investor profile",
        )
    )
    items.append(
        DailyBriefItem(
            "Profile Drift",
            risk_drift.drift_summary,
            "Worth monitoring",
        )
    )
    return DailyBriefSection(
        title="Portfolio Notes",
        items=tuple(items),
        narrative="Atlas reviewed alignment, drift, and concentration before market context.",
    )


def _market_notes_section(
    market_regime: MarketRegimeAnalysis,
    market_health: MarketHealthReport,
    economic_signals: EconomicSignalAnalysis,
) -> DailyBriefSection:
    credit_group = _group_status(market_health, "Credit")
    liquidity_group = _group_status(market_health, "Liquidity")
    rates_group = _economic_group_status(economic_signals, "Interest Rates")
    return DailyBriefSection(
        title="Market Notes",
        items=(
            DailyBriefItem("Market Regime", market_regime.regime.value, "Context"),
            DailyBriefItem(
                "Market Health",
                f"{market_health.overall_market_health}; {market_health.overall_risk_level} risk.",
                "Worth monitoring",
            ),
            DailyBriefItem(
                "Economic Signals",
                (
                    f"{economic_signals.overall_economic_health}; risk score "
                    f"{economic_signals.overall_risk_score}/100."
                ),
                "Context",
            ),
            DailyBriefItem("Credit", credit_group, "Worth monitoring"),
            DailyBriefItem("Liquidity", liquidity_group, "Worth monitoring"),
            DailyBriefItem("Rates", rates_group, "Worth monitoring"),
        ),
        narrative="Market context appears stable enough to study, but not risk-free.",
    )


def _themes_section(theme_analyses: tuple[ThemeAnalysis, ...]) -> DailyBriefSection:
    return DailyBriefSection(
        title="Themes To Watch",
        items=tuple(
            DailyBriefItem(
                analysis.theme.value,
                _theme_summary(analysis),
                "Worth understanding",
            )
            for analysis in theme_analyses[:4]
        ),
        narrative="These are research themes, not trade instructions.",
    )


def _risks_section(
    market_health: MarketHealthReport,
    economic_signals: EconomicSignalAnalysis,
    theme_analyses: tuple[ThemeAnalysis, ...],
    risk_drift,
) -> DailyBriefSection:
    theme_risks = tuple(
        DailyBriefItem(
            risk.name,
            risk.why_it_matters,
            "May deserve attention",
        )
        for risk in theme_analyses[0].key_risks[:2]
    )
    items = (
        DailyBriefItem(
            "Market Health",
            market_health.what_could_change_view[0],
            "Worth monitoring",
        ),
        DailyBriefItem(
            "Economic Risk",
            economic_signals.what_would_worsen_outlook[0],
            "Worth monitoring",
        ),
        DailyBriefItem(
            "Risk Drift",
            risk_drift.drift_summary,
            "Depends on investor profile",
        ),
        *theme_risks,
    )
    return DailyBriefSection(
        title="Risks To Watch",
        items=items,
        narrative="Atlas is surfacing risks calmly so the user can decide what to study.",
    )


def _opportunities_section(
    theme_analyses: tuple[ThemeAnalysis, ...],
    market_health: MarketHealthReport,
) -> DailyBriefSection:
    items = [
        DailyBriefItem(
            "Power infrastructure",
            "Power infrastructure may be worth understanding.",
            "Research direction",
        ),
        DailyBriefItem(
            "Credit conditions",
            "Credit conditions may deserve monitoring.",
            "Research direction",
        ),
        DailyBriefItem(
            "Semiconductor supply chains",
            "Semiconductor supply chains remain important.",
            "Research direction",
        ),
    ]
    if theme_analyses:
        items.append(
            DailyBriefItem(
                theme_analyses[0].theme.value,
                theme_analyses[0].second_order_winners[0],
                "Research direction",
            )
        )
    items.append(
        DailyBriefItem(
            "Market breadth",
            market_health.what_could_change_view[-1],
            "Worth monitoring",
        )
    )
    return DailyBriefSection(
        title="Opportunities To Study",
        items=tuple(items[:5]),
        narrative="These are study areas only and depend on investor profile and context.",
    )


def _opening_summary(
    drift_level: str,
    market_health: MarketHealthReport,
) -> str:
    if drift_level in {"High", "Moderate"}:
        return "A few signals are worth monitoring, especially profile and risk alignment."
    if market_health.overall_score >= 60:
        return (
            "Nothing urgent requires attention today. Conditions appear stable, "
            "while some risk remains."
        )
    return "Market conditions may deserve attention, but there is no need for alarm."


def _suggested_questions(portfolio: Portfolio | None) -> tuple[str, ...]:
    questions = [
        "Has anything important changed?",
        "What should I monitor this week?",
        "What risks am I underestimating?",
        "What opportunities should I study?",
    ]
    if portfolio is not None:
        questions.insert(2, "Is my portfolio still aligned with my goals?")
    else:
        questions.insert(2, "What portfolio context should I add first?")
    return tuple(questions)


def _dashboard_default_market_snapshot() -> MarketSnapshot:
    from atlas.dashboard.engine import _default_market_snapshot

    return _default_market_snapshot()


def _find_section(
    dashboard: DashboardSummary,
    title: str,
):
    for section in dashboard.sections:
        if section.title == title:
            return section
    return None


def _theme_summary(analysis: ThemeAnalysis) -> str:
    bottlenecks = ", ".join(item.name for item in analysis.key_bottlenecks[:2])
    return f"{analysis.summary} Key watch areas: {bottlenecks}."


def _group_status(report: MarketHealthReport, name: str) -> str:
    for group in report.signal_groups:
        if group.name == name:
            return f"{group.status}; {group.interpretation}"
    return "Not enough information."


def _economic_group_status(analysis: EconomicSignalAnalysis, name: str) -> str:
    for group in analysis.signal_groups:
        if group.name == name:
            return f"{group.status}; {group.interpretation}"
    return "Not enough information."


def _render_list(items: tuple[str, ...]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]

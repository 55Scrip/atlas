from dataclasses import dataclass

from atlas.analysis.engine import AtlasInvestmentEngine
from atlas.analysis.portfolio import Portfolio
from atlas.analysis.scores import clamp_score
from atlas.analysis.watchlist import Watchlist, WatchlistAnalysis
from atlas.capabilities.watchlist_intelligence import WatchlistIntelligenceEngine
from atlas.capabilities.watchlist_intelligence.models import (
    WatchlistIntelligenceInput,
    WatchlistItem as IntelligenceWatchlistItem,
)
from atlas.market import (
    MarketHealthEngine,
    MarketIndicators,
    MarketRegimeEngine,
    MarketSnapshot,
)
from atlas.providers import CompanyDataProvider
from atlas.themes import ThemeEngine, ThemeInput


@dataclass(frozen=True)
class MonitoringSignal:
    name: str
    score: int
    status: str
    summary: str
    higher_is_better: bool = True


@dataclass(frozen=True)
class MonitoringSnapshot:
    object_type: str
    identifier: str
    summary: str
    signals: tuple[MonitoringSignal, ...]
    new_risks: tuple[str, ...]
    new_opportunities: tuple[str, ...]
    monitoring_items: tuple[str, ...]
    confidence: int
    importance_score: int


@dataclass(frozen=True)
class MonitoringChange:
    signal_name: str
    previous_score: int
    current_score: int
    direction: str
    summary: str


@dataclass(frozen=True)
class MonitoringAlert:
    object_type: str
    identifier: str
    summary: str
    improved_signals: tuple[MonitoringChange, ...]
    deteriorated_signals: tuple[MonitoringChange, ...]
    new_risks: tuple[str, ...]
    new_opportunities: tuple[str, ...]
    monitoring_items: tuple[str, ...]
    confidence: int
    importance_score: int
    previous_snapshot: MonitoringSnapshot
    current_snapshot: MonitoringSnapshot


class MonitoringEngine:
    def __init__(
        self,
        investment_engine: AtlasInvestmentEngine | None = None,
        theme_engine: ThemeEngine | None = None,
        market_health_engine: MarketHealthEngine | None = None,
        market_regime_engine: MarketRegimeEngine | None = None,
    ) -> None:
        self.investment_engine = investment_engine or AtlasInvestmentEngine()
        self.theme_engine = theme_engine or ThemeEngine()
        self.market_health_engine = market_health_engine or MarketHealthEngine()
        self.market_regime_engine = market_regime_engine or MarketRegimeEngine()

    def snapshot_company(
        self,
        ticker: str,
        provider: CompanyDataProvider,
    ) -> MonitoringSnapshot:
        report = self.investment_engine.analyze_ticker(ticker.upper(), provider)
        return MonitoringSnapshot(
            object_type="Company",
            identifier=ticker.upper(),
            summary=(
                f"{report.company} has Atlas Score {report.atlas_score}/100 "
                f"and confidence {report.confidence}/100."
            ),
            signals=(
                MonitoringSignal(
                    "Atlas Score",
                    report.atlas_score,
                    "Current",
                    "Overall company signal from the Investment Engine.",
                ),
                MonitoringSignal(
                    "Quality",
                    report.quality.score,
                    "Current",
                    report.quality.reasoning,
                ),
                MonitoringSignal(
                    "Growth",
                    report.growth.score,
                    "Current",
                    report.growth.reasoning,
                ),
                MonitoringSignal(
                    "Valuation",
                    report.valuation.score,
                    "Current",
                    report.valuation.reasoning,
                ),
                MonitoringSignal(
                    "Risk profile",
                    report.risk.score,
                    "Current",
                    report.risk.reasoning,
                ),
            ),
            new_risks=("Valuation, risk, and confidence should be monitored together.",),
            new_opportunities=("Improving quality or valuation can strengthen the thesis.",),
            monitoring_items=(
                "quality score",
                "valuation score",
                "growth score",
                "risk profile",
            ),
            confidence=report.confidence,
            importance_score=report.atlas_score,
        )

    def snapshot_theme(self, theme: str) -> MonitoringSnapshot:
        analysis = self.theme_engine.analyze(ThemeInput(theme=theme))
        bottleneck_signals = tuple(
            MonitoringSignal(
                name=f"{bottleneck.name} bottleneck",
                score=_bottleneck_score(bottleneck.name),
                status="Constrained",
                summary=bottleneck.why_it_matters,
            )
            for bottleneck in analysis.key_bottlenecks
        )
        return MonitoringSnapshot(
            object_type="Theme",
            identifier=analysis.theme.value,
            summary=analysis.summary,
            signals=(
                MonitoringSignal(
                    "Theme confidence",
                    analysis.confidence,
                    "Current",
                    "Confidence from deterministic theme template.",
                ),
                *bottleneck_signals,
            ),
            new_risks=tuple(
                f"{risk.name}: {risk.why_it_matters}" for risk in analysis.key_risks[:4]
            ),
            new_opportunities=analysis.second_order_winners[:4],
            monitoring_items=analysis.monitoring_items,
            confidence=analysis.confidence,
            importance_score=analysis.confidence,
        )

    def snapshot_market_health(self) -> MonitoringSnapshot:
        report = self.market_health_engine.analyze()
        return MonitoringSnapshot(
            object_type="Market Health",
            identifier="Market Health",
            summary=report.atlas_view,
            signals=tuple(
                MonitoringSignal(
                    group.name,
                    group.score,
                    group.status,
                    group.interpretation,
                )
                for group in report.signal_groups
            ),
            new_risks=report.what_could_change_view,
            new_opportunities=(
                "Improving breadth can confirm healthier market participation.",
                "Improving credit can support broader risk appetite.",
            ),
            monitoring_items=tuple(
                item for group in report.signal_groups for item in group.monitoring_items[:1]
            ),
            confidence=76,
            importance_score=report.overall_score,
        )

    def snapshot_market_regime(
        self,
        snapshot: MarketSnapshot | None = None,
    ) -> MonitoringSnapshot:
        analysis = self.market_regime_engine.analyze(snapshot or _default_market_snapshot())
        return MonitoringSnapshot(
            object_type="Market Regime",
            identifier="Market Regime",
            summary=analysis.summary,
            signals=(
                MonitoringSignal(
                    "Regime confidence",
                    analysis.confidence,
                    analysis.regime.value,
                    analysis.summary,
                ),
            ),
            new_risks=analysis.risks,
            new_opportunities=analysis.opportunities,
            monitoring_items=analysis.key_indicators,
            confidence=analysis.confidence,
            importance_score=analysis.confidence,
        )

    def snapshot_portfolio(self, portfolio: Portfolio) -> MonitoringSnapshot:
        position_count = len(portfolio.positions)
        average_quality = round(
            sum(position.quality_score for position in portfolio.positions) / position_count
        )
        average_risk = round(
            sum(position.risk_score for position in portfolio.positions) / position_count
        )
        largest_position = max(portfolio.positions, key=lambda position: position.weight)
        concentration_score = clamp_score(round(100 - (largest_position.weight * 100)))
        sector_count = len({position.sector for position in portfolio.positions})
        country_count = len({position.country for position in portfolio.positions})
        return MonitoringSnapshot(
            object_type="Portfolio",
            identifier="Portfolio",
            summary=(
                f"Portfolio has {position_count} position(s), {sector_count} sector(s), "
                f"and {country_count} country exposure(s)."
            ),
            signals=(
                MonitoringSignal(
                    "Average quality",
                    average_quality,
                    "Current",
                    "Average quality score across portfolio positions.",
                ),
                MonitoringSignal(
                    "Average risk profile",
                    average_risk,
                    "Current",
                    "Average risk profile across portfolio positions.",
                ),
                MonitoringSignal(
                    "Largest position concentration",
                    concentration_score,
                    "Current",
                    (
                        f"Largest position is {largest_position.ticker} at "
                        f"{largest_position.weight:.1%}."
                    ),
                ),
                MonitoringSignal(
                    "Sector diversification",
                    clamp_score(sector_count * 20),
                    "Current",
                    f"Portfolio spans {sector_count} sector(s).",
                ),
            ),
            new_risks=(
                f"Largest position concentration is {largest_position.weight:.1%}.",
                "Sector and country concentration should be monitored over time.",
            ),
            new_opportunities=(
                "Improving diversification can reduce single-position dependency.",
                "Higher average quality can improve portfolio resilience.",
            ),
            monitoring_items=(
                "largest position weight",
                "average quality",
                "average risk profile",
                "country concentration",
            ),
            confidence=78,
            importance_score=round(
                (average_quality * 0.35)
                + (average_risk * 0.30)
                + (concentration_score * 0.35)
            ),
        )

    def snapshot_watchlist_from_analysis(self, analysis: WatchlistAnalysis) -> MonitoringSnapshot:
        strongest_report = analysis.reports[analysis.strongest_opportunity.ticker]
        return MonitoringSnapshot(
            object_type="Watchlist",
            identifier=analysis.name,
            summary=analysis.final_atlas_view,
            signals=(
                MonitoringSignal(
                    "Strongest opportunity score",
                    strongest_report.atlas_score,
                    analysis.strongest_opportunity.ticker,
                    analysis.strongest_opportunity.reasoning,
                ),
                MonitoringSignal(
                    "Best valuation",
                    analysis.reports[analysis.cheapest_valuation.ticker].valuation.score,
                    analysis.cheapest_valuation.ticker,
                    analysis.cheapest_valuation.reasoning,
                ),
                MonitoringSignal(
                    "Highest quality",
                    analysis.reports[analysis.highest_quality_company.ticker].quality.score,
                    analysis.highest_quality_company.ticker,
                    analysis.highest_quality_company.reasoning,
                ),
            ),
            new_risks=tuple(signal.reasoning for signal in analysis.companies_to_avoid[:2]),
            new_opportunities=(analysis.strongest_opportunity.reasoning,),
            monitoring_items=(
                "ranked opportunities",
                "best valuation",
                "highest quality",
                "highest risk company",
            ),
            confidence=80,
            importance_score=strongest_report.atlas_score,
        )

    def snapshot_watchlist(
        self,
        watchlist: Watchlist,
        provider: CompanyDataProvider | None = None,
    ) -> MonitoringSnapshot:
        intelligence_input = WatchlistIntelligenceInput(
            name=watchlist.name,
            items=tuple(
                IntelligenceWatchlistItem(
                    id=item.ticker.lower(),
                    ticker=item.ticker,
                )
                for item in watchlist.items
            ),
        )
        report = WatchlistIntelligenceEngine().analyze(intelligence_input)
        attention_count = len(report.companies_needing_attention)
        gap_count = len(report.evidence_gaps)
        question_count = len(report.open_questions)
        return MonitoringSnapshot(
            object_type="Watchlist",
            identifier=report.name,
            summary=report.overview,
            signals=(
                MonitoringSignal(
                    "Items needing attention",
                    clamp_score(attention_count * 20),
                    "Current",
                    f"{attention_count} item(s) need review or more evidence.",
                    higher_is_better=False,
                ),
                MonitoringSignal(
                    "Evidence gaps",
                    clamp_score(gap_count * 15),
                    "Current",
                    f"{gap_count} evidence gap(s) identified.",
                    higher_is_better=False,
                ),
                MonitoringSignal(
                    "Open questions",
                    clamp_score(question_count * 10),
                    "Current",
                    f"{question_count} open research question(s).",
                    higher_is_better=False,
                ),
            ),
            new_risks=tuple(
                f"{u.ticker}: {u.detail}" for u in report.evidence_gaps[:2]
            ),
            new_opportunities=report.suggested_next_research_steps[:2],
            monitoring_items=(
                "items needing attention",
                "evidence gaps",
                "open research questions",
                "suggested next steps",
            ),
            confidence=70,
            importance_score=clamp_score(attention_count * 15 + gap_count * 10),
        )

    def compare(
        self,
        previous_snapshot: MonitoringSnapshot,
        current_snapshot: MonitoringSnapshot,
    ) -> MonitoringAlert:
        previous_by_name = {signal.name: signal for signal in previous_snapshot.signals}
        improved: list[MonitoringChange] = []
        deteriorated: list[MonitoringChange] = []
        for current_signal in current_snapshot.signals:
            previous_signal = previous_by_name.get(current_signal.name)
            if previous_signal is None:
                continue
            change = _signal_change(previous_signal, current_signal)
            if change is None:
                continue
            if change.direction == "Improved":
                improved.append(change)
            elif change.direction == "Deteriorated":
                deteriorated.append(change)

        return MonitoringAlert(
            object_type=current_snapshot.object_type,
            identifier=current_snapshot.identifier,
            summary=_summary(improved, deteriorated),
            improved_signals=tuple(improved),
            deteriorated_signals=tuple(deteriorated),
            new_risks=_new_items(previous_snapshot.new_risks, current_snapshot.new_risks),
            new_opportunities=_new_items(
                previous_snapshot.new_opportunities,
                current_snapshot.new_opportunities,
            ),
            monitoring_items=current_snapshot.monitoring_items,
            confidence=_combined_confidence(previous_snapshot, current_snapshot),
            importance_score=_importance_score(current_snapshot, improved, deteriorated),
            previous_snapshot=previous_snapshot,
            current_snapshot=current_snapshot,
        )

    def monitor_company(self, ticker: str, provider: CompanyDataProvider) -> MonitoringAlert:
        current = self.snapshot_company(ticker, provider)
        previous = _previous_baseline(current)
        return self.compare(previous, current)

    def monitor_theme(self, theme: str) -> MonitoringAlert:
        current = self.snapshot_theme(theme)
        previous = _previous_baseline(current)
        return self.compare(previous, current)

    def monitor_market_health(self) -> MonitoringAlert:
        current = self.snapshot_market_health()
        previous = _previous_baseline(current)
        return self.compare(previous, current)

    def monitor_market_regime(
        self,
        snapshot: MarketSnapshot | None = None,
    ) -> MonitoringAlert:
        current = self.snapshot_market_regime(snapshot)
        previous = _previous_baseline(current)
        return self.compare(previous, current)

    def monitor_portfolio(self, portfolio: Portfolio) -> MonitoringAlert:
        current = self.snapshot_portfolio(portfolio)
        previous = _previous_baseline(current)
        return self.compare(previous, current)

    def monitor_watchlist(
        self,
        watchlist: Watchlist,
        provider: CompanyDataProvider | None = None,
    ) -> MonitoringAlert:
        current = self.snapshot_watchlist(watchlist)
        previous = _previous_baseline(current)
        return self.compare(previous, current)


def render_monitoring_alert(alert: MonitoringAlert) -> str:
    lines = [
        "Monitoring Alert",
        "",
        f"Object: {alert.object_type} - {alert.identifier}",
        "",
        "Summary",
        alert.current_snapshot.summary,
        "",
        "Since last analysis:",
        alert.summary,
        "",
        "Signals that improved",
        *_render_changes(alert.improved_signals, prefix="[+]"),
        "",
        "Signals that deteriorated",
        *_render_changes(alert.deteriorated_signals, prefix="[!]"),
        "",
        "New risks",
        *_render_list(alert.new_risks),
        "",
        "New opportunities",
        *_render_list(alert.new_opportunities),
        "",
        f"Confidence: {alert.confidence}/100",
        f"Importance Score: {alert.importance_score}/100",
        "",
        "Atlas recommends monitoring",
        *_render_list(alert.monitoring_items),
        "",
        "Research Framing",
        "This is deterministic monitoring context, not a notification or investment advice.",
    ]
    return "\n".join(lines)


def _signal_change(
    previous: MonitoringSignal,
    current: MonitoringSignal,
) -> MonitoringChange | None:
    raw_delta = current.score - previous.score
    if raw_delta == 0:
        return None
    improved = raw_delta > 0 if current.higher_is_better else raw_delta < 0
    direction = "Improved" if improved else "Deteriorated"
    return MonitoringChange(
        signal_name=current.name,
        previous_score=previous.score,
        current_score=current.score,
        direction=direction,
        summary=(
            f"{current.name} {direction.lower()} from {previous.score}/100 "
            f"to {current.score}/100. {current.summary}"
        ),
    )


def _previous_baseline(snapshot: MonitoringSnapshot) -> MonitoringSnapshot:
    return MonitoringSnapshot(
        object_type=snapshot.object_type,
        identifier=snapshot.identifier,
        summary=f"Previous deterministic baseline for {snapshot.identifier}.",
        signals=tuple(
            _previous_signal(snapshot.object_type, signal) for signal in snapshot.signals
        ),
        new_risks=_previous_risks(snapshot),
        new_opportunities=_previous_opportunities(snapshot),
        monitoring_items=snapshot.monitoring_items,
        confidence=clamp_score(snapshot.confidence - 4),
        importance_score=clamp_score(snapshot.importance_score - 3),
    )


def _previous_signal(object_type: str, signal: MonitoringSignal) -> MonitoringSignal:
    previous_score = signal.score
    if object_type == "Theme":
        if signal.name == "Theme confidence":
            previous_score = signal.score - 5
        elif "Electricity supply" in signal.name:
            previous_score = signal.score + 12
        elif "HBM memory" in signal.name:
            previous_score = signal.score
        else:
            previous_score = signal.score + 4
    elif object_type == "Market Health":
        if signal.name == "Credit":
            previous_score = signal.score - 8
        elif signal.name == "Market Breadth":
            previous_score = signal.score + 5
        else:
            previous_score = signal.score - 2
    elif object_type == "Market Regime":
        previous_score = signal.score - 3
    elif object_type == "Company":
        if signal.name == "Valuation":
            previous_score = signal.score + 3
        else:
            previous_score = signal.score - 3
    elif object_type == "Portfolio":
        if signal.name in {"Sector concentration", "Overlap"}:
            previous_score = signal.score + 4
        else:
            previous_score = signal.score - 3
    elif object_type == "Watchlist":
        previous_score = signal.score - 3
    return MonitoringSignal(
        name=signal.name,
        score=clamp_score(previous_score),
        status="Previous",
        summary=f"Previous baseline for {signal.name}.",
        higher_is_better=signal.higher_is_better,
    )


def _previous_risks(snapshot: MonitoringSnapshot) -> tuple[str, ...]:
    if snapshot.object_type == "Theme":
        return snapshot.new_risks[:1]
    if snapshot.object_type == "Market Health":
        return snapshot.new_risks[:2]
    return ()


def _previous_opportunities(snapshot: MonitoringSnapshot) -> tuple[str, ...]:
    if snapshot.object_type in {"Theme", "Watchlist"}:
        return snapshot.new_opportunities[:1]
    return ()


def _bottleneck_score(name: str) -> int:
    scores = {
        "Electricity supply": 44,
        "Grid capacity": 48,
        "Data center construction": 55,
        "Cooling": 58,
        "Transformers": 42,
        "HBM memory": 45,
        "Advanced packaging": 50,
    }
    return scores.get(name, 60)


def _summary(
    improved: list[MonitoringChange],
    deteriorated: list[MonitoringChange],
) -> str:
    if improved and deteriorated:
        return (
            f"{len(improved)} signal(s) improved while "
            f"{len(deteriorated)} signal(s) deteriorated."
        )
    if improved:
        return f"{len(improved)} signal(s) improved and no tracked signals deteriorated."
    if deteriorated:
        return f"{len(deteriorated)} signal(s) deteriorated and no tracked signals improved."
    return "No material tracked signal changed."


def _new_items(previous: tuple[str, ...], current: tuple[str, ...]) -> tuple[str, ...]:
    previous_set = set(previous)
    return tuple(item for item in current if item not in previous_set)


def _combined_confidence(
    previous_snapshot: MonitoringSnapshot,
    current_snapshot: MonitoringSnapshot,
) -> int:
    return clamp_score(round((previous_snapshot.confidence + current_snapshot.confidence) / 2))


def _importance_score(
    snapshot: MonitoringSnapshot,
    improved: list[MonitoringChange],
    deteriorated: list[MonitoringChange],
) -> int:
    change_weight = (len(improved) * 3) + (len(deteriorated) * 6)
    return clamp_score(snapshot.importance_score + change_weight)


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


def _render_changes(changes: tuple[MonitoringChange, ...], prefix: str) -> list[str]:
    if not changes:
        return ["- None"]
    return [f"{prefix} {change.summary}" for change in changes]


def _render_list(items: tuple[str, ...]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]

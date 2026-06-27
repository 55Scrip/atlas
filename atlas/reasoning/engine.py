from dataclasses import dataclass

from atlas.analysis.engine import InvestmentReport
from atlas.analysis.portfolio import PortfolioAnalysis
from atlas.economics import EconomicSignalAnalysis
from atlas.market import MarketHealthReport, MarketRegimeAnalysis
from atlas.monitoring import MonitoringAlert
from atlas.risk import RiskAnalysis
from atlas.themes import ThemeAnalysis


@dataclass(frozen=True)
class Evidence:
    source: str
    summary: str
    confidence: int
    importance: int


@dataclass(frozen=True)
class SupportingFactor:
    title: str
    evidence: Evidence
    explanation: str


@dataclass(frozen=True)
class ContradictingFactor:
    title: str
    evidence: Evidence
    explanation: str


@dataclass(frozen=True)
class ReasoningInput:
    company_analysis: InvestmentReport | None = None
    portfolio_analysis: PortfolioAnalysis | None = None
    theme_analysis: ThemeAnalysis | None = None
    monitoring_report: MonitoringAlert | None = None
    economic_signals: EconomicSignalAnalysis | None = None
    market_health: MarketHealthReport | None = None
    market_regime: MarketRegimeAnalysis | None = None
    risk_analysis: RiskAnalysis | None = None


@dataclass(frozen=True)
class ReasoningReport:
    executive_summary: str
    bullish_factors: tuple[SupportingFactor, ...]
    bearish_factors: tuple[ContradictingFactor, ...]
    areas_of_uncertainty: tuple[str, ...]
    signals_trusted_most: tuple[Evidence, ...]
    signals_trusted_least: tuple[Evidence, ...]
    confidence: int
    alternative_scenarios: tuple[str, ...]
    thesis_invalidation: tuple[str, ...]
    monitor_next: tuple[str, ...]


class ReasoningEngine:
    def analyze(self, reasoning_input: ReasoningInput) -> ReasoningReport:
        evidence = _collect_evidence(reasoning_input)
        bullish = _bullish_factors(reasoning_input)
        bearish = _bearish_factors(reasoning_input)
        uncertainty = _areas_of_uncertainty(reasoning_input, bullish, bearish)
        trusted_most = tuple(
            sorted(evidence, key=lambda item: (-item.confidence, -item.importance))[:5]
        )
        trusted_least = tuple(
            sorted(evidence, key=lambda item: (item.confidence, item.importance))[:5]
        )
        confidence = _confidence(evidence, uncertainty)
        return ReasoningReport(
            executive_summary=_executive_summary(bullish, bearish, confidence),
            bullish_factors=bullish,
            bearish_factors=bearish,
            areas_of_uncertainty=uncertainty,
            signals_trusted_most=trusted_most,
            signals_trusted_least=trusted_least,
            confidence=confidence,
            alternative_scenarios=_alternative_scenarios(bullish, bearish, reasoning_input),
            thesis_invalidation=_thesis_invalidation(reasoning_input),
            monitor_next=_monitor_next(reasoning_input),
        )


def render_reasoning_report(report: ReasoningReport) -> str:
    lines = [
        "Atlas Reasoning Report",
        "",
        "Executive Summary",
        report.executive_summary,
        "",
        "Bullish Factors",
        *_render_supporting(report.bullish_factors),
        "",
        "Bearish Factors",
        *_render_contradicting(report.bearish_factors),
        "",
        "Areas of Uncertainty",
        *_render_list(report.areas_of_uncertainty),
        "",
        "Signals Atlas Trusts Most",
        *_render_evidence(report.signals_trusted_most),
        "",
        "Signals Atlas Trusts Least",
        *_render_evidence(report.signals_trusted_least),
        "",
        f"Confidence: {report.confidence}/100",
        "",
        "Alternative Scenarios",
        *_render_list(report.alternative_scenarios),
        "",
        "What Could Invalidate The Thesis",
        *_render_list(report.thesis_invalidation),
        "",
        "What Atlas Will Monitor Next",
        *_render_list(report.monitor_next),
        "",
        "Research Framing",
        "This is deterministic thesis synthesis, not forecasting or buy/sell advice.",
    ]
    return "\n".join(lines)


def _collect_evidence(reasoning_input: ReasoningInput) -> tuple[Evidence, ...]:
    items: list[Evidence] = []
    if reasoning_input.company_analysis is not None:
        report = reasoning_input.company_analysis
        items.extend(
            [
                Evidence(
                    "Company Analysis",
                    f"Atlas Score {report.atlas_score}/100 for {report.company}.",
                    report.confidence,
                    report.atlas_score,
                ),
                Evidence(
                    "Quality",
                    report.quality.reasoning,
                    report.quality.confidence,
                    report.quality.score,
                ),
                Evidence(
                    "Valuation",
                    report.valuation.reasoning,
                    report.valuation.confidence,
                    report.valuation.score,
                ),
                Evidence(
                    "Growth",
                    report.growth.reasoning,
                    report.growth.confidence,
                    report.growth.score,
                ),
                Evidence(
                    "Risk",
                    report.risk.reasoning,
                    report.risk.confidence,
                    report.risk.score,
                ),
            ]
        )
    if reasoning_input.portfolio_analysis is not None:
        analysis = reasoning_input.portfolio_analysis
        items.append(
            Evidence(
                "Portfolio Analysis",
                analysis.final_reasoning,
                78,
                analysis.portfolio_score,
            )
        )
    if reasoning_input.theme_analysis is not None:
        analysis = reasoning_input.theme_analysis
        items.append(
            Evidence(
                "Theme Analysis",
                analysis.summary,
                analysis.confidence,
                analysis.confidence,
            )
        )
    if reasoning_input.monitoring_report is not None:
        alert = reasoning_input.monitoring_report
        items.append(
            Evidence(
                "Monitoring Report",
                alert.summary,
                alert.confidence,
                alert.importance_score,
            )
        )
    if reasoning_input.economic_signals is not None:
        analysis = reasoning_input.economic_signals
        items.append(
            Evidence(
                "Economic Signals",
                analysis.conclusion,
                74,
                100 - analysis.overall_risk_score,
            )
        )
    if reasoning_input.market_health is not None:
        report = reasoning_input.market_health
        items.append(
            Evidence(
                "Market Health",
                report.atlas_view,
                76,
                report.overall_score,
            )
        )
    if reasoning_input.market_regime is not None:
        analysis = reasoning_input.market_regime
        items.append(
            Evidence(
                "Market Regime",
                analysis.summary,
                analysis.confidence,
                analysis.confidence,
            )
        )
    if reasoning_input.risk_analysis is not None:
        analysis = reasoning_input.risk_analysis
        items.append(
            Evidence(
                "Risk Analysis",
                analysis.position_sizing.final_risk_recommendation,
                82,
                75,
            )
        )
    return tuple(items)


def _bullish_factors(reasoning_input: ReasoningInput) -> tuple[SupportingFactor, ...]:
    factors: list[SupportingFactor] = []
    if reasoning_input.company_analysis is not None:
        report = reasoning_input.company_analysis
        if report.quality.score >= 75:
            factors.append(
                SupportingFactor(
                    "Business quality",
                    Evidence(
                        "Quality",
                        report.quality.reasoning,
                        report.quality.confidence,
                        report.quality.score,
                    ),
                    (
                        "The quality score supports the thesis because Atlas rates "
                        "the business highly."
                    ),
                )
            )
        if report.growth.score >= 75:
            factors.append(
                SupportingFactor(
                    "Growth profile",
                    Evidence(
                        "Growth",
                        report.growth.reasoning,
                        report.growth.confidence,
                        report.growth.score,
                    ),
                    (
                        "The growth score supports the thesis because Atlas sees "
                        "durable expansion signals."
                    ),
                )
            )
    if reasoning_input.theme_analysis is not None:
        analysis = reasoning_input.theme_analysis
        factors.append(
            SupportingFactor(
                "Structural theme",
                Evidence(
                    "Theme Analysis",
                    analysis.summary,
                    analysis.confidence,
                    analysis.confidence,
                ),
                "The theme analysis supports the thesis through long-term structural tailwinds.",
            )
        )
    if reasoning_input.monitoring_report is not None:
        alert = reasoning_input.monitoring_report
        for change in alert.improved_signals[:2]:
            factors.append(
                SupportingFactor(
                    change.signal_name,
                    Evidence(
                        "Monitoring Report",
                        change.summary,
                        alert.confidence,
                        alert.importance_score,
                    ),
                    "The monitoring report shows this signal improved versus the prior snapshot.",
                )
            )
    if reasoning_input.economic_signals is not None:
        for signal in reasoning_input.economic_signals.strongest_positive_signals[:2]:
            factors.append(
                SupportingFactor(
                    signal.name,
                    Evidence(
                        "Economic Signals",
                        signal.why_it_matters,
                        signal.confidence,
                        signal.importance,
                    ),
                    "This is one of the strongest positive economic signals in the analysis.",
                )
            )
    return tuple(factors)


def _bearish_factors(reasoning_input: ReasoningInput) -> tuple[ContradictingFactor, ...]:
    factors: list[ContradictingFactor] = []
    if reasoning_input.company_analysis is not None:
        report = reasoning_input.company_analysis
        if report.valuation.score < 80:
            factors.append(
                ContradictingFactor(
                    "Valuation sensitivity",
                    Evidence(
                        "Valuation",
                        report.valuation.reasoning,
                        report.valuation.confidence,
                        report.valuation.score,
                    ),
                    (
                        "Valuation is a constraint because Atlas does not rate it "
                        "as clearly favorable."
                    ),
                )
            )
        if report.risk.score < 75:
            factors.append(
                ContradictingFactor(
                    "Company risk",
                    Evidence(
                        "Risk",
                        report.risk.reasoning,
                        report.risk.confidence,
                        report.risk.score,
                    ),
                    "The risk score creates a counterweight to the bullish company signals.",
                )
            )
    if reasoning_input.portfolio_analysis is not None:
        analysis = reasoning_input.portfolio_analysis
        if analysis.sector_concentration.score < 70:
            factors.append(
                ContradictingFactor(
                    "Portfolio concentration",
                    Evidence(
                        "Portfolio Analysis",
                        analysis.sector_concentration.reasoning,
                        78,
                        analysis.sector_concentration.score,
                    ),
                    "Portfolio concentration weakens the thesis from an allocation context.",
                )
            )
    if reasoning_input.theme_analysis is not None:
        analysis = reasoning_input.theme_analysis
        for risk in analysis.key_risks[:2]:
            factors.append(
                ContradictingFactor(
                    risk.name,
                    Evidence("Theme Analysis", risk.why_it_matters, analysis.confidence, 70),
                    "The theme analysis identifies this as a risk to the thesis.",
                )
            )
    if reasoning_input.monitoring_report is not None:
        alert = reasoning_input.monitoring_report
        for change in alert.deteriorated_signals[:2]:
            factors.append(
                ContradictingFactor(
                    change.signal_name,
                    Evidence(
                        "Monitoring Report",
                        change.summary,
                        alert.confidence,
                        alert.importance_score,
                    ),
                    (
                        "The monitoring report shows this signal deteriorated versus "
                        "the prior snapshot."
                    ),
                )
            )
    if reasoning_input.economic_signals is not None:
        for signal in reasoning_input.economic_signals.strongest_negative_signals[:2]:
            factors.append(
                ContradictingFactor(
                    signal.name,
                    Evidence(
                        "Economic Signals",
                        signal.why_it_matters,
                        signal.confidence,
                        signal.importance,
                    ),
                    "This is one of the strongest negative economic signals in the analysis.",
                )
            )
    if (
        reasoning_input.market_health is not None
        and reasoning_input.market_health.overall_score < 65
    ):
        report = reasoning_input.market_health
        factors.append(
            ContradictingFactor(
                "Market health",
                Evidence("Market Health", report.atlas_view, 76, report.overall_score),
                (
                    "Market health is a counterweight because the overall score "
                    "is not strongly supportive."
                ),
            )
        )
    return tuple(factors)


def _areas_of_uncertainty(
    reasoning_input: ReasoningInput,
    bullish: tuple[SupportingFactor, ...],
    bearish: tuple[ContradictingFactor, ...],
) -> tuple[str, ...]:
    uncertainties = []
    if not bullish:
        uncertainties.append("Atlas has limited supporting evidence in the provided inputs.")
    if not bearish:
        uncertainties.append("Atlas has limited contradicting evidence in the provided inputs.")
    missing = {
        "Company Analysis": reasoning_input.company_analysis,
        "Portfolio Analysis": reasoning_input.portfolio_analysis,
        "Theme Analysis": reasoning_input.theme_analysis,
        "Monitoring Report": reasoning_input.monitoring_report,
        "Economic Signals": reasoning_input.economic_signals,
        "Market Health": reasoning_input.market_health,
        "Market Regime": reasoning_input.market_regime,
        "Risk Analysis": reasoning_input.risk_analysis,
    }
    for name, value in missing.items():
        if value is None:
            uncertainties.append(f"{name} was not supplied, so Atlas does not infer it.")
    return tuple(uncertainties)


def _confidence(evidence: tuple[Evidence, ...], uncertainty: tuple[str, ...]) -> int:
    if not evidence:
        return 30
    average = round(sum(item.confidence for item in evidence) / len(evidence))
    penalty = min(24, len(uncertainty) * 3)
    return max(0, min(100, average - penalty))


def _executive_summary(
    bullish: tuple[SupportingFactor, ...],
    bearish: tuple[ContradictingFactor, ...],
    confidence: int,
) -> str:
    return (
        f"Atlas synthesizes {len(bullish)} bullish factor(s) and "
        f"{len(bearish)} bearish factor(s) with confidence {confidence}/100. "
        "The thesis is evidence-weighted and conditional, not a trading recommendation."
    )


def _alternative_scenarios(
    bullish: tuple[SupportingFactor, ...],
    bearish: tuple[ContradictingFactor, ...],
    reasoning_input: ReasoningInput,
) -> tuple[str, ...]:
    scenarios = []
    if bullish:
        scenarios.append(
            (
                "Constructive scenario: the strongest supporting factors persist "
                "while monitoring signals improve."
            )
        )
    if bearish:
        scenarios.append(
            (
                "Adverse scenario: the strongest contradicting factors worsen "
                "and reduce confidence."
            )
        )
    if reasoning_input.economic_signals is not None:
        scenarios.append(
            (
                "Macro scenario: economic health remains "
                f"{reasoning_input.economic_signals.overall_economic_health}."
            )
        )
    return tuple(scenarios or ("Atlas needs more supplied evidence to describe scenarios.",))


def _thesis_invalidation(reasoning_input: ReasoningInput) -> tuple[str, ...]:
    invalidators = []
    if reasoning_input.company_analysis is not None:
        invalidators.append(
            "Company quality, growth, valuation, or risk scores deteriorate materially."
        )
    if reasoning_input.theme_analysis is not None:
        invalidators.extend(reasoning_input.theme_analysis.what_would_change_view[:3])
    if reasoning_input.economic_signals is not None:
        invalidators.extend(reasoning_input.economic_signals.what_would_worsen_outlook[:3])
    if reasoning_input.market_health is not None:
        invalidators.extend(reasoning_input.market_health.what_could_change_view[:2])
    return tuple(invalidators or ("New evidence contradicts the supplied thesis inputs.",))


def _monitor_next(reasoning_input: ReasoningInput) -> tuple[str, ...]:
    items = []
    if reasoning_input.theme_analysis is not None:
        items.extend(reasoning_input.theme_analysis.monitoring_items[:4])
    if reasoning_input.monitoring_report is not None:
        items.extend(reasoning_input.monitoring_report.monitoring_items[:4])
    if reasoning_input.economic_signals is not None:
        items.extend(reasoning_input.economic_signals.watching_most_closely[:3])
    if reasoning_input.market_regime is not None:
        items.extend(reasoning_input.market_regime.key_indicators[:3])
    return tuple(dict.fromkeys(items)) or (
        "Provide more engine outputs to define monitoring priorities.",
    )


def _render_supporting(factors: tuple[SupportingFactor, ...]) -> list[str]:
    if not factors:
        return ["- None supplied"]
    return [
        (
            f"- {factor.title}: {factor.explanation} "
            f"Evidence: {factor.evidence.summary}"
        )
        for factor in factors
    ]


def _render_contradicting(factors: tuple[ContradictingFactor, ...]) -> list[str]:
    if not factors:
        return ["- None supplied"]
    return [
        (
            f"- {factor.title}: {factor.explanation} "
            f"Evidence: {factor.evidence.summary}"
        )
        for factor in factors
    ]


def _render_evidence(items: tuple[Evidence, ...]) -> list[str]:
    if not items:
        return ["- None supplied"]
    return [
        (
            f"- {item.source}: confidence {item.confidence}/100, "
            f"importance {item.importance}/100. {item.summary}"
        )
        for item in items
    ]


def _render_list(items: tuple[str, ...]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]

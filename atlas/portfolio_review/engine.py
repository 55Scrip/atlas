from dataclasses import dataclass
from enum import Enum

from atlas.analysis.portfolio import Portfolio
from atlas.economics import EconomicSignalAnalysis, EconomicSignalsEngine
from atlas.language import AtlasLanguageEngine, AtlasLanguageReport
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
from atlas.risk_drift import RiskDriftEngine, RiskDriftInput
from atlas.suitability import SuitabilityEngine, SuitabilityInput
from atlas.themes import ThemeAnalysis, ThemeEngine, ThemeInput


class PortfolioAlignmentRating(str, Enum):
    EXCELLENT_ALIGNMENT = "Excellent Alignment"
    STRONG_ALIGNMENT = "Strong Alignment"
    BALANCED = "Balanced"
    LIMITED_ALIGNMENT = "Limited Alignment"
    MISALIGNED = "Misaligned"


@dataclass(frozen=True)
class PortfolioReviewObservation:
    title: str
    summary: str
    importance: str = "Context"


@dataclass(frozen=True)
class PortfolioReviewSection:
    title: str
    observations: tuple[PortfolioReviewObservation, ...]
    narrative: str


@dataclass(frozen=True)
class PortfolioReviewInput:
    portfolio: Portfolio
    investor_profile: InvestorProfile | None = None
    theme_names: tuple[str, ...] = (
        "AI infrastructure",
        "Semiconductors",
        "Energy transition",
    )
    market_snapshot: MarketSnapshot | None = None


@dataclass(frozen=True)
class PortfolioReviewReport:
    title: str
    bottom_line: str
    atlas_rating: PortfolioAlignmentRating
    sections: tuple[PortfolioReviewSection, ...]
    confidence: int
    principles_check: PrinciplesCheck
    language_report: AtlasLanguageReport | None = None


class PortfolioReviewEngine:
    def __init__(
        self,
        profile_engine: InvestorProfileEngine | None = None,
        suitability_engine: SuitabilityEngine | None = None,
        risk_drift_engine: RiskDriftEngine | None = None,
        theme_engine: ThemeEngine | None = None,
        market_health_engine: MarketHealthEngine | None = None,
        market_regime_engine: MarketRegimeEngine | None = None,
        economic_signals_engine: EconomicSignalsEngine | None = None,
        monitoring_engine: MonitoringEngine | None = None,
        principles_engine: PrinciplesEngine | None = None,
        language_engine: AtlasLanguageEngine | None = None,
    ) -> None:
        self.profile_engine = profile_engine or InvestorProfileEngine()
        self.suitability_engine = suitability_engine or SuitabilityEngine()
        self.risk_drift_engine = risk_drift_engine or RiskDriftEngine()
        self.theme_engine = theme_engine or ThemeEngine()
        self.market_health_engine = market_health_engine or MarketHealthEngine()
        self.market_regime_engine = market_regime_engine or MarketRegimeEngine()
        self.economic_signals_engine = economic_signals_engine or EconomicSignalsEngine()
        self.monitoring_engine = monitoring_engine or MonitoringEngine()
        self.principles_engine = principles_engine or PrinciplesEngine()
        self.language_engine = language_engine or AtlasLanguageEngine()

    def review(self, review_input: PortfolioReviewInput) -> PortfolioReviewReport:
        profile = review_input.investor_profile or self.profile_engine.create_default_profile()
        context = self.profile_engine.investor_context(profile)
        portfolio_snapshot = self.monitoring_engine.snapshot_portfolio(review_input.portfolio)
        suitability = self.suitability_engine.assess(
            SuitabilityInput(investor_profile=profile, portfolio=review_input.portfolio)
        )
        market_regime = self.market_regime_engine.analyze(
            review_input.market_snapshot or _default_market_snapshot()
        )
        market_health = self.market_health_engine.analyze()
        economic_signals = self.economic_signals_engine.analyze()
        risk_drift = self.risk_drift_engine.assess(
            RiskDriftInput(
                original_profile=profile,
                current_profile=profile,
                current_portfolio=review_input.portfolio,
                current_market_regime=market_regime,
                current_market_health=market_health,
                current_economic_signals=economic_signals,
                current_suitability_assessment=suitability,
            )
        )
        themes = tuple(
            self.theme_engine.analyze(ThemeInput(theme=name))
            for name in review_input.theme_names[:3]
        )
        rating = _atlas_rating(
            portfolio_score=portfolio_snapshot.importance_score,
            suitability_score=suitability.suitability_score,
            drift_score=risk_drift.drift_score,
            market_score=market_health.overall_score,
        )
        bottom_line = _bottom_line(
            rating=rating,
            profile=profile,
            portfolio=review_input.portfolio,
            suitability=suitability,
            risk_drift=risk_drift,
        )
        sections = (
            _bottom_line_section(bottom_line),
            _rating_section(rating, portfolio_snapshot.importance_score),
            _strengths_section(review_input.portfolio, portfolio_snapshot, suitability, themes),
            _main_risks_section(review_input.portfolio, market_health, economic_signals),
            _investor_alignment_section(profile, context, suitability, risk_drift),
            _theme_exposure_section(review_input.portfolio, themes),
            _market_context_section(market_regime, market_health, economic_signals),
            _monitoring_section(portfolio_snapshot, market_health, themes),
            _change_view_section(risk_drift, market_health, economic_signals),
            _missing_information_section(suitability.missing_information),
            _follow_up_questions_section(review_input.portfolio, risk_drift),
        )
        draft = _render_portfolio_review_without_principles(
            title="Atlas Portfolio Review",
            bottom_line=bottom_line,
            rating=rating,
            sections=sections,
            confidence=_confidence(portfolio_snapshot.confidence, suitability.confidence),
        )
        report_without_language = PortfolioReviewReport(
            title="Atlas Portfolio Review",
            bottom_line=bottom_line,
            atlas_rating=rating,
            sections=sections,
            confidence=_confidence(portfolio_snapshot.confidence, suitability.confidence),
            principles_check=self.principles_engine.check(draft),
        )
        return PortfolioReviewReport(
            title=report_without_language.title,
            bottom_line=report_without_language.bottom_line,
            atlas_rating=report_without_language.atlas_rating,
            sections=report_without_language.sections,
            confidence=report_without_language.confidence,
            principles_check=report_without_language.principles_check,
            language_report=self.language_engine.from_portfolio_review(report_without_language),
        )


def render_portfolio_review(report: PortfolioReviewReport) -> str:
    return _render_portfolio_review_without_principles(
        title=report.title,
        bottom_line=report.bottom_line,
        rating=report.atlas_rating,
        sections=report.sections,
        confidence=report.confidence,
    )


def _render_portfolio_review_without_principles(
    title: str,
    bottom_line: str,
    rating: PortfolioAlignmentRating,
    sections: tuple[PortfolioReviewSection, ...],
    confidence: int,
) -> str:
    lines = [
        title,
        "",
        "Bottom Line",
        bottom_line,
        "",
        f"Atlas Rating: {rating.value}",
        f"Confidence: {confidence}/100",
    ]
    for section in sections:
        lines.extend(["", section.title, section.narrative])
        lines.extend(
            f"- {item.title}: {item.summary} ({item.importance})"
            for item in section.observations
        )
    lines.extend(
        [
            "",
            "Research Framing",
            (
                "This is a deterministic portfolio review for context and education. "
                "It is not personalized financial advice."
            ),
        ]
    )
    return "\n".join(lines)


def _atlas_rating(
    portfolio_score: int,
    suitability_score: int,
    drift_score: int,
    market_score: int,
) -> PortfolioAlignmentRating:
    score = round(
        portfolio_score * 0.30
        + suitability_score * 0.35
        + (100 - drift_score) * 0.20
        + market_score * 0.15
    )
    if score >= 85:
        return PortfolioAlignmentRating.EXCELLENT_ALIGNMENT
    if score >= 74:
        return PortfolioAlignmentRating.STRONG_ALIGNMENT
    if score >= 60:
        return PortfolioAlignmentRating.BALANCED
    if score >= 45:
        return PortfolioAlignmentRating.LIMITED_ALIGNMENT
    return PortfolioAlignmentRating.MISALIGNED


def _bottom_line(
    rating: PortfolioAlignmentRating,
    profile: InvestorProfile,
    portfolio: Portfolio,
    suitability,
    risk_drift,
) -> str:
    largest = _largest_position(portfolio)
    return (
        f"Current evidence suggests the portfolio is {rating.value.lower()} for "
        f"{profile.name}'s stated context. Suitability appears "
        f"{suitability.overall_suitability.value.lower()}, while risk drift is "
        f"{risk_drift.overall_drift_level.value.lower()}. The largest position is "
        f"{largest.ticker} at {largest.weight:.1%}, which is worth monitoring."
    )


def _bottom_line_section(bottom_line: str) -> PortfolioReviewSection:
    return PortfolioReviewSection(
        title="Bottom Line",
        observations=(PortfolioReviewObservation("Summary", bottom_line, "High"),),
        narrative="Atlas starts with the conclusion, then shows the evidence behind it.",
    )


def _rating_section(
    rating: PortfolioAlignmentRating,
    portfolio_score: int,
) -> PortfolioReviewSection:
    return PortfolioReviewSection(
        title="Atlas Rating",
        observations=(
            PortfolioReviewObservation(
                "Alignment Rating",
                rating.value,
                "High",
            ),
            PortfolioReviewObservation(
                "Portfolio Health Signal",
                f"Monitoring-based portfolio health is {portfolio_score}/100.",
                "Context",
            ),
        ),
        narrative=(
            "This is an alignment rating, not a performance rating. It reflects fit "
            "between portfolio structure, profile context, risk drift, and markets."
        ),
    )


def _strengths_section(
    portfolio: Portfolio,
    portfolio_snapshot,
    suitability,
    themes: tuple[ThemeAnalysis, ...],
) -> PortfolioReviewSection:
    sector_count = len({position.sector for position in portfolio.positions})
    average_quality = _average(portfolio, "quality_score")
    observations = [
        PortfolioReviewObservation(
            "Quality",
            f"Average portfolio quality is {average_quality:.0f}/100.",
            "Strength",
        ),
        PortfolioReviewObservation(
            "Diversification",
            f"The portfolio spans {sector_count} sector(s).",
            "Worth monitoring" if sector_count < 4 else "Strength",
        ),
        PortfolioReviewObservation(
            "Suitability Alignment",
            _first_or_default(suitability.why_it_fits, "Profile compatibility is being assessed."),
            "Strength",
        ),
        PortfolioReviewObservation(
            "Long-term Theme Exposure",
            f"{themes[0].theme.value} is represented as a theme worth understanding.",
            "Context",
        ),
        PortfolioReviewObservation(
            "Resilience",
            portfolio_snapshot.summary,
            "Context",
        ),
    ]
    return PortfolioReviewSection(
        title="Portfolio Strengths",
        observations=tuple(observations),
        narrative="Atlas highlights structural strengths before moving to risks.",
    )


def _main_risks_section(
    portfolio: Portfolio,
    market_health: MarketHealthReport,
    economic_signals: EconomicSignalAnalysis,
) -> PortfolioReviewSection:
    largest = _largest_position(portfolio)
    sector, sector_weight = _top_exposure(portfolio, "sector")
    country, country_weight = _top_exposure(portfolio, "country")
    return PortfolioReviewSection(
        title="Main Risks",
        observations=(
            PortfolioReviewObservation(
                "Concentration",
                f"{largest.ticker} is {largest.weight:.1%} of the portfolio.",
                _attention_for_weight(largest.weight),
            ),
            PortfolioReviewObservation(
                "Sector Exposure",
                f"Largest sector exposure is {sector} at {sector_weight:.1%}.",
                _attention_for_weight(sector_weight),
            ),
            PortfolioReviewObservation(
                "Geographic Exposure",
                f"Largest country exposure is {country} at {country_weight:.1%}.",
                _attention_for_weight(country_weight),
            ),
            PortfolioReviewObservation(
                "Macro Sensitivity",
                economic_signals.conclusion,
                "Worth monitoring",
            ),
            PortfolioReviewObservation(
                "Market Breadth",
                market_health.what_could_change_view[-1],
                "May deserve attention",
            ),
        ),
        narrative="These risks do not imply urgency, but they could affect portfolio fit.",
    )


def _investor_alignment_section(
    profile: InvestorProfile,
    context,
    suitability,
    risk_drift,
) -> PortfolioReviewSection:
    return PortfolioReviewSection(
        title="Investor Alignment",
        observations=(
            PortfolioReviewObservation(
                "Goals",
                f"Stated goals: {', '.join(context.investment_goals)}.",
                "Context",
            ),
            PortfolioReviewObservation(
                "Time Horizon",
                f"Time horizon is {context.time_horizon}.",
                "Context",
            ),
            PortfolioReviewObservation(
                "Risk Tolerance",
                f"Risk tolerance is {profile.risk_tolerance.value}.",
                "Context",
            ),
            PortfolioReviewObservation(
                "Risk Capacity",
                f"Risk capacity is {profile.risk_capacity.value}.",
                "Context",
            ),
            PortfolioReviewObservation(
                "Portfolio Purpose",
                f"Portfolio purpose is {context.portfolio_purpose}.",
                "Context",
            ),
            PortfolioReviewObservation(
                "Alignment Evidence",
                f"Suitability is {suitability.overall_suitability.value}; "
                f"risk drift is {risk_drift.overall_drift_level.value}.",
                "High",
            ),
        ),
        narrative="Atlas checks the portfolio against the investor profile before themes.",
    )


def _theme_exposure_section(
    portfolio: Portfolio,
    themes: tuple[ThemeAnalysis, ...],
) -> PortfolioReviewSection:
    sectors = {position.sector.lower() for position in portfolio.positions}
    observations = []
    for theme in themes:
        represented = _theme_represented(theme, sectors)
        observations.append(
            PortfolioReviewObservation(
                theme.theme.value,
                (
                    "Appears represented through current sector exposure."
                    if represented
                    else "May be missing or indirect in the current portfolio."
                ),
                "Worth understanding",
            )
        )
    return PortfolioReviewSection(
        title="Theme Exposure",
        observations=tuple(observations),
        narrative="Theme exposure is a research map, not a portfolio instruction.",
    )


def _market_context_section(
    market_regime: MarketRegimeAnalysis,
    market_health: MarketHealthReport,
    economic_signals: EconomicSignalAnalysis,
) -> PortfolioReviewSection:
    return PortfolioReviewSection(
        title="Market Context",
        observations=(
            PortfolioReviewObservation("Market Regime", market_regime.regime.value, "Context"),
            PortfolioReviewObservation(
                "Market Health",
                f"{market_health.overall_market_health}; {market_health.overall_risk_level} risk.",
                "Worth monitoring",
            ),
            PortfolioReviewObservation(
                "Economic Signals",
                (
                    f"{economic_signals.overall_economic_health}; risk score "
                    f"{economic_signals.overall_risk_score}/100."
                ),
                "Context",
            ),
        ),
        narrative="Market context shapes interpretation, but does not replace profile fit.",
    )


def _monitoring_section(
    portfolio_snapshot,
    market_health: MarketHealthReport,
    themes: tuple[ThemeAnalysis, ...],
) -> PortfolioReviewSection:
    items = tuple(
        PortfolioReviewObservation("Portfolio Signal", item, "Worth monitoring")
        for item in portfolio_snapshot.monitoring_items[:3]
    )
    theme_items = tuple(
        PortfolioReviewObservation(theme.theme.value, theme.monitoring_items[0], "Context")
        for theme in themes[:2]
    )
    market_item = PortfolioReviewObservation(
        "Market Health",
        market_health.what_could_change_view[0],
        "Worth monitoring",
    )
    return PortfolioReviewSection(
        title="What Atlas Is Monitoring",
        observations=(*items, *theme_items, market_item),
        narrative="Atlas is tracking signals that could affect the portfolio thesis.",
    )


def _change_view_section(
    risk_drift,
    market_health: MarketHealthReport,
    economic_signals: EconomicSignalAnalysis,
) -> PortfolioReviewSection:
    return PortfolioReviewSection(
        title="What Could Change Atlas' View",
        observations=(
            PortfolioReviewObservation(
                "Risk Drift",
                risk_drift.drift_summary,
                "Worth monitoring",
            ),
            PortfolioReviewObservation(
                "Market Health",
                market_health.what_could_change_view[0],
                "Context",
            ),
            PortfolioReviewObservation(
                "Economic Risk",
                economic_signals.what_would_worsen_outlook[0],
                "Context",
            ),
        ),
        narrative="These changes would materially affect the portfolio review.",
    )


def _missing_information_section(
    missing_information: tuple[str, ...],
) -> PortfolioReviewSection:
    items = tuple(
        PortfolioReviewObservation("Missing Context", item, "Missing")
        for item in missing_information[:5]
    ) or (
        PortfolioReviewObservation(
            "Missing Context",
            "No major missing information was detected for this deterministic review.",
            "Context",
        ),
    )
    return PortfolioReviewSection(
        title="Missing Information",
        observations=items,
        narrative="More context can improve confidence without changing the review framework.",
    )


def _follow_up_questions_section(
    portfolio: Portfolio,
    risk_drift,
) -> PortfolioReviewSection:
    largest = _largest_position(portfolio)
    questions = [
        "Has your investment horizon changed?",
        f"Is the {largest.ticker} concentration intentional?",
        "Would you still build this portfolio today?",
        "Has the purpose of this portfolio changed?",
    ]
    if risk_drift.overall_drift_level.value in {"None", "Low"}:
        questions = questions[:3]
    return PortfolioReviewSection(
        title="Optional Follow-up Questions",
        observations=tuple(
            PortfolioReviewObservation("Question", question, "Could improve confidence")
            for question in questions
        ),
        narrative="These questions are included only because answers could change confidence.",
    )


def _default_market_snapshot() -> MarketSnapshot:
    return MarketSnapshot(
        indicators=MarketIndicators(
            sp500_drawdown=-0.04,
            nasdaq_drawdown=-0.07,
            vix=19,
            interest_rate_trend="stable",
            inflation_trend="stable",
        ),
        source="deterministic-portfolio-review-placeholder",
    )


def _confidence(portfolio_confidence: int, suitability_confidence: int) -> int:
    return round((portfolio_confidence * 0.55) + (suitability_confidence * 0.45))


def _average(portfolio: Portfolio, field: str) -> float:
    return sum(getattr(position, field) for position in portfolio.positions) / len(
        portfolio.positions
    )


def _largest_position(portfolio: Portfolio):
    return max(portfolio.positions, key=lambda position: position.weight)


def _top_exposure(portfolio: Portfolio, field: str) -> tuple[str, float]:
    weights: dict[str, float] = {}
    for position in portfolio.positions:
        value = str(getattr(position, field))
        weights[value] = weights.get(value, 0.0) + position.weight
    return max(weights.items(), key=lambda item: item[1])


def _attention_for_weight(weight: float) -> str:
    if weight >= 0.40:
        return "May deserve attention"
    if weight >= 0.25:
        return "Worth monitoring"
    return "Context"


def _theme_represented(theme: ThemeAnalysis, sectors: set[str]) -> bool:
    industries = {industry.lower() for industry in theme.affected_industries}
    return bool(sectors & industries)


def _first_or_default(items: tuple[str, ...], default: str) -> str:
    return items[0] if items else default

from dataclasses import dataclass
from enum import Enum

from atlas.analysis.portfolio import Portfolio, PortfolioAnalysis
from atlas.analysis.scores import clamp_score
from atlas.economics import EconomicSignalAnalysis
from atlas.market import MarketHealthReport, MarketRegime, MarketRegimeAnalysis
from atlas.profile import (
    InvestorProfile,
    PortfolioPurpose,
    RiskCapacity,
    RiskTolerance,
    TimeHorizon,
)
from atlas.suitability import OverallSuitability, SuitabilityAssessment


class RiskDriftLevel(str, Enum):
    NONE = "None"
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"


@dataclass(frozen=True)
class RiskDriftSignal:
    name: str
    level: RiskDriftLevel
    what_changed: str
    why_it_matters: str
    confidence: int


@dataclass(frozen=True)
class RiskDriftTrigger:
    name: str
    review_area: str
    question: str


@dataclass(frozen=True)
class RiskDriftInput:
    original_profile: InvestorProfile
    current_profile: InvestorProfile
    current_portfolio: Portfolio | None = None
    current_portfolio_analysis: PortfolioAnalysis | None = None
    original_market_regime: MarketRegime | None = None
    current_market_regime: MarketRegimeAnalysis | None = None
    current_market_health: MarketHealthReport | None = None
    current_economic_signals: EconomicSignalAnalysis | None = None
    current_suitability_assessment: SuitabilityAssessment | None = None
    original_portfolio_size: float | None = None
    current_portfolio_size: float | None = None
    original_largest_position_weight: float | None = None
    current_largest_position_weight: float | None = None
    volatility_exposure: str | None = None


@dataclass(frozen=True)
class RiskDriftAssessment:
    overall_drift_level: RiskDriftLevel
    drift_score: int
    drift_summary: str
    signals_detected: tuple[RiskDriftSignal, ...]
    what_changed: tuple[str, ...]
    why_it_matters: tuple[str, ...]
    triggers: tuple[RiskDriftTrigger, ...]
    questions_atlas_should_ask: tuple[str, ...]
    suggested_profile_review_areas: tuple[str, ...]
    confidence: int
    missing_information: tuple[str, ...]


class RiskDriftEngine:
    def assess(self, risk_drift_input: RiskDriftInput) -> RiskDriftAssessment:
        signals = _signals(risk_drift_input)
        missing_information = _missing_information(risk_drift_input)
        score = _drift_score(signals)
        level = _drift_level(score)
        return RiskDriftAssessment(
            overall_drift_level=level,
            drift_score=score,
            drift_summary=_summary(level, signals),
            signals_detected=signals,
            what_changed=_what_changed(signals),
            why_it_matters=_why_it_matters(signals),
            triggers=_triggers(risk_drift_input, signals),
            questions_atlas_should_ask=_questions(risk_drift_input, signals),
            suggested_profile_review_areas=_review_areas(signals),
            confidence=_confidence(risk_drift_input, signals, missing_information),
            missing_information=missing_information,
        )


def render_risk_drift_assessment(assessment: RiskDriftAssessment) -> str:
    lines = [
        "Risk Drift Assessment",
        "",
        f"Overall Drift Level: {assessment.overall_drift_level.value}",
        f"Drift Score: {assessment.drift_score}/100",
        f"Confidence: {assessment.confidence}/100",
        "",
        "Drift Summary",
        assessment.drift_summary,
        "",
        "Signals Detected",
    ]
    for signal in assessment.signals_detected:
        lines.append(
            (
                f"- {signal.name} ({signal.level.value}, {signal.confidence}/100): "
                f"{signal.what_changed} {signal.why_it_matters}"
            )
        )
    lines.extend(
        [
            "",
            "What Changed",
            *_render_list(assessment.what_changed),
            "",
            "Why It Matters",
            *_render_list(assessment.why_it_matters),
            "",
            "Triggers",
        ]
    )
    for trigger in assessment.triggers:
        lines.append(
            f"- {trigger.name}: Review {trigger.review_area}. {trigger.question}"
        )
    lines.extend(
        [
            "",
            "Questions Atlas Should Ask",
            *_render_list(assessment.questions_atlas_should_ask),
            "",
            "Suggested Profile Review Areas",
            *_render_list(assessment.suggested_profile_review_areas),
            "",
            "Missing Information",
            *_render_list(assessment.missing_information),
            "",
            "Research Framing",
            (
                "This identifies possible drift in assumptions only. It is not "
                "personalized financial advice."
            ),
        ]
    )
    return "\n".join(lines)


def _signals(risk_drift_input: RiskDriftInput) -> tuple[RiskDriftSignal, ...]:
    signals: list[RiskDriftSignal] = []
    signals.extend(_profile_signals(risk_drift_input))
    portfolio_growth = _portfolio_growth_signal(risk_drift_input)
    if portfolio_growth:
        signals.append(portfolio_growth)
    concentration = _concentration_signal(risk_drift_input)
    if concentration:
        signals.append(concentration)
    market_regime = _market_regime_signal(risk_drift_input)
    if market_regime:
        signals.append(market_regime)
    market_health = _market_health_signal(risk_drift_input)
    if market_health:
        signals.append(market_health)
    economic = _economic_signal(risk_drift_input)
    if economic:
        signals.append(economic)
    suitability = _suitability_signal(risk_drift_input)
    if suitability:
        signals.append(suitability)
    volatility = _volatility_signal(risk_drift_input)
    if volatility:
        signals.append(volatility)
    return tuple(signals)


def _profile_signals(risk_drift_input: RiskDriftInput) -> tuple[RiskDriftSignal, ...]:
    original = risk_drift_input.original_profile
    current = risk_drift_input.current_profile
    signals: list[RiskDriftSignal] = []
    if original.risk_tolerance != current.risk_tolerance:
        level = _profile_change_level(
            _risk_tolerance_rank(original.risk_tolerance),
            _risk_tolerance_rank(current.risk_tolerance),
        )
        signals.append(
            RiskDriftSignal(
                name="Risk tolerance drift",
                level=level,
                what_changed=(
                    f"Risk tolerance changed from {original.risk_tolerance.value} "
                    f"to {current.risk_tolerance.value}."
                ),
                why_it_matters="Portfolio volatility assumptions may no longer match behavior.",
                confidence=90,
            )
        )
    if original.risk_capacity != current.risk_capacity:
        level = _profile_change_level(
            _risk_capacity_rank(original.risk_capacity),
            _risk_capacity_rank(current.risk_capacity),
        )
        signals.append(
            RiskDriftSignal(
                name="Risk capacity drift",
                level=level,
                what_changed=(
                    f"Risk capacity changed from {original.risk_capacity.value} "
                    f"to {current.risk_capacity.value}."
                ),
                why_it_matters="Financial ability to absorb drawdowns may have changed.",
                confidence=90,
            )
        )
    if original.time_horizon != current.time_horizon:
        level = _profile_change_level(
            _time_horizon_rank(original.time_horizon),
            _time_horizon_rank(current.time_horizon),
        )
        signals.append(
            RiskDriftSignal(
                name="Time horizon drift",
                level=level,
                what_changed=(
                    f"Time horizon changed from {original.time_horizon.value} "
                    f"to {current.time_horizon.value}."
                ),
                why_it_matters="Shorter horizons reduce room to recover from volatility.",
                confidence=88,
            )
        )
    if original.portfolio_purpose != current.portfolio_purpose:
        signals.append(
            RiskDriftSignal(
                name="Portfolio purpose drift",
                level=RiskDriftLevel.MODERATE,
                what_changed=(
                    f"Portfolio purpose changed from {original.portfolio_purpose.value} "
                    f"to {current.portfolio_purpose.value}."
                ),
                why_it_matters="The same holdings can fit one portfolio purpose and not another.",
                confidence=86,
            )
        )
    return tuple(signals)


def _portfolio_growth_signal(
    risk_drift_input: RiskDriftInput,
) -> RiskDriftSignal | None:
    original_size = risk_drift_input.original_portfolio_size
    current_size = risk_drift_input.current_portfolio_size
    if original_size is None or current_size is None or original_size <= 0:
        return None
    growth_ratio = current_size / original_size
    if growth_ratio < 2:
        return None
    level = RiskDriftLevel.HIGH if growth_ratio >= 5 else RiskDriftLevel.MODERATE
    return RiskDriftSignal(
        name="Portfolio size drift",
        level=level,
        what_changed=(
            f"Portfolio size appears to have grown from {original_size:,.0f} "
            f"to {current_size:,.0f}."
        ),
        why_it_matters="A once-small exploratory sleeve can become important enough to review.",
        confidence=82,
    )


def _concentration_signal(risk_drift_input: RiskDriftInput) -> RiskDriftSignal | None:
    current_weight = _current_largest_weight(risk_drift_input)
    original_weight = risk_drift_input.original_largest_position_weight
    if current_weight is None:
        return None
    if current_weight < 0.25 and not _concentration_in_portfolio_analysis(risk_drift_input):
        return None
    level = RiskDriftLevel.HIGH if current_weight >= 0.40 else RiskDriftLevel.MODERATE
    change = f"Largest position is now {current_weight:.1%} of the portfolio."
    if original_weight is not None:
        change = f"Largest position changed from {original_weight:.1%} to {current_weight:.1%}."
    return RiskDriftSignal(
        name="Concentration drift",
        level=level,
        what_changed=change,
        why_it_matters="Concentration can make portfolio risk diverge from profile assumptions.",
        confidence=84,
    )


def _market_regime_signal(risk_drift_input: RiskDriftInput) -> RiskDriftSignal | None:
    current = risk_drift_input.current_market_regime
    original = risk_drift_input.original_market_regime
    if current is None:
        return None
    if (
        original is not None
        and _market_regime_rank(current.regime) <= _market_regime_rank(original)
    ):
        return None
    if current.regime not in {MarketRegime.CORRECTION, MarketRegime.BEAR, MarketRegime.CRISIS}:
        return None
    level = (
        RiskDriftLevel.HIGH
        if current.regime == MarketRegime.CRISIS
        else RiskDriftLevel.MODERATE
    )
    return RiskDriftSignal(
        name="Market regime drift",
        level=level,
        what_changed=f"Market regime is now {current.regime.value}.",
        why_it_matters="Market stress can invalidate calm-market risk assumptions.",
        confidence=current.confidence,
    )


def _market_health_signal(risk_drift_input: RiskDriftInput) -> RiskDriftSignal | None:
    health = risk_drift_input.current_market_health
    if health is None or health.overall_score >= 55:
        return None
    level = RiskDriftLevel.HIGH if health.overall_score < 40 else RiskDriftLevel.MODERATE
    return RiskDriftSignal(
        name="Market health drift",
        level=level,
        what_changed=(
            f"Market health is {health.overall_market_health} with "
            f"{health.overall_risk_level} risk."
        ),
        why_it_matters="Fragile market health can expose portfolios to broader drawdown risk.",
        confidence=78,
    )


def _economic_signal(risk_drift_input: RiskDriftInput) -> RiskDriftSignal | None:
    economics = risk_drift_input.current_economic_signals
    if economics is None or economics.overall_risk_score < 70:
        return None
    level = RiskDriftLevel.HIGH if economics.overall_risk_score >= 85 else RiskDriftLevel.MODERATE
    return RiskDriftSignal(
        name="Economic risk drift",
        level=level,
        what_changed=(
            f"Economic risk score is {economics.overall_risk_score}/100 "
            f"with {economics.overall_economic_health} health."
        ),
        why_it_matters="Macro and credit risks can change the suitability of risk exposure.",
        confidence=76,
    )


def _suitability_signal(risk_drift_input: RiskDriftInput) -> RiskDriftSignal | None:
    suitability = risk_drift_input.current_suitability_assessment
    if suitability is None:
        return None
    if suitability.overall_suitability not in {
        OverallSuitability.NEUTRAL,
        OverallSuitability.POOR_FIT,
    }:
        return None
    level = (
        RiskDriftLevel.HIGH
        if suitability.overall_suitability == OverallSuitability.POOR_FIT
        else RiskDriftLevel.MODERATE
    )
    return RiskDriftSignal(
        name="Suitability drift",
        level=level,
        what_changed=(
            f"Current suitability assessment is {suitability.overall_suitability.value}."
        ),
        why_it_matters="A lower compatibility assessment may indicate profile assumptions changed.",
        confidence=suitability.confidence,
    )


def _volatility_signal(risk_drift_input: RiskDriftInput) -> RiskDriftSignal | None:
    exposure = (risk_drift_input.volatility_exposure or "").strip().lower()
    current = risk_drift_input.current_profile
    if exposure not in {"high", "elevated", "aggressive"}:
        return None
    if _profile_accepts_high_volatility(current):
        return RiskDriftSignal(
            name="Volatility exposure",
            level=RiskDriftLevel.LOW,
            what_changed="Volatility exposure is high, but the current profile accepts it.",
            why_it_matters=(
                "Aggressive portfolios can remain aligned when capacity and horizon fit."
            ),
            confidence=74,
        )
    return RiskDriftSignal(
        name="Volatility exposure",
        level=RiskDriftLevel.MODERATE,
        what_changed="Volatility exposure appears high relative to the current profile.",
        why_it_matters="Atlas would ask whether the original risk assumptions still apply.",
        confidence=74,
    )


def _drift_score(signals: tuple[RiskDriftSignal, ...]) -> int:
    if not signals:
        return 0
    score = sum(_level_points(signal.level) for signal in signals)
    return clamp_score(score)


def _drift_level(score: int) -> RiskDriftLevel:
    if score >= 70:
        return RiskDriftLevel.HIGH
    if score >= 40:
        return RiskDriftLevel.MODERATE
    if score > 0:
        return RiskDriftLevel.LOW
    return RiskDriftLevel.NONE


def _summary(
    level: RiskDriftLevel,
    signals: tuple[RiskDriftSignal, ...],
) -> str:
    if level == RiskDriftLevel.NONE:
        return "No meaningful drift was detected from the supplied information."
    if level == RiskDriftLevel.HIGH:
        return (
            "Your current situation appears to have changed materially since this "
            "profile was created."
        )
    return "Atlas would ask whether the original risk assumptions still apply."


def _what_changed(signals: tuple[RiskDriftSignal, ...]) -> tuple[str, ...]:
    if not signals:
        return ("No meaningful changes were detected.",)
    return tuple(signal.what_changed for signal in signals)


def _why_it_matters(signals: tuple[RiskDriftSignal, ...]) -> tuple[str, ...]:
    if not signals:
        return ("Current assumptions appear consistent with the supplied profile context.",)
    return tuple(signal.why_it_matters for signal in signals)


def _questions(
    risk_drift_input: RiskDriftInput,
    signals: tuple[RiskDriftSignal, ...],
) -> tuple[str, ...]:
    questions = [
        "Do the original risk assumptions still describe the investor today?",
        "Has the portfolio purpose changed since the original profile was created?",
        "Would the investor respond differently to a large drawdown now?",
    ]
    names = {signal.name for signal in signals}
    if "Concentration drift" in names:
        questions.append("Is the current position concentration intentional and still acceptable?")
    if "Portfolio size drift" in names:
        questions.append("Should this portfolio still be treated as the same allocation sleeve?")
    if risk_drift_input.current_portfolio is None:
        questions.append("What are the current position weights and sector exposures?")
    return tuple(questions)


def _triggers(
    risk_drift_input: RiskDriftInput,
    signals: tuple[RiskDriftSignal, ...],
) -> tuple[RiskDriftTrigger, ...]:
    if not signals:
        return (
            RiskDriftTrigger(
                name="No material drift",
                review_area="Profile assumptions",
                question="Should the profile review cadence remain unchanged?",
            ),
        )
    triggers = [
        RiskDriftTrigger(
            name=signal.name,
            review_area=_review_area_for_signal(signal.name),
            question=_trigger_question(signal.name, risk_drift_input),
        )
        for signal in signals
    ]
    return tuple(triggers)


def _review_areas(signals: tuple[RiskDriftSignal, ...]) -> tuple[str, ...]:
    review_areas = []
    for signal in signals:
        review_areas.append(_review_area_for_signal(signal.name))
    if not review_areas:
        return ("No immediate profile review area was detected.",)
    return tuple(dict.fromkeys(review_areas))


def _missing_information(risk_drift_input: RiskDriftInput) -> tuple[str, ...]:
    missing = []
    if risk_drift_input.original_portfolio_size is None:
        missing.append("Original portfolio size is not supplied.")
    if risk_drift_input.current_portfolio_size is None:
        missing.append("Current portfolio size is not supplied.")
    if (
        risk_drift_input.current_portfolio is None
        and risk_drift_input.current_portfolio_analysis is None
    ):
        missing.append("Current portfolio concentration context is not supplied.")
    if risk_drift_input.original_market_regime is None:
        missing.append("Original market regime assumption is not supplied.")
    if risk_drift_input.current_suitability_assessment is None:
        missing.append("Current suitability assessment is not supplied.")
    return tuple(missing)


def _confidence(
    risk_drift_input: RiskDriftInput,
    signals: tuple[RiskDriftSignal, ...],
    missing_information: tuple[str, ...],
) -> int:
    confidence = 58
    confidence += min(len(signals) * 4, 18)
    if risk_drift_input.current_portfolio is not None:
        confidence += 8
    if risk_drift_input.current_market_regime is not None:
        confidence += 6
    if risk_drift_input.current_market_health is not None:
        confidence += 5
    if risk_drift_input.current_economic_signals is not None:
        confidence += 5
    if risk_drift_input.current_suitability_assessment is not None:
        confidence += 6
    confidence -= len(missing_information) * 4
    return clamp_score(confidence)


def _profile_change_level(original_rank: int, current_rank: int) -> RiskDriftLevel:
    delta = abs(current_rank - original_rank)
    if delta >= 2:
        return RiskDriftLevel.HIGH
    return RiskDriftLevel.MODERATE


def _risk_tolerance_rank(value: RiskTolerance) -> int:
    return {
        RiskTolerance.CONSERVATIVE: 0,
        RiskTolerance.BALANCED: 1,
        RiskTolerance.GROWTH: 2,
        RiskTolerance.AGGRESSIVE: 3,
    }[value]


def _risk_capacity_rank(value: RiskCapacity) -> int:
    return {
        RiskCapacity.LOW: 0,
        RiskCapacity.MEDIUM: 1,
        RiskCapacity.HIGH: 2,
    }[value]


def _time_horizon_rank(value: TimeHorizon) -> int:
    return {
        TimeHorizon.SHORT: 0,
        TimeHorizon.MEDIUM: 1,
        TimeHorizon.LONG: 2,
    }[value]


def _market_regime_rank(value: MarketRegime) -> int:
    return {
        MarketRegime.BULL: 0,
        MarketRegime.NEUTRAL: 1,
        MarketRegime.CORRECTION: 2,
        MarketRegime.BEAR: 3,
        MarketRegime.CRISIS: 4,
    }[value]


def _current_largest_weight(risk_drift_input: RiskDriftInput) -> float | None:
    if risk_drift_input.current_largest_position_weight is not None:
        return risk_drift_input.current_largest_position_weight
    portfolio = risk_drift_input.current_portfolio
    if portfolio is None:
        return None
    return max((position.weight for position in portfolio.positions), default=0.0)


def _concentration_in_portfolio_analysis(risk_drift_input: RiskDriftInput) -> bool:
    analysis = risk_drift_input.current_portfolio_analysis
    if analysis is None:
        return False
    return any(
        signal.score < 55
        for signal in (
            analysis.sector_concentration,
            analysis.country_concentration,
            analysis.market_cap_concentration,
            analysis.overlap_with_existing_holdings,
        )
    )


def _profile_accepts_high_volatility(profile: InvestorProfile) -> bool:
    return (
        profile.risk_capacity == RiskCapacity.HIGH
        and profile.risk_tolerance in {RiskTolerance.GROWTH, RiskTolerance.AGGRESSIVE}
        and profile.time_horizon == TimeHorizon.LONG
    ) or profile.portfolio_purpose in {
        PortfolioPurpose.EXPLORATION_PORTFOLIO,
        PortfolioPurpose.HIGH_CONVICTION_PORTFOLIO,
    }


def _level_points(level: RiskDriftLevel) -> int:
    return {
        RiskDriftLevel.NONE: 0,
        RiskDriftLevel.LOW: 12,
        RiskDriftLevel.MODERATE: 26,
        RiskDriftLevel.HIGH: 42,
    }[level]


def _review_area_for_signal(signal_name: str) -> str:
    mapping = {
        "Risk tolerance drift": "Risk tolerance",
        "Risk capacity drift": "Risk capacity",
        "Time horizon drift": "Time horizon",
        "Portfolio purpose drift": "Portfolio purpose",
        "Portfolio size drift": "Portfolio role and allocation sleeve",
        "Concentration drift": "Position concentration limits",
        "Market regime drift": "Market environment assumptions",
        "Market health drift": "Market risk assumptions",
        "Economic risk drift": "Economic and credit risk assumptions",
        "Suitability drift": "Profile compatibility",
        "Volatility exposure": "Volatility tolerance",
    }
    return mapping.get(signal_name, signal_name)


def _trigger_question(signal_name: str, risk_drift_input: RiskDriftInput) -> str:
    questions = {
        "Risk tolerance drift": "Does the current tolerance better describe future behavior?",
        "Risk capacity drift": "Has the investor's ability to absorb losses changed materially?",
        "Time horizon drift": "Should the portfolio be reclassified for a shorter horizon?",
        "Portfolio purpose drift": "Does the original portfolio purpose still apply?",
        "Portfolio size drift": "Has this portfolio become too important for its original role?",
        "Concentration drift": "Is the current concentration intentional and still acceptable?",
        "Market regime drift": "Were original risk assumptions based on calmer market conditions?",
        "Market health drift": "Should fragile market conditions change the review cadence?",
        "Economic risk drift": "Are credit and macro risks now more important to the profile?",
        "Suitability drift": "What profile assumption explains the lower compatibility reading?",
        "Volatility exposure": "Does the investor still explicitly accept this volatility?",
    }
    if signal_name == "Volatility exposure" and _profile_accepts_high_volatility(
        risk_drift_input.current_profile
    ):
        return "Is high volatility still intentionally accepted within this portfolio purpose?"
    return questions.get(signal_name, "Should this assumption be reviewed?")


def _render_list(items: tuple[str, ...]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]

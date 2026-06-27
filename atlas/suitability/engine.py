from dataclasses import dataclass
from enum import Enum

from atlas.analysis.engine import InvestmentReport
from atlas.analysis.portfolio import Portfolio, PortfolioAnalysis
from atlas.analysis.scores import clamp_score
from atlas.intelligence import IntelligenceReport
from atlas.profile import (
    InvestmentGoal,
    InvestorProfile,
    PortfolioPurpose,
    RiskCapacity,
    RiskPreference,
    RiskTolerance,
    TimeHorizon,
)
from atlas.themes import ThemeAnalysis


class OverallSuitability(str, Enum):
    EXCELLENT_FIT = "Excellent Fit"
    GOOD_FIT = "Good Fit"
    NEUTRAL = "Neutral"
    POOR_FIT = "Poor Fit"


@dataclass(frozen=True)
class SuitabilityFactor:
    name: str
    score: int
    reasoning: str


@dataclass(frozen=True)
class SuitabilityMismatch:
    name: str
    severity: str
    reasoning: str


@dataclass(frozen=True)
class SuitabilityInput:
    investor_profile: InvestorProfile
    ticker: str | None = None
    investment_report: InvestmentReport | None = None
    portfolio: Portfolio | None = None
    portfolio_analysis: PortfolioAnalysis | None = None
    theme_analysis: ThemeAnalysis | None = None
    intelligence_report: IntelligenceReport | None = None
    preferred_investment_style: str | None = None
    volatility: str | None = None
    business_quality: int | None = None
    valuation_sensitivity: str | None = None
    concentration_impact: str | None = None
    cyclicality: str | None = None
    leverage: str | None = None
    sector_exposure: str | None = None
    geographic_exposure: str | None = None


@dataclass(frozen=True)
class SuitabilityAssessment:
    subject: str
    overall_suitability: OverallSuitability
    suitability_score: int
    confidence: int
    why_it_fits: tuple[str, ...]
    why_it_may_not_fit: tuple[str, ...]
    main_strengths: tuple[SuitabilityFactor, ...]
    main_concerns: tuple[SuitabilityMismatch, ...]
    assumptions: tuple[str, ...]
    missing_information: tuple[str, ...]
    questions_before_higher_confidence: tuple[str, ...]


class SuitabilityEngine:
    def assess(self, suitability_input: SuitabilityInput) -> SuitabilityAssessment:
        profile = suitability_input.investor_profile
        characteristics = _derive_characteristics(suitability_input)
        factors = _fit_factors(profile, suitability_input, characteristics)
        mismatches = _mismatches(profile, suitability_input, characteristics)
        score = _suitability_score(factors, mismatches)
        missing_information = _missing_information(suitability_input)
        confidence = _confidence(suitability_input, missing_information)
        return SuitabilityAssessment(
            subject=_subject(suitability_input),
            overall_suitability=_overall_suitability(score),
            suitability_score=score,
            confidence=confidence,
            why_it_fits=_why_it_fits(factors),
            why_it_may_not_fit=_why_it_may_not_fit(mismatches),
            main_strengths=tuple(sorted(factors, key=lambda item: item.score, reverse=True)[:5]),
            main_concerns=mismatches[:5],
            assumptions=_assumptions(profile, suitability_input, characteristics),
            missing_information=missing_information,
            questions_before_higher_confidence=_questions(profile, suitability_input),
        )


def render_suitability_assessment(assessment: SuitabilityAssessment) -> str:
    lines = [
        "Suitability Assessment",
        "",
        f"Subject: {assessment.subject}",
        f"Overall Suitability: {assessment.overall_suitability.value}",
        f"Suitability Score: {assessment.suitability_score}/100",
        f"Confidence: {assessment.confidence}/100",
        "",
        "Compatibility View",
        _compatibility_language(assessment.overall_suitability),
        "",
        "Why It Fits",
        *_render_list(assessment.why_it_fits),
        "",
        "Why It May Not Fit",
        *_render_list(assessment.why_it_may_not_fit),
        "",
        "Main Strengths",
    ]
    for factor in assessment.main_strengths:
        lines.append(f"- {factor.name} ({factor.score}/100): {factor.reasoning}")
    lines.extend(["", "Main Concerns"])
    for mismatch in assessment.main_concerns:
        lines.append(f"- {mismatch.name} ({mismatch.severity}): {mismatch.reasoning}")
    lines.extend(
        [
            "",
            "Assumptions",
            *_render_list(assessment.assumptions),
            "",
            "Missing Information",
            *_render_list(assessment.missing_information),
            "",
            "Questions Atlas Would Ask Before Increasing Confidence",
            *_render_list(assessment.questions_before_higher_confidence),
            "",
            "Research Framing",
            (
                "This evaluates profile compatibility only. It does not judge investment "
                "merit or provide personalized financial advice."
            ),
        ]
    )
    return "\n".join(lines)


def _derive_characteristics(suitability_input: SuitabilityInput) -> dict[str, str | int]:
    report = suitability_input.investment_report
    portfolio = suitability_input.portfolio
    portfolio_analysis = suitability_input.portfolio_analysis

    quality = suitability_input.business_quality
    if quality is None and report is not None:
        quality = report.quality.score
    if quality is None and portfolio is not None:
        quality = round(_weighted_average(portfolio, "quality_score"))

    risk_profile_score = report.risk.score if report is not None else None
    if risk_profile_score is None and portfolio is not None:
        risk_profile_score = round(_weighted_average(portfolio, "risk_score"))

    valuation_score = report.valuation.score if report is not None else None
    volatility = suitability_input.volatility or _volatility_from_risk(risk_profile_score)
    valuation_sensitivity = (
        suitability_input.valuation_sensitivity
        or _valuation_sensitivity(valuation_score, volatility)
    )
    concentration_impact = suitability_input.concentration_impact
    if concentration_impact is None:
        concentration_impact = _concentration_impact(portfolio, portfolio_analysis)

    return {
        "volatility": volatility,
        "business_quality": quality if quality is not None else "unknown",
        "valuation_sensitivity": valuation_sensitivity,
        "concentration_impact": concentration_impact,
        "cyclicality": suitability_input.cyclicality or _cyclicality(suitability_input),
        "leverage": suitability_input.leverage or _leverage(report),
        "sector_exposure": suitability_input.sector_exposure or _sector_exposure(portfolio),
        "geographic_exposure": (
            suitability_input.geographic_exposure or _geographic_exposure(portfolio)
        ),
        "risk_profile_score": risk_profile_score if risk_profile_score is not None else "unknown",
    }


def _fit_factors(
    profile: InvestorProfile,
    suitability_input: SuitabilityInput,
    characteristics: dict[str, str | int],
) -> tuple[SuitabilityFactor, ...]:
    factors: list[SuitabilityFactor] = []
    quality = characteristics["business_quality"]
    risk_score = characteristics["risk_profile_score"]
    volatility = str(characteristics["volatility"]).lower()

    if isinstance(quality, int) and quality >= 80:
        factors.append(
            SuitabilityFactor(
                name="Business quality",
                score=quality,
                reasoning="High business quality supports profiles that value durability.",
            )
        )
    if profile.time_horizon == TimeHorizon.LONG:
        factors.append(
            SuitabilityFactor(
                name="Time horizon",
                score=86,
                reasoning="A long horizon gives the investor more room to absorb volatility.",
            )
        )
    if profile.risk_capacity == RiskCapacity.HIGH:
        factors.append(
            SuitabilityFactor(
                name="Risk capacity",
                score=82,
                reasoning="High risk capacity improves compatibility with uncertain outcomes.",
            )
        )
    if _accepts_volatility(profile) and volatility in {"medium", "high"}:
        factors.append(
            SuitabilityFactor(
                name="Accepted volatility",
                score=84,
                reasoning=(
                    "The stated profile can tolerate volatility when the portfolio purpose "
                    "is exploratory, growth-oriented, or high conviction."
                ),
            )
        )
    if _is_exploration_or_high_conviction(profile) and _is_higher_risk(risk_score):
        factors.append(
            SuitabilityFactor(
                name="Purpose alignment",
                score=80,
                reasoning=(
                    "Higher-risk exposure can be compatible with an exploration or high "
                    "conviction sleeve when capacity and horizon support it."
                ),
            )
        )
    if suitability_input.theme_analysis is not None:
        factors.append(
            SuitabilityFactor(
                name="Theme context",
                score=suitability_input.theme_analysis.confidence,
                reasoning=(
                    "Theme analysis supplies structural context rather than a standalone "
                    "investment conclusion."
                ),
            )
        )
    if isinstance(risk_score, int) and risk_score >= 70:
        factors.append(
            SuitabilityFactor(
                name="Risk profile quality",
                score=risk_score,
                reasoning="The risk profile score appears compatible with mainstream use cases.",
            )
        )
    return tuple(factors)


def _mismatches(
    profile: InvestorProfile,
    suitability_input: SuitabilityInput,
    characteristics: dict[str, str | int],
) -> tuple[SuitabilityMismatch, ...]:
    mismatches: list[SuitabilityMismatch] = []
    risk_score = characteristics["risk_profile_score"]
    volatility = str(characteristics["volatility"]).lower()
    valuation_sensitivity = str(characteristics["valuation_sensitivity"]).lower()
    concentration_impact = str(characteristics["concentration_impact"]).lower()
    quality = characteristics["business_quality"]

    if profile.time_horizon == TimeHorizon.SHORT and volatility in {"medium", "high"}:
        mismatches.append(
            SuitabilityMismatch(
                name="Time horizon mismatch",
                severity="High",
                reasoning="A short horizon conflicts with material volatility.",
            )
        )
    if profile.risk_capacity == RiskCapacity.LOW and _is_higher_risk(risk_score):
        mismatches.append(
            SuitabilityMismatch(
                name="Risk capacity mismatch",
                severity="High",
                reasoning="Low risk capacity conflicts with a higher-risk opportunity.",
            )
        )
    if profile.risk_tolerance == RiskTolerance.CONSERVATIVE and volatility == "high":
        mismatches.append(
            SuitabilityMismatch(
                name="Risk tolerance mismatch",
                severity="High",
                reasoning="Conservative tolerance conflicts with high volatility.",
            )
        )
    if _capital_preservation_profile(profile) and valuation_sensitivity == "high":
        mismatches.append(
            SuitabilityMismatch(
                name="Valuation sensitivity",
                severity="Medium",
                reasoning="Capital preservation profiles are less compatible with valuation risk.",
            )
        )
    if "high" in concentration_impact:
        mismatches.append(
            SuitabilityMismatch(
                name="Concentration impact",
                severity="Medium",
                reasoning="The opportunity may increase existing concentration exposure.",
            )
        )
    if (
        profile.portfolio_purpose == PortfolioPurpose.CORE_PORTFOLIO
        and isinstance(quality, int)
        and quality < 70
    ):
        mismatches.append(
            SuitabilityMismatch(
                name="Core quality threshold",
                severity="Medium",
                reasoning="Core portfolios generally require stronger business quality.",
            )
        )
    if suitability_input.investment_report is None and suitability_input.portfolio is None:
        mismatches.append(
            SuitabilityMismatch(
                name="Investment characteristics unavailable",
                severity="Medium",
                reasoning="Atlas has limited facts about the opportunity being evaluated.",
            )
        )
    return tuple(mismatches)


def _suitability_score(
    factors: tuple[SuitabilityFactor, ...],
    mismatches: tuple[SuitabilityMismatch, ...],
) -> int:
    base_score = 55
    factor_lift = round(sum((factor.score - 50) * 0.18 for factor in factors))
    mismatch_penalty = sum(_severity_penalty(mismatch.severity) for mismatch in mismatches)
    return clamp_score(base_score + factor_lift - mismatch_penalty)


def _overall_suitability(score: int) -> OverallSuitability:
    if score >= 82:
        return OverallSuitability.EXCELLENT_FIT
    if score >= 68:
        return OverallSuitability.GOOD_FIT
    if score >= 50:
        return OverallSuitability.NEUTRAL
    return OverallSuitability.POOR_FIT


def _confidence(
    suitability_input: SuitabilityInput,
    missing_information: tuple[str, ...],
) -> int:
    confidence = 55
    if suitability_input.investment_report is not None:
        confidence += 12
    if suitability_input.portfolio is not None or suitability_input.portfolio_analysis is not None:
        confidence += 10
    if suitability_input.theme_analysis is not None:
        confidence += 6
    if suitability_input.intelligence_report is not None:
        confidence += 8
    confidence -= len(missing_information) * 4
    return clamp_score(confidence)


def _missing_information(suitability_input: SuitabilityInput) -> tuple[str, ...]:
    missing: list[str] = []
    if suitability_input.preferred_investment_style is None:
        missing.append("Preferred investment style has not been explicitly stated.")
    if suitability_input.investment_report is None and suitability_input.portfolio is None:
        missing.append("Investment characteristics are incomplete.")
    if suitability_input.portfolio_analysis is None and suitability_input.portfolio is None:
        missing.append("Concentration impact is estimated without full portfolio context.")
    if suitability_input.volatility is None:
        missing.append("Volatility is inferred from deterministic risk scoring.")
    if suitability_input.cyclicality is None:
        missing.append("Cyclicality is inferred from available theme or company context.")
    if suitability_input.leverage is None:
        missing.append("Leverage is inferred from financial strength scoring.")
    return tuple(missing)


def _assumptions(
    profile: InvestorProfile,
    suitability_input: SuitabilityInput,
    characteristics: dict[str, str | int],
) -> tuple[str, ...]:
    style = suitability_input.preferred_investment_style or _style_from_profile(profile)
    assumptions = [
        f"Preferred investment style is treated as {style}.",
        f"Volatility is treated as {characteristics['volatility']}.",
        f"Valuation sensitivity is treated as {characteristics['valuation_sensitivity']}.",
        f"Concentration impact is treated as {characteristics['concentration_impact']}.",
        f"Cyclicality is treated as {characteristics['cyclicality']}.",
        f"Leverage is treated as {characteristics['leverage']}.",
    ]
    if suitability_input.intelligence_report is not None:
        assumptions.append("Intelligence context is used as synthesis context only.")
    return tuple(assumptions)


def _questions(
    profile: InvestorProfile,
    suitability_input: SuitabilityInput,
) -> tuple[str, ...]:
    questions = [
        "What maximum drawdown would the investor tolerate without changing course?",
        "Is this intended for the core portfolio or a limited satellite sleeve?",
        "How much near-term liquidity must remain outside investment capital?",
    ]
    if profile.portfolio_purpose == PortfolioPurpose.HIGH_CONVICTION_PORTFOLIO:
        questions.append("What position-size limit defines acceptable concentration?")
    if suitability_input.portfolio is None and suitability_input.portfolio_analysis is None:
        questions.append("What are the current sector, country, and position weights?")
    return tuple(questions)


def _why_it_fits(factors: tuple[SuitabilityFactor, ...]) -> tuple[str, ...]:
    if not factors:
        return ("Atlas does not have enough positive fit evidence yet.",)
    return tuple(factor.reasoning for factor in factors[:5])


def _why_it_may_not_fit(
    mismatches: tuple[SuitabilityMismatch, ...],
) -> tuple[str, ...]:
    if not mismatches:
        return ("No major profile conflicts were detected from the supplied information.",)
    return tuple(mismatch.reasoning for mismatch in mismatches[:5])


def _subject(suitability_input: SuitabilityInput) -> str:
    if suitability_input.investment_report is not None:
        return suitability_input.investment_report.company
    if suitability_input.portfolio is not None:
        return "Portfolio"
    if suitability_input.ticker:
        return suitability_input.ticker.upper()
    return "Investment opportunity"


def _compatibility_language(suitability: OverallSuitability) -> str:
    if suitability in {OverallSuitability.EXCELLENT_FIT, OverallSuitability.GOOD_FIT}:
        return "This investment appears compatible with the stated investor profile."
    if suitability == OverallSuitability.POOR_FIT:
        return "This investment appears inconsistent with the stated objectives."
    return "This investment has mixed compatibility with the stated investor profile."


def _volatility_from_risk(risk_score: int | None) -> str:
    if risk_score is None:
        return "unknown"
    if risk_score >= 75:
        return "low"
    if risk_score >= 55:
        return "medium"
    return "high"


def _valuation_sensitivity(valuation_score: int | None, volatility: str) -> str:
    if valuation_score is None:
        return "unknown"
    if valuation_score < 55 or volatility == "high":
        return "high"
    if valuation_score < 75:
        return "medium"
    return "low"


def _concentration_impact(
    portfolio: Portfolio | None,
    portfolio_analysis: PortfolioAnalysis | None,
) -> str:
    if portfolio_analysis is not None:
        signals = (
            portfolio_analysis.sector_concentration,
            portfolio_analysis.country_concentration,
            portfolio_analysis.market_cap_concentration,
            portfolio_analysis.overlap_with_existing_holdings,
        )
        if any(signal.score < 45 for signal in signals):
            return "high"
        if any(signal.score < 70 for signal in signals):
            return "medium"
        return "low"
    if portfolio is not None:
        max_sector = _max_weight(portfolio, "sector")
        max_country = _max_weight(portfolio, "country")
        if max_sector > 0.40 or max_country > 0.70:
            return "high"
        if max_sector > 0.25 or max_country > 0.55:
            return "medium"
        return "low"
    return "unknown"


def _cyclicality(suitability_input: SuitabilityInput) -> str:
    report = suitability_input.investment_report
    if report is not None and report.financial_strength.score >= 80:
        return "moderate"
    if suitability_input.theme_analysis is not None:
        return "theme-dependent"
    return "unknown"


def _leverage(report: InvestmentReport | None) -> str:
    if report is None:
        return "unknown"
    if report.financial_strength.score >= 80:
        return "low concern"
    if report.financial_strength.score >= 60:
        return "moderate concern"
    return "high concern"


def _sector_exposure(portfolio: Portfolio | None) -> str:
    if portfolio is None:
        return "unknown"
    return _top_exposure(portfolio, "sector")


def _geographic_exposure(portfolio: Portfolio | None) -> str:
    if portfolio is None:
        return "unknown"
    return _top_exposure(portfolio, "country")


def _style_from_profile(profile: InvestorProfile) -> str:
    if profile.portfolio_purpose == PortfolioPurpose.INCOME_PORTFOLIO:
        return "income-oriented"
    if profile.portfolio_purpose == PortfolioPurpose.EXPLORATION_PORTFOLIO:
        return "exploratory"
    if profile.portfolio_purpose == PortfolioPurpose.HIGH_CONVICTION_PORTFOLIO:
        return "high conviction"
    if profile.risk_preference in {RiskPreference.GROWTH, RiskPreference.AGGRESSIVE}:
        return "growth-oriented"
    return "balanced"


def _accepts_volatility(profile: InvestorProfile) -> bool:
    return (
        profile.time_horizon == TimeHorizon.LONG
        and profile.risk_capacity == RiskCapacity.HIGH
        and profile.risk_tolerance in {RiskTolerance.GROWTH, RiskTolerance.AGGRESSIVE}
    ) or _is_exploration_or_high_conviction(profile)


def _is_exploration_or_high_conviction(profile: InvestorProfile) -> bool:
    return profile.portfolio_purpose in {
        PortfolioPurpose.EXPLORATION_PORTFOLIO,
        PortfolioPurpose.HIGH_CONVICTION_PORTFOLIO,
    }


def _is_higher_risk(risk_score: int | str) -> bool:
    return risk_score == "unknown" or (isinstance(risk_score, int) and risk_score < 60)


def _capital_preservation_profile(profile: InvestorProfile) -> bool:
    return (
        InvestmentGoal.CAPITAL_PRESERVATION in profile.investment_goals
        or profile.portfolio_purpose == PortfolioPurpose.CORE_PORTFOLIO
        and profile.risk_preference == RiskPreference.CONSERVATIVE
    )


def _severity_penalty(severity: str) -> int:
    if severity == "High":
        return 24
    if severity == "Medium":
        return 14
    return 8


def _weighted_average(portfolio: Portfolio, field: str) -> float:
    total_weight = sum(position.weight for position in portfolio.positions)
    if total_weight <= 0:
        return 0.0
    total = sum(getattr(position, field) * position.weight for position in portfolio.positions)
    return total / total_weight


def _max_weight(portfolio: Portfolio, field: str) -> float:
    weights: dict[str, float] = {}
    for position in portfolio.positions:
        value = str(getattr(position, field))
        weights[value] = weights.get(value, 0.0) + position.weight
    return max(weights.values(), default=0.0)


def _top_exposure(portfolio: Portfolio, field: str) -> str:
    weights: dict[str, float] = {}
    for position in portfolio.positions:
        value = str(getattr(position, field))
        weights[value] = weights.get(value, 0.0) + position.weight
    if not weights:
        return "unknown"
    value, weight = max(weights.items(), key=lambda item: item[1])
    return f"{value} at {weight:.1%}"


def _render_list(items: tuple[str, ...]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]

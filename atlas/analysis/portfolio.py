import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from atlas.analysis.scores import clamp_score
from atlas.providers.base import CompanyDataProvider


@dataclass(frozen=True)
class PortfolioPosition:
    ticker: str
    company: str
    sector: str
    country: str
    market_cap: float
    weight: float
    quality_score: int
    risk_score: int


@dataclass(frozen=True)
class Portfolio:
    positions: tuple[PortfolioPosition, ...]

    @classmethod
    def from_json_file(cls, path: Path) -> "Portfolio":
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        return cls.from_mapping(payload)

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "Portfolio":
        raw_positions = payload.get("positions")
        if not isinstance(raw_positions, list) or not raw_positions:
            raise ValueError("Portfolio JSON must contain a non-empty positions list.")
        return cls(positions=tuple(_position_from_mapping(item) for item in raw_positions))


@dataclass(frozen=True)
class PortfolioSignal:
    score: int
    reasoning: str


class PortfolioRecommendation(str, Enum):
    STRONG_ADD = "Strong Add"
    ADD = "Add"
    NEUTRAL = "Neutral"
    REDUCE = "Reduce"
    AVOID = "Avoid"


@dataclass(frozen=True)
class PortfolioAnalysis:
    company: str
    ticker: str
    portfolio_score: int
    recommendation: PortfolioRecommendation
    diversification_impact: PortfolioSignal
    sector_concentration: PortfolioSignal
    country_concentration: PortfolioSignal
    market_cap_concentration: PortfolioSignal
    overlap_with_existing_holdings: PortfolioSignal
    expected_portfolio_quality_impact: PortfolioSignal
    expected_portfolio_risk_impact: PortfolioSignal
    final_reasoning: str


@dataclass(frozen=True)
class CompanyPortfolioProfile:
    ticker: str
    company: str
    sector: str
    country: str
    market_cap: float
    quality_score: int
    risk_score: int


DEFAULT_TARGET_WEIGHT = 0.05


class PortfolioIntelligenceEngine:
    def analyze(
        self,
        portfolio: Portfolio,
        target: CompanyPortfolioProfile,
        target_weight: float = DEFAULT_TARGET_WEIGHT,
    ) -> PortfolioAnalysis:
        normalized_weight = _normalize_weight(target_weight)
        diversification = _diversification_impact(portfolio, target, normalized_weight)
        sector = _sector_concentration(portfolio, target, normalized_weight)
        country = _country_concentration(portfolio, target, normalized_weight)
        market_cap = _market_cap_concentration(portfolio, target, normalized_weight)
        overlap = _overlap_with_existing_holdings(portfolio, target)
        quality = _expected_quality_impact(portfolio, target, normalized_weight)
        risk = _expected_risk_impact(portfolio, target, normalized_weight)
        portfolio_score = _aggregate_portfolio_score(
            diversification=diversification,
            sector=sector,
            country=country,
            market_cap=market_cap,
            overlap=overlap,
            quality=quality,
            risk=risk,
        )
        recommendation = _recommend(portfolio_score)
        return PortfolioAnalysis(
            company=target.company,
            ticker=target.ticker,
            portfolio_score=portfolio_score,
            recommendation=recommendation,
            diversification_impact=diversification,
            sector_concentration=sector,
            country_concentration=country,
            market_cap_concentration=market_cap,
            overlap_with_existing_holdings=overlap,
            expected_portfolio_quality_impact=quality,
            expected_portfolio_risk_impact=risk,
            final_reasoning=_final_reasoning(
                target,
                portfolio_score,
                recommendation,
                sector,
                overlap,
                quality,
                risk,
            ),
        )

    def analyze_ticker(
        self,
        portfolio: Portfolio,
        ticker: str,
        provider: CompanyDataProvider,
        target_weight: float = DEFAULT_TARGET_WEIGHT,
    ) -> PortfolioAnalysis:
        return self.analyze(
            portfolio=portfolio,
            target=provider.get_portfolio_profile(ticker),
            target_weight=target_weight,
        )


def get_mock_company_portfolio_profile(ticker: str) -> CompanyPortfolioProfile:
    from atlas.providers.mock import MockCompanyAnalysisProvider

    return MockCompanyAnalysisProvider().get_portfolio_profile(ticker)


def render_portfolio_analysis(analysis: PortfolioAnalysis) -> str:
    return "\n".join(
        [
            "Portfolio Analysis",
            "",
            f"Company: {analysis.company} ({analysis.ticker})",
            f"Portfolio Recommendation: {analysis.recommendation.value}",
            _score_line("Portfolio Score", analysis.portfolio_score),
            "",
            "Diversification Impact",
            _signal_line(analysis.diversification_impact),
            "",
            "Sector Concentration",
            _signal_line(analysis.sector_concentration),
            "",
            "Country Concentration",
            _signal_line(analysis.country_concentration),
            "",
            "Market Cap Concentration",
            _signal_line(analysis.market_cap_concentration),
            "",
            "Portfolio Risk Impact",
            _signal_line(analysis.expected_portfolio_risk_impact),
            "",
            "Portfolio Quality Impact",
            _signal_line(analysis.expected_portfolio_quality_impact),
            "",
            "Overlap Analysis",
            _signal_line(analysis.overlap_with_existing_holdings),
            "",
            "Final Reasoning",
            analysis.final_reasoning,
        ]
    )


def _position_from_mapping(payload: dict[str, Any]) -> PortfolioPosition:
    required_fields = (
        "ticker",
        "company",
        "sector",
        "country",
        "market_cap",
        "weight",
        "quality_score",
        "risk_score",
    )
    missing = [field for field in required_fields if field not in payload]
    if missing:
        raise ValueError(f"Portfolio position is missing required fields: {', '.join(missing)}")
    return PortfolioPosition(
        ticker=str(payload["ticker"]).upper(),
        company=str(payload["company"]),
        sector=str(payload["sector"]),
        country=str(payload["country"]),
        market_cap=float(payload["market_cap"]),
        weight=_normalize_weight(float(payload["weight"])),
        quality_score=clamp_score(round(float(payload["quality_score"]))),
        risk_score=clamp_score(round(float(payload["risk_score"]))),
    )


def _diversification_impact(
    portfolio: Portfolio,
    target: CompanyPortfolioProfile,
    target_weight: float,
) -> PortfolioSignal:
    sector_weight = _weight_by_attribute(portfolio, "sector", target.sector)
    country_weight = _weight_by_attribute(portfolio, "country", target.country)
    mega_cap_weight = _mega_cap_weight(portfolio)
    raw_score = 100 - round((sector_weight * 55) + (country_weight * 25) + (mega_cap_weight * 20))
    score = clamp_score(raw_score)
    return PortfolioSignal(
        score=score,
        reasoning=(
            f"Adding {target.ticker} at {target_weight:.1%} would bring existing "
            f"{target.sector} exposure of {sector_weight:.1%} and {target.country} exposure "
            f"of {country_weight:.1%} into the decision."
        ),
    )


def _sector_concentration(
    portfolio: Portfolio,
    target: CompanyPortfolioProfile,
    target_weight: float,
) -> PortfolioSignal:
    current_weight = _weight_by_attribute(portfolio, "sector", target.sector)
    pro_forma_weight = current_weight + target_weight
    score = _concentration_score(pro_forma_weight, preferred_limit=0.25, hard_limit=0.40)
    return PortfolioSignal(
        score=score,
        reasoning=(
            f"Pro forma {target.sector} exposure would be {pro_forma_weight:.1%} "
            f"including the target position."
        ),
    )


def _country_concentration(
    portfolio: Portfolio,
    target: CompanyPortfolioProfile,
    target_weight: float,
) -> PortfolioSignal:
    current_weight = _weight_by_attribute(portfolio, "country", target.country)
    pro_forma_weight = current_weight + target_weight
    score = _concentration_score(pro_forma_weight, preferred_limit=0.45, hard_limit=0.65)
    return PortfolioSignal(
        score=score,
        reasoning=(
            f"Pro forma {target.country} exposure would be {pro_forma_weight:.1%} "
            f"including the target position."
        ),
    )


def _market_cap_concentration(
    portfolio: Portfolio,
    target: CompanyPortfolioProfile,
    target_weight: float,
) -> PortfolioSignal:
    current_weight = _mega_cap_weight(portfolio)
    pro_forma_weight = current_weight + (target_weight if _is_mega_cap(target.market_cap) else 0)
    score = _concentration_score(pro_forma_weight, preferred_limit=0.35, hard_limit=0.55)
    cap_bucket = "mega-cap" if _is_mega_cap(target.market_cap) else "non-mega-cap"
    return PortfolioSignal(
        score=score,
        reasoning=(
            f"{target.ticker} is a {cap_bucket} company. Pro forma mega-cap exposure "
            f"would be {pro_forma_weight:.1%}."
        ),
    )


def _overlap_with_existing_holdings(
    portfolio: Portfolio,
    target: CompanyPortfolioProfile,
) -> PortfolioSignal:
    existing_tickers = {position.ticker.upper() for position in portfolio.positions}
    if target.ticker.upper() in existing_tickers:
        return PortfolioSignal(
            score=20,
            reasoning=(
                f"{target.ticker} already exists in the portfolio, so this would add "
                "direct overlap."
            ),
        )
    same_sector_positions = [
        position for position in portfolio.positions if position.sector == target.sector
    ]
    if same_sector_positions:
        tickers = ", ".join(position.ticker for position in same_sector_positions)
        score = clamp_score(80 - len(same_sector_positions) * 10)
        return PortfolioSignal(
            score=score,
            reasoning=f"{target.ticker} overlaps by sector with existing holdings: {tickers}.",
        )
    return PortfolioSignal(
        score=92,
        reasoning=f"{target.ticker} has no direct ticker or sector overlap with current holdings.",
    )


def _expected_quality_impact(
    portfolio: Portfolio,
    target: CompanyPortfolioProfile,
    target_weight: float,
) -> PortfolioSignal:
    current_quality = _weighted_average(portfolio.positions, "quality_score")
    pro_forma_quality = _pro_forma_average(current_quality, target.quality_score, target_weight)
    score = clamp_score(round(50 + (pro_forma_quality - current_quality) * 4))
    direction = "improve" if pro_forma_quality >= current_quality else "dilute"
    return PortfolioSignal(
        score=score,
        reasoning=(
            f"The target quality score of {target.quality_score}/100 would {direction} "
            f"portfolio quality from {current_quality:.1f}/100 to {pro_forma_quality:.1f}/100."
        ),
    )


def _expected_risk_impact(
    portfolio: Portfolio,
    target: CompanyPortfolioProfile,
    target_weight: float,
) -> PortfolioSignal:
    current_risk = _weighted_average(portfolio.positions, "risk_score")
    pro_forma_risk = _pro_forma_average(current_risk, target.risk_score, target_weight)
    score = clamp_score(round(50 + (pro_forma_risk - current_risk) * 4))
    direction = "improve" if pro_forma_risk >= current_risk else "weaken"
    return PortfolioSignal(
        score=score,
        reasoning=(
            f"The target risk profile score of {target.risk_score}/100 would {direction} "
            f"portfolio risk quality from {current_risk:.1f}/100 to {pro_forma_risk:.1f}/100."
        ),
    )


def _aggregate_portfolio_score(
    diversification: PortfolioSignal,
    sector: PortfolioSignal,
    country: PortfolioSignal,
    market_cap: PortfolioSignal,
    overlap: PortfolioSignal,
    quality: PortfolioSignal,
    risk: PortfolioSignal,
) -> int:
    weighted_score = (
        diversification.score * 0.15
        + sector.score * 0.15
        + country.score * 0.10
        + market_cap.score * 0.10
        + overlap.score * 0.15
        + quality.score * 0.20
        + risk.score * 0.15
    )
    return clamp_score(round(weighted_score))


def _recommend(score: int) -> PortfolioRecommendation:
    if score >= 85:
        return PortfolioRecommendation.STRONG_ADD
    if score >= 70:
        return PortfolioRecommendation.ADD
    if score >= 50:
        return PortfolioRecommendation.NEUTRAL
    if score >= 35:
        return PortfolioRecommendation.REDUCE
    return PortfolioRecommendation.AVOID


def _final_reasoning(
    target: CompanyPortfolioProfile,
    portfolio_score: int,
    recommendation: PortfolioRecommendation,
    sector: PortfolioSignal,
    overlap: PortfolioSignal,
    quality: PortfolioSignal,
    risk: PortfolioSignal,
) -> str:
    return (
        f"Atlas rates {target.ticker} as {recommendation.value} for this portfolio with a "
        f"{portfolio_score}/100 portfolio fit score. The decision is driven by sector "
        f"concentration ({sector.score}/100), overlap ({overlap.score}/100), expected "
        f"quality impact ({quality.score}/100), and expected risk impact ({risk.score}/100)."
    )


def _weight_by_attribute(portfolio: Portfolio, attribute: str, value: str) -> float:
    return sum(
        position.weight
        for position in portfolio.positions
        if getattr(position, attribute).lower() == value.lower()
    )


def _mega_cap_weight(portfolio: Portfolio) -> float:
    return sum(
        position.weight
        for position in portfolio.positions
        if _is_mega_cap(position.market_cap)
    )


def _weighted_average(positions: tuple[PortfolioPosition, ...], attribute: str) -> float:
    total_weight = sum(position.weight for position in positions)
    if total_weight <= 0:
        return 0
    return (
        sum(getattr(position, attribute) * position.weight for position in positions)
        / total_weight
    )


def _pro_forma_average(current_value: float, target_value: int, target_weight: float) -> float:
    current_weight = max(0.0, 1.0 - target_weight)
    return current_value * current_weight + target_value * target_weight


def _concentration_score(weight: float, preferred_limit: float, hard_limit: float) -> int:
    if weight <= preferred_limit:
        return 90
    if weight >= hard_limit:
        return 25
    penalty_range = hard_limit - preferred_limit
    overage = weight - preferred_limit
    return clamp_score(round(90 - (overage / penalty_range) * 65))


def _normalize_weight(weight: float) -> float:
    normalized = weight / 100 if weight > 1 else weight
    return max(0.0, min(1.0, normalized))


def _is_mega_cap(market_cap: float) -> bool:
    return market_cap >= 500_000_000_000


def _score_line(label: str, score: int) -> str:
    return f"{label}: {score}/100"


def _signal_line(signal: PortfolioSignal) -> str:
    return f"{_score_line('Score', signal.score)}\nReasoning: {signal.reasoning}"

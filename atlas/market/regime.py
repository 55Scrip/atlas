import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from atlas.analysis.scores import clamp_score


class MarketRegime(str, Enum):
    BULL = "Bull"
    NEUTRAL = "Neutral"
    CORRECTION = "Correction"
    BEAR = "Bear"
    CRISIS = "Crisis"


@dataclass(frozen=True)
class MarketIndicators:
    sp500_drawdown: float
    nasdaq_drawdown: float
    vix: float
    interest_rate_trend: str
    inflation_trend: str

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "MarketIndicators":
        return cls(
            sp500_drawdown=_normalize_drawdown(payload["sp500_drawdown"]),
            nasdaq_drawdown=_normalize_drawdown(payload["nasdaq_drawdown"]),
            vix=float(payload["vix"]),
            interest_rate_trend=str(payload["interest_rate_trend"]),
            inflation_trend=str(payload["inflation_trend"]),
        )


@dataclass(frozen=True)
class MarketSnapshot:
    indicators: MarketIndicators
    as_of: str | None = None
    source: str = "manual"

    @classmethod
    def from_json_file(cls, path: Path) -> "MarketSnapshot":
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        return cls.from_mapping(payload)

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "MarketSnapshot":
        raw_indicators = payload.get("indicators", payload)
        if not isinstance(raw_indicators, dict):
            raise ValueError("Market JSON indicators must be an object.")
        try:
            indicators = MarketIndicators.from_mapping(raw_indicators)
        except KeyError as exc:
            raise ValueError(f"Market JSON is missing required field: {exc.args[0]}") from exc
        return cls(
            indicators=indicators,
            as_of=_optional_string(payload.get("as_of")),
            source=str(payload.get("source", "manual")),
        )


@dataclass(frozen=True)
class MarketRegimeAnalysis:
    regime: MarketRegime
    confidence: int
    indicators: MarketIndicators
    key_indicators: tuple[str, ...]
    opportunities: tuple[str, ...]
    risks: tuple[str, ...]
    suggested_investment_behaviour: tuple[str, ...]
    summary: str


class MarketRegimeEngine:
    def analyze(self, snapshot: MarketSnapshot) -> MarketRegimeAnalysis:
        indicators = snapshot.indicators
        regime = _classify_regime(indicators)
        key_indicators = _key_indicators(indicators)
        return MarketRegimeAnalysis(
            regime=regime,
            confidence=_confidence(regime, indicators),
            indicators=indicators,
            key_indicators=key_indicators,
            opportunities=_opportunities(regime),
            risks=_risks(regime, indicators),
            suggested_investment_behaviour=_suggested_behaviour(regime),
            summary=_summary(regime, key_indicators),
        )


def render_market_regime(analysis: MarketRegimeAnalysis) -> str:
    lines = [
        "Market Regime Analysis",
        "",
        f"Current market regime: {analysis.regime.value}",
        f"Confidence: {analysis.confidence}/100",
        "",
        "Key Indicators",
        *_render_list(analysis.key_indicators),
        "",
        "Opportunities",
        *_render_list(analysis.opportunities),
        "",
        "Risks",
        *_render_list(analysis.risks),
        "",
        "Suggested Investment Behaviour",
        *_render_list(analysis.suggested_investment_behaviour),
        "",
        "Summary",
        analysis.summary,
    ]
    return "\n".join(lines)


def _classify_regime(indicators: MarketIndicators) -> MarketRegime:
    stress_score = _stress_score(indicators)
    if stress_score >= 10:
        return MarketRegime.CRISIS
    if stress_score >= 7:
        return MarketRegime.BEAR
    if stress_score >= 3:
        return MarketRegime.CORRECTION
    if _bullish_conditions(indicators):
        return MarketRegime.BULL
    return MarketRegime.NEUTRAL


def _stress_score(indicators: MarketIndicators) -> int:
    score = 0
    score += _drawdown_stress(
        indicators.sp500_drawdown,
        correction=-0.10,
        bear=-0.20,
        crisis=-0.35,
    )
    score += _drawdown_stress(
        indicators.nasdaq_drawdown,
        correction=-0.15,
        bear=-0.30,
        crisis=-0.45,
    )
    score += _vix_stress(indicators.vix)
    score += _trend_stress(indicators.interest_rate_trend)
    score += _trend_stress(indicators.inflation_trend)
    return score


def _drawdown_stress(value: float, correction: float, bear: float, crisis: float) -> int:
    if value <= crisis:
        return 4
    if value <= bear:
        return 3
    if value <= correction:
        return 2
    if value <= -0.05:
        return 1
    return 0


def _vix_stress(vix: float) -> int:
    if vix >= 50:
        return 4
    if vix >= 35:
        return 3
    if vix >= 25:
        return 2
    if vix >= 20:
        return 1
    return 0


def _trend_stress(trend: str) -> int:
    normalized = _normalize_trend(trend)
    if normalized in {"surging", "accelerating", "rising sharply"}:
        return 2
    if normalized in {"rising", "higher"}:
        return 1
    if normalized in {"falling", "declining", "lower", "easing"}:
        return -1
    return 0


def _bullish_conditions(indicators: MarketIndicators) -> bool:
    return (
        indicators.sp500_drawdown >= -0.05
        and indicators.nasdaq_drawdown >= -0.08
        and indicators.vix < 18
        and _trend_stress(indicators.interest_rate_trend) <= 0
        and _trend_stress(indicators.inflation_trend) <= 0
    )


def _confidence(regime: MarketRegime, indicators: MarketIndicators) -> int:
    stress_score = _stress_score(indicators)
    if regime == MarketRegime.CRISIS:
        base = 88 if stress_score >= 10 else 80
    elif regime == MarketRegime.BEAR:
        base = 82 if stress_score >= 7 else 74
    elif regime == MarketRegime.CORRECTION:
        base = 76 if stress_score >= 4 else 68
    elif regime == MarketRegime.BULL:
        base = 76
    else:
        base = 64
    if abs(indicators.sp500_drawdown - indicators.nasdaq_drawdown) > 0.20:
        base -= 8
    if indicators.vix >= 35 and regime not in {MarketRegime.BEAR, MarketRegime.CRISIS}:
        base -= 10
    return clamp_score(base)


def _key_indicators(indicators: MarketIndicators) -> tuple[str, ...]:
    return (
        f"S&P 500 drawdown: {_format_drawdown(indicators.sp500_drawdown)}",
        f"Nasdaq drawdown: {_format_drawdown(indicators.nasdaq_drawdown)}",
        f"VIX: {indicators.vix:.1f}",
        f"Interest rate trend: {indicators.interest_rate_trend}",
        f"Inflation trend: {indicators.inflation_trend}",
    )


def _opportunities(regime: MarketRegime) -> tuple[str, ...]:
    opportunities = {
        MarketRegime.BULL: (
            "Broad participation can support steady capital deployment.",
            "Strong businesses may keep compounding when valuation remains reasonable.",
        ),
        MarketRegime.NEUTRAL: (
            "Normal allocation discipline can work without forcing urgency.",
            "Security selection can matter more than market timing.",
        ),
        MarketRegime.CORRECTION: (
            "Watchlists become more useful as prices reset.",
            "Gradual buying can improve long-term entry points.",
        ),
        MarketRegime.BEAR: (
            "High-quality profitable businesses may become more attractive.",
            "Phased capital deployment can take advantage of volatility.",
        ),
        MarketRegime.CRISIS: (
            "Financially strong businesses may become available at unusual prices.",
            "Patient investors can prepare without needing to predict the bottom.",
        ),
    }
    return opportunities[regime]


def _risks(regime: MarketRegime, indicators: MarketIndicators) -> tuple[str, ...]:
    risks = {
        MarketRegime.BULL: (
            "Momentum can hide valuation risk.",
            "Low volatility can encourage position sizes that are too aggressive.",
        ),
        MarketRegime.NEUTRAL: (
            "Mixed signals can lead to overconfidence.",
            "Macro conditions may shift before prices fully reflect them.",
        ),
        MarketRegime.CORRECTION: (
            "Volatility can continue before fundamentals improve.",
            "Weak companies may look cheap for good reasons.",
        ),
        MarketRegime.BEAR: (
            "Drawdowns can deepen and remain painful for longer than expected.",
            "Liquidity and earnings risk can rise together.",
        ),
        MarketRegime.CRISIS: (
            "Liquidity can disappear quickly.",
            "Even strong companies can face forced selling and severe volatility.",
        ),
    }
    trend_risks = []
    if _trend_stress(indicators.interest_rate_trend) > 0:
        trend_risks.append("Rising rates can pressure valuation multiples.")
    if _trend_stress(indicators.inflation_trend) > 0:
        trend_risks.append("Rising inflation can pressure margins and discount rates.")
    return (*risks[regime], *trend_risks)


def _suggested_behaviour(regime: MarketRegime) -> tuple[str, ...]:
    behaviours = {
        MarketRegime.BULL: (
            "Continue investing.",
            "Avoid chasing momentum.",
        ),
        MarketRegime.NEUTRAL: (
            "Invest normally.",
            "Keep normal diversification and valuation discipline.",
        ),
        MarketRegime.CORRECTION: (
            "Continue dollar-cost averaging.",
            "Build watchlists.",
            "Prepare capital for opportunities.",
        ),
        MarketRegime.BEAR: (
            "Buy gradually.",
            "Slightly increase cash reserves.",
            "Focus on profitable, high-quality companies.",
        ),
        MarketRegime.CRISIS: (
            "Never panic sell.",
            "Invest slowly over time.",
            "Preserve liquidity.",
            "Focus only on financially strong businesses.",
        ),
    }
    return behaviours[regime]


def _summary(regime: MarketRegime, key_indicators: tuple[str, ...]) -> str:
    return (
        f"Atlas classifies the market as {regime.value} based on "
        f"{'; '.join(key_indicators)}."
    )


def _normalize_drawdown(value: Any) -> float:
    number = float(value)
    if abs(number) > 1:
        number = number / 100
    return -abs(number)


def _normalize_trend(trend: str) -> str:
    return trend.strip().lower().replace("_", " ")


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _format_drawdown(value: float) -> str:
    return f"{value:.1%}"


def _render_list(items: tuple[str, ...]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from atlas.analysis.scores import clamp_score
from atlas.market import MarketRegime


class RiskProfile(str, Enum):
    CONSERVATIVE = "Conservative"
    BALANCED = "Balanced"
    GROWTH = "Growth"
    AGGRESSIVE = "Aggressive"


@dataclass(frozen=True)
class CurrentPosition:
    ticker: str
    market_value: float

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "CurrentPosition":
        try:
            ticker = str(payload["ticker"]).upper()
            market_value = float(payload["market_value"])
        except KeyError as exc:
            raise ValueError(f"Current position is missing required field: {exc.args[0]}") from exc
        if market_value < 0:
            raise ValueError("Current position market_value cannot be negative.")
        return cls(ticker=ticker, market_value=market_value)


@dataclass(frozen=True)
class PositionSizingInput:
    total_capital: float
    investable_capital: float
    existing_cash_reserve: float
    required_cash_reserve: float
    investment_horizon_years: float
    risk_profile: RiskProfile
    market_regime: MarketRegime
    current_positions: tuple[CurrentPosition, ...]
    target_ticker: str
    target_company_score: int
    target_confidence: int
    target_risk_score: int

    @classmethod
    def from_json_file(cls, path: Path) -> "PositionSizingInput":
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        return cls.from_mapping(payload)

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "PositionSizingInput":
        required_fields = (
            "total_capital",
            "investable_capital",
            "existing_cash_reserve",
            "required_cash_reserve",
            "investment_horizon_years",
            "risk_profile",
            "market_regime",
            "current_positions",
            "target_ticker",
            "target_company_score",
            "target_confidence",
            "target_risk_score",
        )
        missing = [field for field in required_fields if field not in payload]
        if missing:
            raise ValueError(f"Risk input is missing required fields: {', '.join(missing)}")
        raw_positions = payload["current_positions"]
        if not isinstance(raw_positions, list):
            raise ValueError("current_positions must be a list.")
        return cls(
            total_capital=_non_negative_float(payload["total_capital"], "total_capital"),
            investable_capital=_non_negative_float(
                payload["investable_capital"],
                "investable_capital",
            ),
            existing_cash_reserve=_non_negative_float(
                payload["existing_cash_reserve"],
                "existing_cash_reserve",
            ),
            required_cash_reserve=_non_negative_float(
                payload["required_cash_reserve"],
                "required_cash_reserve",
            ),
            investment_horizon_years=_non_negative_float(
                payload["investment_horizon_years"],
                "investment_horizon_years",
            ),
            risk_profile=_parse_risk_profile(payload["risk_profile"]),
            market_regime=_parse_market_regime(payload["market_regime"]),
            current_positions=tuple(
                CurrentPosition.from_mapping(position) for position in raw_positions
            ),
            target_ticker=str(payload["target_ticker"]).upper(),
            target_company_score=clamp_score(round(float(payload["target_company_score"]))),
            target_confidence=clamp_score(round(float(payload["target_confidence"]))),
            target_risk_score=clamp_score(round(float(payload["target_risk_score"]))),
        )


@dataclass(frozen=True)
class CapitalDeploymentPlan:
    suggested_initial_investment: float
    suggested_monthly_deployment: float
    deployment_period_months: int
    market_regime_adjustment: str


@dataclass(frozen=True)
class PositionSizingResult:
    investable_capital: float
    cash_reserve_status: str
    maximum_recommended_position_size: float
    concentration_warning: str
    liquidity_warning: str
    final_risk_recommendation: str


@dataclass(frozen=True)
class RiskAnalysis:
    risk_profile: RiskProfile
    target_ticker: str
    deployment_plan: CapitalDeploymentPlan
    position_sizing: PositionSizingResult
    reasoning: tuple[str, ...]


class RiskEngine:
    def analyze(self, sizing_input: PositionSizingInput) -> RiskAnalysis:
        cash_gap = max(
            0.0,
            sizing_input.required_cash_reserve - sizing_input.existing_cash_reserve,
        )
        cash_reserve_ok = cash_gap == 0
        horizon_ok = sizing_input.investment_horizon_years >= 3
        adjusted_investable = _adjusted_investable_capital(
            sizing_input=sizing_input,
            cash_gap=cash_gap,
            horizon_ok=horizon_ok,
        )
        max_position_size = _maximum_position_size(sizing_input)
        current_target_value = _current_target_value(sizing_input)
        remaining_position_capacity = max(0.0, max_position_size - current_target_value)
        deployable_to_target = min(adjusted_investable, remaining_position_capacity)
        period = _deployment_period(sizing_input.market_regime)
        initial_rate = _initial_deployment_rate(sizing_input.market_regime)
        suggested_initial = _round_money(deployable_to_target * initial_rate)
        remaining_after_initial = max(0.0, deployable_to_target - suggested_initial)
        suggested_monthly = _round_money(remaining_after_initial / period) if period else 0.0

        deployment_plan = CapitalDeploymentPlan(
            suggested_initial_investment=suggested_initial,
            suggested_monthly_deployment=suggested_monthly,
            deployment_period_months=period,
            market_regime_adjustment=_market_regime_adjustment(sizing_input.market_regime),
        )
        position_sizing = PositionSizingResult(
            investable_capital=_round_money(adjusted_investable),
            cash_reserve_status=_cash_reserve_status(cash_reserve_ok, cash_gap),
            maximum_recommended_position_size=_round_money(max_position_size),
            concentration_warning=_concentration_warning(
                sizing_input=sizing_input,
                max_position_size=max_position_size,
                current_target_value=current_target_value,
            ),
            liquidity_warning=_liquidity_warning(
                cash_reserve_ok=cash_reserve_ok,
                horizon_ok=horizon_ok,
                cash_gap=cash_gap,
            ),
            final_risk_recommendation=_final_recommendation(
                sizing_input=sizing_input,
                cash_reserve_ok=cash_reserve_ok,
                horizon_ok=horizon_ok,
                deployable_to_target=deployable_to_target,
            ),
        )
        return RiskAnalysis(
            risk_profile=sizing_input.risk_profile,
            target_ticker=sizing_input.target_ticker,
            deployment_plan=deployment_plan,
            position_sizing=position_sizing,
            reasoning=_reasoning(
                sizing_input=sizing_input,
                cash_gap=cash_gap,
                adjusted_investable=adjusted_investable,
                max_position_size=max_position_size,
                current_target_value=current_target_value,
                deployable_to_target=deployable_to_target,
            ),
        )


def render_risk_analysis(analysis: RiskAnalysis) -> str:
    sizing = analysis.position_sizing
    plan = analysis.deployment_plan
    lines = [
        "Risk & Position Sizing Analysis",
        "",
        f"Target Ticker: {analysis.target_ticker}",
        f"Risk Profile: {analysis.risk_profile.value}",
        f"Investable Capital: {_format_money(sizing.investable_capital)}",
        f"Cash Reserve Status: {sizing.cash_reserve_status}",
        f"Suggested Initial Investment: {_format_money(plan.suggested_initial_investment)}",
        f"Suggested Monthly Deployment: {_format_money(plan.suggested_monthly_deployment)}",
        f"Deployment Period: {plan.deployment_period_months} months",
        f"Maximum Position Size: {_format_money(sizing.maximum_recommended_position_size)}",
        f"Concentration Risk: {sizing.concentration_warning}",
        f"Liquidity Risk: {sizing.liquidity_warning}",
        f"Market Regime Adjustment: {plan.market_regime_adjustment}",
        f"Final Recommendation: {sizing.final_risk_recommendation}",
        "",
        "Reasoning",
        *_render_list(analysis.reasoning),
    ]
    return "\n".join(lines)


def _adjusted_investable_capital(
    sizing_input: PositionSizingInput,
    cash_gap: float,
    horizon_ok: bool,
) -> float:
    if not horizon_ok:
        return 0.0
    reserve_protected_capital = max(0.0, sizing_input.investable_capital - cash_gap)
    surplus_after_required_reserve = max(
        0.0,
        sizing_input.total_capital - sizing_input.required_cash_reserve,
    )
    return min(reserve_protected_capital, surplus_after_required_reserve)


def _maximum_position_size(sizing_input: PositionSizingInput) -> float:
    base_limit = sizing_input.total_capital * _risk_profile_position_cap(sizing_input.risk_profile)
    quality_multiplier = _quality_multiplier(sizing_input)
    return base_limit * quality_multiplier


def _risk_profile_position_cap(risk_profile: RiskProfile) -> float:
    caps = {
        RiskProfile.CONSERVATIVE: 0.05,
        RiskProfile.BALANCED: 0.08,
        RiskProfile.GROWTH: 0.12,
        RiskProfile.AGGRESSIVE: 0.15,
    }
    return caps[risk_profile]


def _quality_multiplier(sizing_input: PositionSizingInput) -> float:
    multiplier = 1.0
    if sizing_input.target_confidence < 60:
        multiplier *= 0.50
    elif sizing_input.target_confidence < 75:
        multiplier *= 0.75
    if sizing_input.target_risk_score < 40:
        multiplier *= 0.50
    elif sizing_input.target_risk_score < 60:
        multiplier *= 0.75
    if sizing_input.target_company_score < 70:
        multiplier *= 0.75
    return multiplier


def _current_target_value(sizing_input: PositionSizingInput) -> float:
    return sum(
        position.market_value
        for position in sizing_input.current_positions
        if position.ticker == sizing_input.target_ticker
    )


def _deployment_period(market_regime: MarketRegime) -> int:
    periods = {
        MarketRegime.BULL: 3,
        MarketRegime.NEUTRAL: 6,
        MarketRegime.CORRECTION: 12,
        MarketRegime.BEAR: 18,
        MarketRegime.CRISIS: 24,
    }
    return periods[market_regime]


def _initial_deployment_rate(market_regime: MarketRegime) -> float:
    rates = {
        MarketRegime.BULL: 0.35,
        MarketRegime.NEUTRAL: 0.25,
        MarketRegime.CORRECTION: 0.15,
        MarketRegime.BEAR: 0.10,
        MarketRegime.CRISIS: 0.05,
    }
    return rates[market_regime]


def _market_regime_adjustment(market_regime: MarketRegime) -> str:
    adjustments = {
        MarketRegime.BULL: "Bull market allows normal deployment, but avoids momentum chasing.",
        MarketRegime.NEUTRAL: "Neutral market supports normal staged deployment.",
        MarketRegime.CORRECTION: (
            "Correction regime slows deployment and favors dollar-cost averaging."
        ),
        MarketRegime.BEAR: "Bear market favors gradual buying and slightly higher cash reserves.",
        MarketRegime.CRISIS: "Crisis regime prioritizes liquidity and very slow deployment.",
    }
    return adjustments[market_regime]


def _cash_reserve_status(cash_reserve_ok: bool, cash_gap: float) -> str:
    if cash_reserve_ok:
        return "Adequate"
    return f"Below required reserve by {_format_money(cash_gap)}"


def _concentration_warning(
    sizing_input: PositionSizingInput,
    max_position_size: float,
    current_target_value: float,
) -> str:
    if sizing_input.total_capital <= 0:
        return "Total capital is zero, so concentration cannot be measured."
    max_weight = max_position_size / sizing_input.total_capital
    current_weight = current_target_value / sizing_input.total_capital
    if current_target_value > max_position_size:
        return (
            f"{sizing_input.target_ticker} already exceeds the recommended cap "
            f"({current_weight:.1%} current vs {max_weight:.1%} max)."
        )
    return (
        f"Single-position cap is {max_weight:.1%}; current {sizing_input.target_ticker} "
        f"weight is {current_weight:.1%}."
    )


def _liquidity_warning(cash_reserve_ok: bool, horizon_ok: bool, cash_gap: float) -> str:
    if not horizon_ok:
        return "Investment horizon is short term; do not invest money needed soon."
    if not cash_reserve_ok:
        return (
            f"Required reserve is not fully funded; protect {_format_money(cash_gap)} before "
            "new investment."
        )
    return "Required cash reserve is protected before new investment."


def _final_recommendation(
    sizing_input: PositionSizingInput,
    cash_reserve_ok: bool,
    horizon_ok: bool,
    deployable_to_target: float,
) -> str:
    if not horizon_ok:
        return "Do not invest now; capital may be needed in the short term."
    if not cash_reserve_ok:
        return "Fund the required cash reserve before investing additional capital."
    if deployable_to_target <= 0:
        return "Do not add to this position; concentration or capital limits are binding."
    if sizing_input.market_regime in {
        MarketRegime.CORRECTION,
        MarketRegime.BEAR,
        MarketRegime.CRISIS,
    }:
        return "Invest gradually with disciplined pacing and preserved liquidity."
    return "Deploy capital normally within the recommended position-size limit."


def _reasoning(
    sizing_input: PositionSizingInput,
    cash_gap: float,
    adjusted_investable: float,
    max_position_size: float,
    current_target_value: float,
    deployable_to_target: float,
) -> tuple[str, ...]:
    return (
        (
            f"Atlas protects the required cash reserve first. Existing reserve is "
            f"{_format_money(sizing_input.existing_cash_reserve)} against a required "
            f"reserve of {_format_money(sizing_input.required_cash_reserve)}."
        ),
        (
            f"After reserve protection and horizon checks, investable capital is "
            f"{_format_money(adjusted_investable)}."
        ),
        (
            f"{sizing_input.risk_profile.value} profile caps a single position before "
            f"quality adjustments; confidence {sizing_input.target_confidence}/100 and "
            f"risk score {sizing_input.target_risk_score}/100 set the final cap at "
            f"{_format_money(max_position_size)}."
        ),
        (
            f"Current {sizing_input.target_ticker} exposure is "
            f"{_format_money(current_target_value)}, leaving "
            f"{_format_money(max(0.0, max_position_size - current_target_value))} of "
            "remaining position capacity."
        ),
        (
            f"Market regime {sizing_input.market_regime.value} sets deployment pacing; "
            f"deployable capital for this target is {_format_money(deployable_to_target)}."
        ),
        (
            "This is deterministic risk guidance for position sizing and liquidity "
            "discipline, not personal financial advice or a guaranteed outcome."
        ),
    )


def _parse_risk_profile(value: Any) -> RiskProfile:
    normalized = str(value).strip().lower().replace("_", " ")
    for profile in RiskProfile:
        if normalized == profile.value.lower():
            return profile
    raise ValueError(f"Unknown risk profile: {value}")


def _parse_market_regime(value: Any) -> MarketRegime:
    normalized = str(value).strip().lower().replace("_", " ")
    for regime in MarketRegime:
        if normalized == regime.value.lower():
            return regime
    raise ValueError(f"Unknown market regime: {value}")


def _non_negative_float(value: Any, field_name: str) -> float:
    number = float(value)
    if number < 0:
        raise ValueError(f"{field_name} cannot be negative.")
    return number


def _round_money(value: float) -> float:
    return round(value, 2)


def _format_money(value: float) -> str:
    return f"${value:,.2f}"


def _render_list(items: tuple[str, ...]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]

import json

from typer.testing import CliRunner

from atlas.cli.main import app
from atlas.market import MarketRegime
from atlas.risk import (
    CurrentPosition,
    PositionSizingInput,
    RiskEngine,
    RiskProfile,
    render_risk_analysis,
)


def _sizing_input(
    *,
    total_capital: float = 500_000,
    investable_capital: float = 200_000,
    existing_cash_reserve: float = 100_000,
    required_cash_reserve: float = 75_000,
    investment_horizon_years: float = 10,
    risk_profile: RiskProfile = RiskProfile.BALANCED,
    market_regime: MarketRegime = MarketRegime.CORRECTION,
    current_positions: tuple[CurrentPosition, ...] = (
        CurrentPosition(ticker="MSFT", market_value=80_000),
        CurrentPosition(ticker="NVDA", market_value=60_000),
    ),
    target_ticker: str = "TSMC",
    target_company_score: int = 86,
    target_confidence: int = 82,
    target_risk_score: int = 35,
) -> PositionSizingInput:
    return PositionSizingInput(
        total_capital=total_capital,
        investable_capital=investable_capital,
        existing_cash_reserve=existing_cash_reserve,
        required_cash_reserve=required_cash_reserve,
        investment_horizon_years=investment_horizon_years,
        risk_profile=risk_profile,
        market_regime=market_regime,
        current_positions=current_positions,
        target_ticker=target_ticker,
        target_company_score=target_company_score,
        target_confidence=target_confidence,
        target_risk_score=target_risk_score,
    )


def test_risk_engine_sizes_balanced_correction_example():
    analysis = RiskEngine().analyze(_sizing_input())

    assert analysis.risk_profile == RiskProfile.BALANCED
    assert analysis.target_ticker == "TSMC"
    assert analysis.position_sizing.cash_reserve_status == "Adequate"
    assert analysis.position_sizing.investable_capital == 200_000
    assert analysis.position_sizing.maximum_recommended_position_size == 20_000
    assert analysis.deployment_plan.suggested_initial_investment == 3_000
    assert analysis.deployment_plan.suggested_monthly_deployment == 1_416.67
    assert analysis.deployment_plan.deployment_period_months == 12
    assert "gradually" in analysis.position_sizing.final_risk_recommendation.lower()


def test_risk_engine_never_invests_below_required_cash_reserve():
    sizing_input = _sizing_input(
        investable_capital=50_000,
        existing_cash_reserve=40_000,
        required_cash_reserve=75_000,
    )

    analysis = RiskEngine().analyze(sizing_input)

    assert analysis.position_sizing.cash_reserve_status == (
        "Below required reserve by $35,000.00"
    )
    assert analysis.position_sizing.investable_capital == 15_000
    assert "Fund the required cash reserve" in (
        analysis.position_sizing.final_risk_recommendation
    )
    assert "Required reserve is not fully funded" in analysis.position_sizing.liquidity_warning


def test_risk_engine_blocks_short_term_capital():
    analysis = RiskEngine().analyze(_sizing_input(investment_horizon_years=1))

    assert analysis.position_sizing.investable_capital == 0
    assert analysis.deployment_plan.suggested_initial_investment == 0
    assert analysis.deployment_plan.suggested_monthly_deployment == 0
    assert "short term" in analysis.position_sizing.liquidity_warning
    assert "Do not invest now" in analysis.position_sizing.final_risk_recommendation


def test_risk_engine_uses_market_regime_to_set_pacing():
    bull = RiskEngine().analyze(_sizing_input(market_regime=MarketRegime.BULL))
    crisis = RiskEngine().analyze(_sizing_input(market_regime=MarketRegime.CRISIS))

    assert bull.deployment_plan.deployment_period_months == 3
    assert crisis.deployment_plan.deployment_period_months == 24
    assert bull.deployment_plan.suggested_initial_investment > (
        crisis.deployment_plan.suggested_initial_investment
    )
    assert "very slow" in crisis.deployment_plan.market_regime_adjustment


def test_risk_engine_caps_single_position_by_risk_profile():
    conservative = RiskEngine().analyze(
        _sizing_input(
            risk_profile=RiskProfile.CONSERVATIVE,
            target_risk_score=80,
        )
    )
    aggressive = RiskEngine().analyze(
        _sizing_input(
            risk_profile=RiskProfile.AGGRESSIVE,
            target_risk_score=80,
        )
    )

    assert conservative.position_sizing.maximum_recommended_position_size == 25_000
    assert aggressive.position_sizing.maximum_recommended_position_size == 75_000


def test_risk_engine_lowers_position_size_for_low_confidence_and_high_risk():
    strong = RiskEngine().analyze(
        _sizing_input(
            target_confidence=90,
            target_risk_score=85,
        )
    )
    weak = RiskEngine().analyze(
        _sizing_input(
            target_confidence=55,
            target_risk_score=35,
        )
    )

    assert strong.position_sizing.maximum_recommended_position_size == 40_000
    assert weak.position_sizing.maximum_recommended_position_size == 10_000


def test_risk_engine_warns_when_target_position_already_exceeds_cap():
    analysis = RiskEngine().analyze(
        _sizing_input(
            current_positions=(CurrentPosition(ticker="TSMC", market_value=50_000),),
        )
    )

    assert analysis.deployment_plan.suggested_initial_investment == 0
    assert "already exceeds the recommended cap" in (
        analysis.position_sizing.concentration_warning
    )
    assert "concentration or capital limits are binding" in (
        analysis.position_sizing.final_risk_recommendation
    )


def test_position_sizing_input_loads_json(tmp_path):
    path = tmp_path / "risk_input.json"
    path.write_text(
        json.dumps(
            {
                "total_capital": 500000,
                "investable_capital": 200000,
                "existing_cash_reserve": 100000,
                "required_cash_reserve": 75000,
                "investment_horizon_years": 10,
                "risk_profile": "balanced",
                "market_regime": "correction",
                "current_positions": [
                    {"ticker": "MSFT", "market_value": 80000},
                    {"ticker": "NVDA", "market_value": 60000},
                ],
                "target_ticker": "TSMC",
                "target_company_score": 86,
                "target_confidence": 82,
                "target_risk_score": 35,
            }
        ),
        encoding="utf-8",
    )

    sizing_input = PositionSizingInput.from_json_file(path)

    assert sizing_input.risk_profile == RiskProfile.BALANCED
    assert sizing_input.market_regime == MarketRegime.CORRECTION
    assert sizing_input.target_ticker == "TSMC"
    assert len(sizing_input.current_positions) == 2


def test_position_sizing_input_rejects_missing_fields(tmp_path):
    path = tmp_path / "risk_input.json"
    path.write_text(json.dumps({"total_capital": 500000}), encoding="utf-8")

    try:
        PositionSizingInput.from_json_file(path)
    except ValueError as exc:
        assert "missing required fields" in str(exc)
    else:
        raise AssertionError("PositionSizingInput should reject incomplete JSON")


def test_risk_renderer_includes_required_sections():
    analysis = RiskEngine().analyze(_sizing_input())

    rendered = render_risk_analysis(analysis)

    assert "Risk Profile" in rendered
    assert "Investable Capital" in rendered
    assert "Cash Reserve Status" in rendered
    assert "Suggested Initial Investment" in rendered
    assert "Suggested Monthly Deployment" in rendered
    assert "Deployment Period" in rendered
    assert "Maximum Position Size" in rendered
    assert "Concentration Risk" in rendered
    assert "Liquidity Risk" in rendered
    assert "Market Regime Adjustment" in rendered
    assert "Final Recommendation" in rendered
    assert "Reasoning" in rendered


def test_risk_cli_outputs_position_sizing_report(tmp_path):
    path = tmp_path / "risk_input.json"
    path.write_text(
        json.dumps(
            {
                "total_capital": 500000,
                "investable_capital": 200000,
                "existing_cash_reserve": 100000,
                "required_cash_reserve": 75000,
                "investment_horizon_years": 10,
                "risk_profile": "balanced",
                "market_regime": "correction",
                "current_positions": [
                    {"ticker": "MSFT", "market_value": 80000},
                    {"ticker": "NVDA", "market_value": 60000},
                ],
                "target_ticker": "TSMC",
                "target_company_score": 86,
                "target_confidence": 82,
                "target_risk_score": 35,
            }
        ),
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(app, ["risk", "size", str(path)])

    assert result.exit_code == 0
    assert "Risk & Position Sizing Analysis" in result.output
    assert "Risk Profile: Balanced" in result.output
    assert "Suggested Initial Investment: $3,000.00" in result.output

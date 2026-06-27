import json

from typer.testing import CliRunner

from atlas.cli.main import app
from atlas.market import MarketIndicators, MarketRegime, MarketRegimeEngine, MarketSnapshot
from atlas.profile import (
    InvestmentGoal,
    InvestorProfileEngine,
    PortfolioPurpose,
    RiskCapacity,
    RiskPreference,
    RiskTolerance,
    TimeHorizon,
)
from atlas.risk_drift import (
    RiskDriftEngine,
    RiskDriftInput,
    RiskDriftLevel,
    render_risk_drift_assessment,
)


def _profile(
    *,
    portfolio_purpose: PortfolioPurpose,
    risk_tolerance: RiskTolerance,
    risk_capacity: RiskCapacity,
    time_horizon: TimeHorizon,
):
    return InvestorProfileEngine().create_profile(
        name="Investor",
        investment_goals=(InvestmentGoal.WEALTH_ACCUMULATION,),
        portfolio_purpose=portfolio_purpose,
        risk_preference=RiskPreference.BALANCED,
        risk_tolerance=risk_tolerance,
        risk_capacity=risk_capacity,
        time_horizon=time_horizon,
    )


def test_detects_material_profile_portfolio_and_market_drift():
    original = _profile(
        portfolio_purpose=PortfolioPurpose.EXPLORATION_PORTFOLIO,
        risk_tolerance=RiskTolerance.AGGRESSIVE,
        risk_capacity=RiskCapacity.HIGH,
        time_horizon=TimeHorizon.LONG,
    )
    current = _profile(
        portfolio_purpose=PortfolioPurpose.CORE_PORTFOLIO,
        risk_tolerance=RiskTolerance.CONSERVATIVE,
        risk_capacity=RiskCapacity.LOW,
        time_horizon=TimeHorizon.SHORT,
    )
    market_regime = MarketRegimeEngine().analyze(
        MarketSnapshot(
            indicators=MarketIndicators(
                sp500_drawdown=-0.18,
                nasdaq_drawdown=-0.26,
                vix=34,
                interest_rate_trend="rising",
                inflation_trend="rising",
            )
        )
    )

    assessment = RiskDriftEngine().assess(
        RiskDriftInput(
            original_profile=original,
            current_profile=current,
            original_market_regime=MarketRegime.BULL,
            current_market_regime=market_regime,
            original_portfolio_size=20_000,
            current_portfolio_size=160_000,
            original_largest_position_weight=0.12,
            current_largest_position_weight=0.46,
            volatility_exposure="high",
        )
    )

    assert assessment.overall_drift_level == RiskDriftLevel.HIGH
    assert assessment.drift_score >= 70
    assert any(signal.name == "Risk tolerance drift" for signal in assessment.signals_detected)
    assert any(signal.name == "Portfolio size drift" for signal in assessment.signals_detected)
    assert any(signal.name == "Market regime drift" for signal in assessment.signals_detected)
    assert "Your current situation appears to have changed materially" in assessment.drift_summary


def test_high_risk_profile_can_show_low_volatility_drift():
    profile = _profile(
        portfolio_purpose=PortfolioPurpose.HIGH_CONVICTION_PORTFOLIO,
        risk_tolerance=RiskTolerance.AGGRESSIVE,
        risk_capacity=RiskCapacity.HIGH,
        time_horizon=TimeHorizon.LONG,
    )

    assessment = RiskDriftEngine().assess(
        RiskDriftInput(
            original_profile=profile,
            current_profile=profile,
            volatility_exposure="high",
        )
    )

    assert assessment.overall_drift_level == RiskDriftLevel.LOW
    assert assessment.signals_detected[0].name == "Volatility exposure"
    assert assessment.signals_detected[0].level == RiskDriftLevel.LOW
    assert "current profile accepts it" in assessment.signals_detected[0].what_changed


def test_renderer_avoids_trade_recommendation_language():
    profile = InvestorProfileEngine().create_default_profile()
    assessment = RiskDriftEngine().assess(
        RiskDriftInput(original_profile=profile, current_profile=profile)
    )

    rendered = render_risk_drift_assessment(assessment)

    assert "Risk Drift Assessment" in rendered
    assert "Overall Drift Level" in rendered
    assert "Questions Atlas Should Ask" in rendered
    assert "personalized financial advice" in rendered
    assert "Buy" not in rendered
    assert "Sell" not in rendered
    assert "Strong Buy" not in rendered
    assert "Strong Sell" not in rendered


def test_risk_drift_cli_outputs_assessment(tmp_path):
    portfolio_path = tmp_path / "portfolio.json"
    portfolio_path.write_text(
        json.dumps(
            {
                "positions": [
                    {
                        "ticker": "NVDA",
                        "company": "NVIDIA",
                        "sector": "Semiconductors",
                        "country": "United States",
                        "market_cap": 3_300_000_000_000,
                        "weight": 0.42,
                        "quality_score": 92,
                        "risk_score": 77,
                    },
                    {
                        "ticker": "MSFT",
                        "company": "Microsoft",
                        "sector": "Software",
                        "country": "United States",
                        "market_cap": 3_400_000_000_000,
                        "weight": 0.28,
                        "quality_score": 90,
                        "risk_score": 78,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "risk-drift",
            "analyze",
            "--portfolio",
            str(portfolio_path),
            "--original-portfolio-size",
            "20000",
            "--current-portfolio-size",
            "120000",
            "--volatility",
            "high",
        ],
    )

    assert result.exit_code == 0
    assert "Risk Drift Assessment" in result.output
    assert "Overall Drift Level" in result.output
    assert "Questions Atlas Should Ask" in result.output

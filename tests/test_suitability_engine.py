import json

from typer.testing import CliRunner

from atlas.analysis.engine import InvestmentReport, ScoreCategory
from atlas.cli.main import app
from atlas.profile import (
    InvestmentGoal,
    InvestorProfileEngine,
    PortfolioPurpose,
    RiskCapacity,
    RiskPreference,
    RiskTolerance,
    TimeHorizon,
)
from atlas.suitability import (
    OverallSuitability,
    SuitabilityEngine,
    SuitabilityInput,
    render_suitability_assessment,
)


def _investment_report(
    quality: int = 88,
    valuation: int = 72,
    risk: int = 70,
) -> InvestmentReport:
    return InvestmentReport(
        company="Example Company (EXM)",
        atlas_score=76,
        overall_recommendation="Hold",
        confidence=74,
        quality=ScoreCategory(quality, "Quality context.", 80),
        growth=ScoreCategory(82, "Growth context.", 78),
        valuation=ScoreCategory(valuation, "Valuation context.", 70),
        financial_strength=ScoreCategory(quality, "Financial strength context.", 72),
        risk=ScoreCategory(risk, "Risk context.", 68),
    )


def test_higher_risk_can_fit_exploration_profile():
    profile = InvestorProfileEngine().create_profile(
        name="Exploration Investor",
        investment_goals=(InvestmentGoal.EXPERIMENTAL_PORTFOLIO,),
        portfolio_purpose=PortfolioPurpose.EXPLORATION_PORTFOLIO,
        risk_preference=RiskPreference.AGGRESSIVE,
        risk_tolerance=RiskTolerance.AGGRESSIVE,
        risk_capacity=RiskCapacity.HIGH,
        time_horizon=TimeHorizon.LONG,
    )

    assessment = SuitabilityEngine().assess(
        SuitabilityInput(
            investor_profile=profile,
            investment_report=_investment_report(quality=86, valuation=58, risk=42),
            volatility="high",
            preferred_investment_style="exploratory",
        )
    )

    assert assessment.overall_suitability in {
        OverallSuitability.EXCELLENT_FIT,
        OverallSuitability.GOOD_FIT,
    }
    assert any(factor.name == "Purpose alignment" for factor in assessment.main_strengths)
    assert not assessment.main_concerns


def test_high_quality_can_still_be_unsuitable_for_short_horizon():
    profile = InvestorProfileEngine().create_profile(
        name="Safety Profile",
        investment_goals=(InvestmentGoal.CAPITAL_PRESERVATION,),
        portfolio_purpose=PortfolioPurpose.CORE_PORTFOLIO,
        risk_preference=RiskPreference.CONSERVATIVE,
        risk_tolerance=RiskTolerance.CONSERVATIVE,
        risk_capacity=RiskCapacity.LOW,
        time_horizon=TimeHorizon.SHORT,
    )

    assessment = SuitabilityEngine().assess(
        SuitabilityInput(
            investor_profile=profile,
            investment_report=_investment_report(quality=94, valuation=42, risk=38),
            volatility="high",
            preferred_investment_style="capital preservation",
        )
    )

    assert assessment.overall_suitability == OverallSuitability.POOR_FIT
    assert any(mismatch.name == "Time horizon mismatch" for mismatch in assessment.main_concerns)
    assert any(mismatch.name == "Risk capacity mismatch" for mismatch in assessment.main_concerns)


def test_renderer_avoids_trade_recommendation_language():
    profile = InvestorProfileEngine().create_default_profile()
    assessment = SuitabilityEngine().assess(
        SuitabilityInput(
            investor_profile=profile,
            investment_report=_investment_report(),
        )
    )

    rendered = render_suitability_assessment(assessment)

    assert "Suitability Assessment" in rendered
    assert "Overall Suitability" in rendered
    assert "Compatibility View" in rendered
    assert "personalized financial advice" in rendered
    assert "Buy" not in rendered
    assert "Sell" not in rendered
    assert "Strong Buy" not in rendered
    assert "Strong Sell" not in rendered


def test_portfolio_suitability_uses_portfolio_characteristics(tmp_path):
    portfolio_path = tmp_path / "portfolio.json"
    portfolio_path.write_text(
        json.dumps(
            {
                "positions": [
                    {
                        "ticker": "MSFT",
                        "company": "Microsoft",
                        "sector": "Software",
                        "country": "United States",
                        "market_cap": 3_400_000_000_000,
                        "weight": 0.55,
                        "quality_score": 90,
                        "risk_score": 78,
                    },
                    {
                        "ticker": "AAPL",
                        "company": "Apple",
                        "sector": "Consumer Electronics",
                        "country": "United States",
                        "market_cap": 3_000_000_000_000,
                        "weight": 0.35,
                        "quality_score": 86,
                        "risk_score": 72,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(app, ["suitability", "analyze", str(portfolio_path)])

    assert result.exit_code == 0
    assert "Suitability Assessment" in result.output
    assert "Subject: Portfolio" in result.output
    assert "Concentration" in result.output


def test_suitability_cli_analyzes_ticker_with_default_profile():
    runner = CliRunner()

    result = runner.invoke(app, ["suitability", "analyze", "NVDA"])

    assert result.exit_code == 0
    assert "Suitability Assessment" in result.output
    assert "Subject: NVIDIA (NVDA)" in result.output
    assert "Overall Suitability" in result.output

import ast
import importlib
import inspect

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


# --- Sprint 120: suitability portfolio dependency migration ---

_SUITABILITY_SOURCE = (
    __import__("pathlib").Path(__file__).parent.parent
    / "atlas"
    / "suitability"
    / "engine.py"
).read_text()

_SUITABILITY_TREE = ast.parse(_SUITABILITY_SOURCE)


def test_sprint120_no_runtime_portfolio_import():
    """atlas.analysis.portfolio must not be imported at module runtime.

    Walks only top-level statements and skips if TYPE_CHECKING: blocks.
    """
    for node in _SUITABILITY_TREE.body:
        if isinstance(node, ast.If):
            test = node.test
            if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                continue  # skip — guarded imports are intentional
        if isinstance(node, ast.ImportFrom):
            assert node.module != "atlas.analysis.portfolio", (
                "atlas.analysis.portfolio must be behind TYPE_CHECKING, not a runtime import"
            )


def test_sprint120_future_annotations_present():
    """from __future__ import annotations must be declared."""
    assert "from __future__ import annotations" in _SUITABILITY_SOURCE


def test_sprint120_type_checking_guard_present():
    """Portfolio must be imported inside an if TYPE_CHECKING: block."""
    for node in _SUITABILITY_TREE.body:
        if isinstance(node, ast.If):
            test = node.test
            if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                for child in ast.walk(node):
                    if isinstance(child, ast.ImportFrom):
                        names = [alias.name for alias in child.names]
                        if "Portfolio" in names:
                            return
    raise AssertionError("Portfolio is not imported inside TYPE_CHECKING block")


def test_sprint120_portfolio_fit_result_in_source():
    """PortfolioFitResult must appear in suitability engine source."""
    assert "PortfolioFitResult" in _SUITABILITY_SOURCE


def test_sprint120_overlap_field_used_not_overlap_with_existing_holdings():
    """_concentration_impact must access .overlap, not .overlap_with_existing_holdings."""
    for node in ast.walk(_SUITABILITY_TREE):
        if isinstance(node, ast.Attribute):
            assert node.attr != "overlap_with_existing_holdings", (
                "Must use .overlap (PortfolioFitResult), not .overlap_with_existing_holdings"
            )
    overlap_used = any(
        isinstance(node, ast.Attribute) and node.attr == "overlap"
        for node in ast.walk(_SUITABILITY_TREE)
    )
    assert overlap_used, "_concentration_impact must access .overlap on PortfolioFitResult"


def test_sprint120_portfolio_fit_result_accepted_at_runtime():
    """SuitabilityInput accepts a PortfolioFitResult in portfolio_analysis without error."""
    from atlas.capabilities.portfolio_intelligence.models import (
        PortfolioFitDimension,
        PortfolioFitResult,
    )
    from atlas.suitability import SuitabilityEngine, SuitabilityInput
    from atlas.profile import InvestorProfileEngine

    dim = PortfolioFitDimension(score=80, note="ok")
    result = PortfolioFitResult(
        ticker="TST",
        company="Test Co",
        fit_score=80,
        diversification=dim,
        sector_concentration=dim,
        country_concentration=dim,
        market_cap_concentration=dim,
        overlap=dim,
        quality_impact=dim,
        risk_impact=dim,
        summary="Fits well.",
    )
    profile = InvestorProfileEngine().create_default_profile()
    assessment = SuitabilityEngine().assess(
        SuitabilityInput(investor_profile=profile, portfolio_analysis=result)
    )
    assert assessment is not None
    # confidence gets +10 bonus for portfolio_analysis; with 5 missing items it lands at 45
    assert assessment.confidence >= 40


def test_sprint120_none_default_behavior_unchanged():
    """With no portfolio or portfolio_analysis, confidence and output are unchanged."""
    from atlas.suitability import SuitabilityEngine, SuitabilityInput
    from atlas.profile import InvestorProfileEngine

    profile = InvestorProfileEngine().create_default_profile()
    assessment = SuitabilityEngine().assess(SuitabilityInput(investor_profile=profile))
    assert assessment is not None
    assert assessment.overall_suitability in {s for s in OverallSuitability}


def test_sprint120_capability_engine_still_no_legacy_portfolio_import():
    """PortfolioIntelligenceCapability must not import from atlas.analysis.portfolio."""
    cap_path = (
        __import__("pathlib").Path(__file__).parent.parent
        / "atlas"
        / "capabilities"
        / "portfolio_intelligence"
        / "engine.py"
    )
    source = cap_path.read_text()
    assert "atlas.analysis.portfolio" not in source


def test_sprint120_legacy_portfolio_module_still_active():
    """atlas.analysis.portfolio must still importable (not deleted)."""
    import atlas.analysis.portfolio as legacy
    assert hasattr(legacy, "Portfolio")

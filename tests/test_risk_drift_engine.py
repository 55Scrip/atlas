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


# ── Sprint 119: risk drift no longer runtime-imports atlas.analysis.portfolio ─

def test_sprint119_no_direct_runtime_import_of_portfolio_or_portfolio_analysis():
    """Portfolio and PortfolioAnalysis must only appear under TYPE_CHECKING."""
    import ast
    import pathlib

    source = pathlib.Path("atlas/risk_drift/engine.py").read_text()
    tree = ast.parse(source)

    guarded_linenos: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test = node.test
            is_type_checking = (
                (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING")
                or (isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING")
            )
            if is_type_checking:
                for child in ast.walk(node):
                    if hasattr(child, "lineno"):
                        guarded_linenos.add(child.lineno)

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and "analysis.portfolio" in node.module:
                assert node.lineno in guarded_linenos, (
                    f"Line {node.lineno}: runtime import from {node.module!r} "
                    "found in risk_drift/engine.py — must be under TYPE_CHECKING"
                )


def test_sprint119_future_annotations_in_risk_drift_engine():
    import pathlib
    source = pathlib.Path("atlas/risk_drift/engine.py").read_text()
    assert "from __future__ import annotations" in source


def test_sprint119_portfolio_fit_result_used_for_portfolio_analysis_field():
    import pathlib
    source = pathlib.Path("atlas/risk_drift/engine.py").read_text()
    assert "PortfolioFitResult" in source
    assert "PortfolioAnalysis" not in source or "TYPE_CHECKING" in source


def test_sprint119_concentration_check_uses_overlap_field():
    import ast, pathlib
    source = pathlib.Path("atlas/risk_drift/engine.py").read_text()
    # verify analysis.overlap is accessed (not analysis.overlap_with_existing_holdings)
    assert "analysis.overlap," in source
    # the old field name must not appear as an attribute access in the AST
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "overlap_with_existing_holdings":
            raise AssertionError("overlap_with_existing_holdings attribute access still present")


def test_sprint119_risk_drift_accepts_portfolio_fit_result_for_concentration():
    """_concentration_in_portfolio_analysis works with a real PortfolioFitResult."""
    from atlas.adapters.portfolio import (
        legacy_portfolio_to_domain_portfolio,
        portfolio_fit_input_from_profile,
    )
    from atlas.analysis.portfolio import Portfolio as LegacyPortfolio
    from atlas.capabilities.portfolio_intelligence import PortfolioIntelligenceCapability
    from atlas.providers import MockCompanyAnalysisProvider

    provider = MockCompanyAnalysisProvider()
    profile = provider.get_portfolio_profile("NVDA")
    legacy = LegacyPortfolio.from_mapping(
        {
            "positions": [
                {
                    "ticker": "NVDA",
                    "company": "NVIDIA",
                    "sector": "Semiconductors",
                    "country": "United States",
                    "market_cap": 3_300_000_000_000,
                    "weight": 0.80,
                    "quality_score": 92,
                    "risk_score": 77,
                }
            ]
        }
    )
    shared = legacy_portfolio_to_domain_portfolio(legacy)
    fit_input = portfolio_fit_input_from_profile(profile)
    result = PortfolioIntelligenceCapability().analyze(shared, fit_input)

    # RiskDriftInput now accepts PortfolioFitResult for current_portfolio_analysis
    ri = RiskDriftInput(
        original_profile=_profile(
            portfolio_purpose=PortfolioPurpose.CORE_PORTFOLIO,
            risk_tolerance=RiskTolerance.BALANCED,
            risk_capacity=RiskCapacity.MEDIUM,
            time_horizon=TimeHorizon.LONG,
        ),
        current_profile=_profile(
            portfolio_purpose=PortfolioPurpose.CORE_PORTFOLIO,
            risk_tolerance=RiskTolerance.BALANCED,
            risk_capacity=RiskCapacity.MEDIUM,
            time_horizon=TimeHorizon.LONG,
        ),
        current_portfolio_analysis=result,
    )
    assessment = RiskDriftEngine().assess(ri)
    # Concentration signal may fire because NVDA is 80% concentration
    assert assessment is not None
    assert isinstance(assessment.drift_score, int)


def test_sprint119_risk_drift_behavior_unchanged_without_portfolio_analysis():
    """Risk drift works correctly when current_portfolio_analysis is None (normal case)."""
    ri = RiskDriftInput(
        original_profile=_profile(
            portfolio_purpose=PortfolioPurpose.CORE_PORTFOLIO,
            risk_tolerance=RiskTolerance.BALANCED,
            risk_capacity=RiskCapacity.MEDIUM,
            time_horizon=TimeHorizon.LONG,
        ),
        current_profile=_profile(
            portfolio_purpose=PortfolioPurpose.CORE_PORTFOLIO,
            risk_tolerance=RiskTolerance.BALANCED,
            risk_capacity=RiskCapacity.MEDIUM,
            time_horizon=TimeHorizon.LONG,
        ),
    )
    assessment = RiskDriftEngine().assess(ri)
    assert assessment.overall_drift_level == RiskDriftLevel.NONE
    assert assessment.drift_score == 0


def test_sprint119_no_advisory_language_in_risk_drift_output():
    ri = RiskDriftInput(
        original_profile=_profile(
            portfolio_purpose=PortfolioPurpose.CORE_PORTFOLIO,
            risk_tolerance=RiskTolerance.GROWTH,
            risk_capacity=RiskCapacity.HIGH,
            time_horizon=TimeHorizon.LONG,
        ),
        current_profile=_profile(
            portfolio_purpose=PortfolioPurpose.CORE_PORTFOLIO,
            risk_tolerance=RiskTolerance.CONSERVATIVE,
            risk_capacity=RiskCapacity.LOW,
            time_horizon=TimeHorizon.SHORT,
        ),
    )
    assessment = RiskDriftEngine().assess(ri)
    rendered = render_risk_drift_assessment(assessment)
    forbidden = ("strong buy", "strong sell", "buy now", "sell now", "price target", "guaranteed")
    lowered = rendered.lower()
    for term in forbidden:
        assert term not in lowered, f"Forbidden term {term!r} in risk drift output"


def test_sprint119_legacy_portfolio_module_still_active():
    from atlas.analysis.portfolio import (  # noqa: F401
        Portfolio,
        PortfolioAnalysis,
        PortfolioIntelligenceEngine,
    )
    assert True


def test_sprint119_capability_engine_still_no_legacy_portfolio_import():
    import pathlib
    source = pathlib.Path("atlas/capabilities/portfolio_intelligence/engine.py").read_text()
    assert "atlas.analysis.portfolio" not in source

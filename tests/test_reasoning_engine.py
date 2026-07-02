from typer.testing import CliRunner

from atlas.analysis.report import build_investment_report
from atlas.cli.main import app
from atlas.economics import EconomicSignalsEngine
from atlas.market import MarketHealthEngine
from atlas.monitoring import MonitoringEngine
from atlas.providers import MockCompanyAnalysisProvider
from atlas.reasoning import ReasoningEngine, ReasoningInput, render_reasoning_report
from atlas.themes import ThemeEngine


def _default_reasoning_input() -> ReasoningInput:
    provider = MockCompanyAnalysisProvider()
    return ReasoningInput(
        company_analysis=build_investment_report(provider.get_company_analysis("NVDA")),
        theme_analysis=ThemeEngine().analyze("AI infrastructure"),
        monitoring_report=MonitoringEngine().monitor_company("NVDA", provider),
        economic_signals=EconomicSignalsEngine().analyze(),
        market_health=MarketHealthEngine().analyze(),
    )


def test_reasoning_engine_synthesizes_existing_outputs():
    report = ReasoningEngine().analyze(_default_reasoning_input())

    assert "bullish factor" in report.executive_summary
    assert report.bullish_factors
    assert report.bearish_factors
    assert report.signals_trusted_most
    assert report.signals_trusted_least
    assert report.confidence > 0
    assert report.monitor_next


def test_reasoning_engine_reports_missing_inputs_without_inventing_facts():
    report = ReasoningEngine().analyze(ReasoningInput())

    assert report.confidence == 30
    assert any(
        item.startswith("Company Analysis was not supplied")
        for item in report.areas_of_uncertainty
    )
    assert report.bullish_factors == ()
    assert report.bearish_factors == ()


def test_reasoning_renderer_includes_required_sections_and_no_trade_advice():
    report = ReasoningEngine().analyze(_default_reasoning_input())

    rendered = render_reasoning_report(report)

    assert "Executive Summary" in rendered
    assert "Bullish Factors" in rendered
    assert "Bearish Factors" in rendered
    assert "Areas of Uncertainty" in rendered
    assert "Signals Atlas Trusts Most" in rendered
    assert "Signals Atlas Trusts Least" in rendered
    assert "Alternative Scenarios" in rendered
    assert "What Could Invalidate The Thesis" in rendered
    assert "What Atlas Will Monitor Next" in rendered
    assert "buy/sell advice" in rendered
    assert "Strong Buy" not in rendered
    assert "Strong Sell" not in rendered


def test_reasoning_cli_command_is_retired():
    # Sprint 87: atlas reason analyze command body retired — no longer a valid command
    runner = CliRunner()
    result = runner.invoke(app, ["reason", "analyze"])
    assert result.exit_code != 0


# ── Sprint 118: reasoning no longer directly imports atlas.analysis.portfolio ─

def test_sprint118_reasoning_engine_no_direct_runtime_import_of_portfolio_analysis():
    """PortfolioAnalysis must only appear under TYPE_CHECKING, not as a runtime import."""
    import ast
    import pathlib

    source = pathlib.Path("atlas/reasoning/engine.py").read_text()
    tree = ast.parse(source)

    # Collect line numbers inside TYPE_CHECKING guards
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
                    "found in reasoning/engine.py — must be under TYPE_CHECKING"
                )


def test_sprint118_reasoning_engine_has_future_annotations():
    import pathlib
    source = pathlib.Path("atlas/reasoning/engine.py").read_text()
    assert "from __future__ import annotations" in source


def test_sprint118_type_checking_guard_present_in_reasoning_engine():
    import pathlib
    source = pathlib.Path("atlas/reasoning/engine.py").read_text()
    assert "TYPE_CHECKING" in source
    assert "if TYPE_CHECKING:" in source


def test_sprint118_reasoning_behavior_unchanged_with_portfolio_analysis_none():
    """Reasoning engine operates correctly when portfolio_analysis is None (default)."""
    report = ReasoningEngine().analyze(ReasoningInput())
    assert any("Portfolio Analysis was not supplied" in item for item in report.areas_of_uncertainty)


def test_sprint118_reasoning_portfolio_analysis_field_still_accepted():
    """ReasoningInput still accepts a portfolio_analysis value (duck-typed at runtime)."""
    from atlas.analysis.portfolio import Portfolio, PortfolioIntelligenceEngine
    from atlas.providers import MockCompanyAnalysisProvider

    provider = MockCompanyAnalysisProvider()
    profile = provider.get_portfolio_profile("NVDA")
    portfolio = Portfolio.from_mapping(
        {
            "positions": [
                {
                    "ticker": "AAPL",
                    "company": "Apple",
                    "sector": "Consumer Electronics",
                    "country": "United States",
                    "market_cap": 3_000_000_000_000,
                    "weight": 1.0,
                    "quality_score": 88,
                    "risk_score": 65,
                }
            ]
        }
    )
    analysis = PortfolioIntelligenceEngine().analyze(portfolio, profile)
    ri = ReasoningInput(portfolio_analysis=analysis)
    report = ReasoningEngine().analyze(ri)
    # portfolio_analysis evidence should appear in collected signals
    assert any(e.source == "Portfolio Analysis" for e in report.signals_trusted_most + report.signals_trusted_least)


def test_sprint118_capability_engine_still_no_legacy_portfolio_import():
    import pathlib
    source = pathlib.Path("atlas/capabilities/portfolio_intelligence/engine.py").read_text()
    assert "atlas.analysis.portfolio" not in source


def test_sprint118_legacy_portfolio_module_remains_active():
    from atlas.analysis.portfolio import (  # noqa: F401
        CompanyPortfolioProfile,
        Portfolio,
        PortfolioAnalysis,
        PortfolioIntelligenceEngine,
        PortfolioPosition,
    )
    assert True

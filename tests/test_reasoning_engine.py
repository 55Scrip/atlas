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


def test_reasoning_cli_outputs_report():
    runner = CliRunner()

    result = runner.invoke(app, ["reason", "analyze"])

    assert result.exit_code == 0
    assert "Atlas Reasoning Report" in result.output
    assert "Executive Summary" in result.output
    assert "What Atlas Will Monitor Next" in result.output

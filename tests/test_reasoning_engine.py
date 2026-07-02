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
    """Sprint 131: atlas.analysis.portfolio must not appear anywhere in reasoning/engine.py."""
    import pathlib
    source = pathlib.Path("atlas/reasoning/engine.py").read_text()
    assert "atlas.analysis.portfolio" not in source, (
        "reasoning/engine.py must not import from atlas.analysis.portfolio after Sprint 131"
    )


def test_sprint118_reasoning_engine_has_future_annotations():
    import pathlib
    source = pathlib.Path("atlas/reasoning/engine.py").read_text()
    assert "from __future__ import annotations" in source


def test_sprint131_reasoning_engine_uses_portfolio_fit_result():
    """Sprint 131: reasoning/engine.py must import PortfolioFitResult, not PortfolioAnalysis."""
    import pathlib
    source = pathlib.Path("atlas/reasoning/engine.py").read_text()
    assert "PortfolioFitResult" in source
    assert "PortfolioAnalysis" not in source


def test_sprint118_reasoning_behavior_unchanged_with_portfolio_analysis_none():
    """Reasoning engine operates correctly when portfolio_analysis is None (default)."""
    report = ReasoningEngine().analyze(ReasoningInput())
    assert any("Portfolio Analysis was not supplied" in item for item in report.areas_of_uncertainty)


def test_sprint118_reasoning_portfolio_analysis_field_still_accepted():
    """Sprint 131: ReasoningInput.portfolio_analysis accepts PortfolioFitResult."""
    from atlas.capabilities.portfolio_intelligence import (
        PortfolioFitDimension,
        PortfolioFitResult,
    )

    dim = PortfolioFitDimension(score=75, note="test note")
    analysis = PortfolioFitResult(
        ticker="NVDA",
        company="NVIDIA",
        fit_score=75,
        diversification=dim,
        sector_concentration=dim,
        country_concentration=dim,
        market_cap_concentration=dim,
        overlap=dim,
        quality_impact=dim,
        risk_impact=dim,
        summary="Good diversification across sectors.",
    )
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
        Portfolio,
        PortfolioPosition,
    )
    assert True


# ---------------------------------------------------------------------------
# Sprint 131: Reasoning PortfolioAnalysis → PortfolioFitResult migration
# ---------------------------------------------------------------------------

def test_sprint131_reasoning_summary_used_not_final_reasoning() -> None:
    """Sprint 131: reasoning/engine.py must use .summary not .final_reasoning."""
    import pathlib
    source = pathlib.Path("atlas/reasoning/engine.py").read_text()
    non_comment = [l for l in source.splitlines() if not l.strip().startswith("#")]
    assert not any("final_reasoning" in l for l in non_comment), (
        "reasoning/engine.py must not reference .final_reasoning after Sprint 131"
    )
    assert any("analysis.summary" in l for l in non_comment), (
        "reasoning/engine.py must use analysis.summary (PortfolioFitResult field)"
    )


def test_sprint131_reasoning_note_used_not_reasoning_field() -> None:
    """Sprint 131: reasoning/engine.py must use .note not .reasoning on dimension fields."""
    import pathlib
    source = pathlib.Path("atlas/reasoning/engine.py").read_text()
    non_comment = [l for l in source.splitlines() if not l.strip().startswith("#")]
    assert not any("sector_concentration.reasoning" in l for l in non_comment), (
        "reasoning/engine.py must not access .reasoning on PortfolioFitDimension after Sprint 131"
    )
    assert any("sector_concentration.note" in l for l in non_comment), (
        "reasoning/engine.py must use sector_concentration.note (PortfolioFitDimension field)"
    )


def test_sprint131_reasoning_fit_score_used_not_portfolio_score() -> None:
    """Sprint 131: reasoning/engine.py must use .fit_score not .portfolio_score."""
    import pathlib
    source = pathlib.Path("atlas/reasoning/engine.py").read_text()
    non_comment = [l for l in source.splitlines() if not l.strip().startswith("#")]
    assert not any("portfolio_score" in l for l in non_comment), (
        "reasoning/engine.py must not reference .portfolio_score after Sprint 131"
    )
    assert any("fit_score" in l for l in non_comment), (
        "reasoning/engine.py must use .fit_score (PortfolioFitResult field)"
    )


def test_sprint131_reasoning_with_portfolio_fit_result_produces_evidence() -> None:
    """Sprint 131: Portfolio Analysis evidence source appears when PortfolioFitResult is supplied."""
    from atlas.capabilities.portfolio_intelligence import PortfolioFitDimension, PortfolioFitResult

    dim = PortfolioFitDimension(score=80, note="no sector concentration concern")
    result = PortfolioFitResult(
        ticker="NVDA",
        company="NVIDIA",
        fit_score=80,
        diversification=dim,
        sector_concentration=dim,
        country_concentration=dim,
        market_cap_concentration=dim,
        overlap=dim,
        quality_impact=dim,
        risk_impact=dim,
        summary="Strong fit across all dimensions.",
    )
    report = ReasoningEngine().analyze(ReasoningInput(portfolio_analysis=result))
    all_evidence = report.signals_trusted_most + report.signals_trusted_least
    assert any(e.source == "Portfolio Analysis" for e in all_evidence)


def test_sprint131_reasoning_portfolio_concentration_bearish_factor() -> None:
    """Sprint 131: sector_concentration.score < 70 triggers Portfolio concentration bearish factor."""
    from atlas.capabilities.portfolio_intelligence import PortfolioFitDimension, PortfolioFitResult

    low_sector = PortfolioFitDimension(score=55, note="high sector concentration")
    high_dim = PortfolioFitDimension(score=85, note="healthy")
    result = PortfolioFitResult(
        ticker="NVDA",
        company="NVIDIA",
        fit_score=60,
        diversification=high_dim,
        sector_concentration=low_sector,
        country_concentration=high_dim,
        market_cap_concentration=high_dim,
        overlap=high_dim,
        quality_impact=high_dim,
        risk_impact=high_dim,
        summary="High sector concentration is a concern.",
    )
    report = ReasoningEngine().analyze(ReasoningInput(portfolio_analysis=result))
    bearish_titles = [f.title for f in report.bearish_factors]
    assert "Portfolio concentration" in bearish_titles


def test_sprint132_portfolio_analysis_signal_recommendation_deleted() -> None:
    """Sprint 132: PortfolioAnalysis, PortfolioSignal, PortfolioRecommendation deleted from portfolio.py."""
    import pytest
    with pytest.raises(ImportError):
        from atlas.analysis.portfolio import PortfolioAnalysis  # noqa: F401
    with pytest.raises(ImportError):
        from atlas.analysis.portfolio import PortfolioSignal  # noqa: F401
    with pytest.raises(ImportError):
        from atlas.analysis.portfolio import PortfolioRecommendation  # noqa: F401

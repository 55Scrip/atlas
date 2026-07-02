import ast
import json
import pathlib

from typer.testing import CliRunner

from atlas.adapters.portfolio import Portfolio, PortfolioPosition
from atlas.cli.main import app
from atlas.intelligence import (
    IntelligenceContext,
    IntelligenceEngine,
    IntelligenceInput,
    render_intelligence_report,
)
from atlas.providers import MockCompanyAnalysisProvider

_INTEL_SOURCE = (
    pathlib.Path(__file__).parent.parent / "atlas" / "intelligence" / "engine.py"
).read_text()
_INTEL_TREE = ast.parse(_INTEL_SOURCE)


def test_intelligence_engine_combines_core_atlas_outputs():
    report = IntelligenceEngine().analyze(
        IntelligenceInput(
            ticker="NVDA",
            provider=MockCompanyAnalysisProvider(),
        )
    )

    assert report.ticker == "NVDA"
    assert report.investment_report.company == "NVIDIA (NVDA)"
    assert report.theme_analysis.theme.value == "AI infrastructure"
    assert report.market_regime_analysis.regime.value == "Neutral"
    assert report.market_health_report.overall_market_health == "Fragile"
    assert report.decision_result.ticker == "NVDA"
    assert report.confidence > 0


def test_intelligence_report_includes_required_sections_without_trade_labels():
    report = IntelligenceEngine().analyze(
        IntelligenceInput(
            ticker="NVDA",
            provider=MockCompanyAnalysisProvider(),
        )
    )

    rendered = render_intelligence_report(report)

    assert "Executive Summary" in rendered
    assert "Structural Tailwinds" in rendered
    assert "Current Market Environment" in rendered
    assert "Company Positioning" in rendered
    assert "Portfolio Impact" in rendered
    assert "Risk Assessment" in rendered
    assert "Atlas Conclusion" in rendered
    assert "What Atlas Is Monitoring" in rendered
    assert "What Could Change Atlas' View" in rendered
    assert "Strong Buy" not in rendered
    assert "Strong Sell" not in rendered
    assert "Buy" not in rendered
    assert "Sell" not in rendered


def test_intelligence_engine_uses_portfolio_context_when_supplied():
    portfolio = Portfolio(
        positions=(
            PortfolioPosition(
                ticker="MSFT",
                company="Microsoft",
                sector="Software",
                country="United States",
                market_cap=3_400_000_000_000,
                weight=0.20,
                quality_score=90,
                risk_score=78,
            ),
        )
    )

    report = IntelligenceEngine().analyze(
        IntelligenceInput(
            ticker="NVDA",
            provider=MockCompanyAnalysisProvider(),
            context=IntelligenceContext(portfolio=portfolio),
        )
    )

    assert report.portfolio_analysis is not None
    assert any("Diversification:" in item for item in report.portfolio_impact)
    assert any("Overlap:" in item for item in report.portfolio_impact)


def test_intelligence_cli_outputs_ticker_report():
    runner = CliRunner()

    result = runner.invoke(app, ["intelligence", "analyze", "NVDA"])

    assert result.exit_code == 0
    assert "Atlas Intelligence Report" in result.output
    assert "Ticker: NVDA" in result.output
    assert "Executive Summary" in result.output


def test_intelligence_cli_accepts_portfolio_and_ticker(tmp_path):
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
                        "market_cap": 3400000000000,
                        "weight": 0.2,
                        "quality_score": 90,
                        "risk_score": 78,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(app, ["intelligence", "analyze", str(portfolio_path), "NVDA"])

    assert result.exit_code == 0
    assert "Portfolio Impact" in result.output
    assert "Portfolio fit remains uncertain" not in result.output


# ---------------------------------------------------------------------------
# Sprint 125: Intelligence portfolio dependency audit and migration
# ---------------------------------------------------------------------------

def _intel_top_level_legacy_imports() -> list[str]:
    """Return atlas.analysis.portfolio runtime imports (not inside TYPE_CHECKING)."""
    results = []
    for node in _INTEL_TREE.body:
        if isinstance(node, ast.If):
            test = node.test
            if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                continue
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if "atlas.analysis.portfolio" in module:
                results.append(module)
    return results


def test_sprint125_intelligence_engine_no_runtime_legacy_portfolio_import():
    """intelligence/engine.py must not runtime-import from atlas.analysis.portfolio."""
    assert _intel_top_level_legacy_imports() == []


def test_sprint125_intelligence_engine_no_portfolio_intelligence_engine():
    """PortfolioIntelligenceEngine must not appear in live code in intelligence/engine.py."""
    non_comment_lines = [
        line for line in _INTEL_SOURCE.splitlines()
        if not line.strip().startswith("#")
    ]
    assert not any("PortfolioIntelligenceEngine" in line for line in non_comment_lines)


def test_sprint125_intelligence_engine_no_portfolio_analysis_runtime():
    """PortfolioAnalysis must not appear in live code in intelligence/engine.py."""
    non_comment_lines = [
        line for line in _INTEL_SOURCE.splitlines()
        if not line.strip().startswith("#")
    ]
    assert not any("PortfolioAnalysis" in line for line in non_comment_lines)


def test_sprint125_intelligence_engine_uses_capability():
    """intelligence/engine.py must import and use PortfolioIntelligenceCapability."""
    assert "PortfolioIntelligenceCapability" in _INTEL_SOURCE


def test_sprint125_intelligence_engine_uses_adapters():
    """Sprint 137: intelligence/engine.py uses adapter; calls provider directly."""
    assert "legacy_portfolio_to_domain_portfolio" in _INTEL_SOURCE
    assert "portfolio_fit_input_from_profile" not in _INTEL_SOURCE
    assert "get_portfolio_profile" in _INTEL_SOURCE


def test_sprint125_intelligence_engine_type_checking_guard():
    """Portfolio and PortfolioFitResult must appear inside a TYPE_CHECKING block."""
    source = _INTEL_SOURCE
    assert "TYPE_CHECKING" in source
    assert "PortfolioFitResult" in source
    assert "from __future__ import annotations" in source


def test_sprint125_intelligence_engine_uses_fit_score_not_portfolio_score():
    """intelligence/engine.py must use .fit_score, not .portfolio_score."""
    assert "portfolio_score" not in _INTEL_SOURCE
    assert "fit_score" in _INTEL_SOURCE


def test_sprint125_intelligence_engine_uses_overlap_not_legacy_field():
    """intelligence/engine.py must use .overlap.note, not .overlap_with_existing_holdings."""
    assert "overlap_with_existing_holdings" not in _INTEL_SOURCE
    assert ".overlap" in _INTEL_SOURCE


def test_sprint125_intelligence_engine_uses_note_not_reasoning_for_portfolio():
    """intelligence/engine.py _portfolio_impact must use .note (PortfolioFitDimension)."""
    assert "diversification.note" in _INTEL_SOURCE
    assert "quality_impact.note" in _INTEL_SOURCE
    assert "risk_impact.note" in _INTEL_SOURCE


def test_sprint125_portfolio_fit_result_stored_on_intelligence_report():
    """When portfolio is supplied, report.portfolio_analysis is a PortfolioFitResult."""
    from atlas.capabilities.portfolio_intelligence import PortfolioFitResult

    portfolio = Portfolio(
        positions=(
            PortfolioPosition(
                ticker="MSFT",
                company="Microsoft",
                sector="Software",
                country="United States",
                market_cap=3_400_000_000_000,
                weight=0.20,
                quality_score=90,
                risk_score=78,
            ),
        )
    )
    report = IntelligenceEngine().analyze(
        IntelligenceInput(
            ticker="NVDA",
            provider=MockCompanyAnalysisProvider(),
            context=IntelligenceContext(portfolio=portfolio),
        )
    )
    assert report.portfolio_analysis is not None
    assert isinstance(report.portfolio_analysis, PortfolioFitResult)


def test_sprint125_capability_injection_works():
    """IntelligenceEngine accepts a PortfolioIntelligenceCapability via constructor."""
    from atlas.capabilities.portfolio_intelligence import PortfolioIntelligenceCapability

    cap = PortfolioIntelligenceCapability()
    engine = IntelligenceEngine(portfolio_fit_capability=cap)
    assert engine.portfolio_fit_capability is cap


def test_sprint125_no_portfolio_engine_kwarg_in_conversation_engine():
    """conversation/engine.py must not pass portfolio_engine= to IntelligenceEngine."""
    conv_source = (
        pathlib.Path(__file__).parent.parent / "atlas" / "conversation" / "engine.py"
    ).read_text()
    assert "portfolio_engine=self.portfolio_engine" not in conv_source

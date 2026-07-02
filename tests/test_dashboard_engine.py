import ast
import json
import pathlib

from typer.testing import CliRunner

from atlas.adapters.portfolio import Portfolio
from atlas.cli.main import app
from atlas.dashboard import DashboardEngine, DashboardInput, render_dashboard
from atlas.profile import InvestorProfileEngine
from atlas.providers import MockCompanyAnalysisProvider

_DASH_SOURCE = (
    pathlib.Path(__file__).parent.parent / "atlas" / "dashboard" / "engine.py"
).read_text()
_DASH_TREE = ast.parse(_DASH_SOURCE)


def _portfolio() -> Portfolio:
    return Portfolio.from_mapping(
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
    )


def test_dashboard_builds_required_sections_without_portfolio():
    summary = DashboardEngine().build()

    section_titles = {section.title for section in summary.sections}

    assert summary.title == "Atlas Home Dashboard"
    assert "Good day" in summary.greeting
    assert "Welcome" in section_titles
    assert "Portfolio Overview" in section_titles
    assert "Market Overview" in section_titles
    assert "Themes To Watch" in section_titles
    assert len(summary.todays_observations) >= 3
    assert len(summary.monitoring_items) >= 5
    assert "Has anything important changed?" in summary.suggested_questions


def test_dashboard_uses_portfolio_context_for_overview():
    profile = InvestorProfileEngine().create_default_profile(name="Atlas User")

    summary = DashboardEngine().build(
        DashboardInput(
            investor_profile=profile,
            portfolio=_portfolio(),
            provider=MockCompanyAnalysisProvider(),
            target_ticker="AAPL",
        )
    )

    rendered = render_dashboard(summary)

    assert "Atlas User" in rendered
    assert "Largest Position: NVDA at 42.0%" in rendered
    assert "Concentration Level: High" in rendered
    assert "Target Portfolio Fit" in rendered
    assert "Is my portfolio still aligned with my goals?" in rendered


def test_dashboard_language_avoids_recommendation_guardrails():
    rendered = render_dashboard(DashboardEngine().build())

    assert "Strong Buy" not in rendered
    assert "Strong Sell" not in rendered
    assert "Buy" not in rendered
    assert "Sell" not in rendered
    assert "Worth monitoring" in rendered
    assert "May deserve attention" in rendered or "Appears stable" in rendered


def test_dashboard_portfolio_fit_card_uses_capability() -> None:
    """Sprint 115: portfolio-fit card is produced by PortfolioIntelligenceCapability."""
    import ast
    from pathlib import Path
    engine_file = Path(__file__).resolve().parent.parent / "atlas" / "dashboard" / "engine.py"
    tree = ast.parse(engine_file.read_text())
    capability_imported = any(
        isinstance(node, ast.ImportFrom)
        and node.module is not None
        and "portfolio_intelligence" in node.module
        and any(alias.name == "PortfolioIntelligenceCapability" for alias in node.names)
        for node in ast.walk(tree)
    )
    assert capability_imported, "dashboard/engine.py must import PortfolioIntelligenceCapability"


def test_dashboard_portfolio_fit_card_score_in_range() -> None:
    """Sprint 115: Target Portfolio Fit card shows a score between 0 and 100."""
    profile = InvestorProfileEngine().create_default_profile(name="Atlas User")
    summary = DashboardEngine().build(
        DashboardInput(
            investor_profile=profile,
            portfolio=_portfolio(),
            provider=MockCompanyAnalysisProvider(),
            target_ticker="AAPL",
        )
    )
    portfolio_section = next(s for s in summary.sections if s.title == "Portfolio Overview")
    fit_card = next((c for c in portfolio_section.cards if c.title == "Target Portfolio Fit"), None)
    assert fit_card is not None
    score_str = fit_card.value.replace("/100", "")
    score = int(score_str)
    assert 0 <= score <= 100


def test_dashboard_portfolio_fit_card_has_no_recommendation_language() -> None:
    """Sprint 115: portfolio-fit card must not contain advisory language."""
    profile = InvestorProfileEngine().create_default_profile(name="Atlas User")
    summary = DashboardEngine().build(
        DashboardInput(
            investor_profile=profile,
            portfolio=_portfolio(),
            provider=MockCompanyAnalysisProvider(),
            target_ticker="AAPL",
        )
    )
    rendered = render_dashboard(summary)
    for term in ("Strong Add", "Strong Buy", "Buy", "Sell", "Avoid", "Reduce"):
        assert term not in rendered, f"Forbidden term '{term}' found in dashboard output"


def test_dashboard_portfolio_fit_capability_is_injected() -> None:
    """Sprint 115: portfolio_fit_capability can be injected into DashboardEngine."""
    from atlas.capabilities.portfolio_intelligence import PortfolioIntelligenceCapability
    cap = PortfolioIntelligenceCapability()
    engine = DashboardEngine(portfolio_fit_capability=cap)
    assert engine.portfolio_fit_capability is cap


def test_dashboard_portfolio_fit_absent_without_target_ticker() -> None:
    """Sprint 115: Target Portfolio Fit card not present when no target_ticker."""
    summary = DashboardEngine().build(
        DashboardInput(
            portfolio=_portfolio(),
            provider=MockCompanyAnalysisProvider(),
        )
    )
    portfolio_section = next(s for s in summary.sections if s.title == "Portfolio Overview")
    fit_card = next((c for c in portfolio_section.cards if c.title == "Target Portfolio Fit"), None)
    assert fit_card is None


def test_dashboard_portfolio_fit_enriched_fields_carried_through() -> None:
    """Sprint 115: adapter carries quality/risk/market_cap → full parity in capability."""
    from atlas.adapters.portfolio import legacy_portfolio_to_domain_portfolio
    domain = legacy_portfolio_to_domain_portfolio(_portfolio())
    for h in domain.holdings:
        assert h.quality_score is not None
        assert h.risk_score is not None
        assert h.market_cap is not None


def test_dashboard_cli_show_outputs_text_dashboard(tmp_path):
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
        ["dashboard", "show", "--portfolio", str(portfolio_path), "--ticker", "AAPL"],
    )

    assert result.exit_code == 0
    assert "Atlas Home Dashboard" in result.output
    assert "Portfolio Overview" in result.output
    assert "Market Overview" in result.output
    assert "Themes To Watch" in result.output
    assert "Suggested Questions" in result.output


# ---------------------------------------------------------------------------
# Sprint 127: Remove stale legacy portfolio engine attribute from dashboard
# ---------------------------------------------------------------------------

def _dash_top_level_legacy_imports() -> list[str]:
    """Return atlas.analysis.portfolio runtime imports (not inside TYPE_CHECKING)."""
    results = []
    for node in _DASH_TREE.body:
        if isinstance(node, ast.If):
            test = node.test
            if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                continue
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if "atlas.analysis.portfolio" in module:
                results.append(module)
    return results


def test_sprint127_dashboard_engine_no_runtime_legacy_portfolio_import():
    """dashboard/engine.py must not runtime-import from atlas.analysis.portfolio."""
    assert _dash_top_level_legacy_imports() == []


def test_sprint127_dashboard_engine_no_portfolio_intelligence_engine():
    """PortfolioIntelligenceEngine must not appear in dashboard/engine.py."""
    assert "PortfolioIntelligenceEngine" not in _DASH_SOURCE


def test_sprint127_dashboard_engine_no_self_portfolio_engine():
    """self.portfolio_engine must not appear in dashboard/engine.py."""
    assert "self.portfolio_engine" not in _DASH_SOURCE


def test_sprint127_dashboard_engine_no_portfolio_engine_constructor_param():
    """portfolio_engine constructor parameter must not appear in live code."""
    non_comment_lines = [
        line for line in _DASH_SOURCE.splitlines()
        if not line.strip().startswith("#")
    ]
    assert not any(
        "portfolio_engine:" in line and "portfolio_fit" not in line
        for line in non_comment_lines
    )


def test_sprint127_dashboard_engine_type_checking_guard_for_portfolio():
    """Portfolio must appear inside a TYPE_CHECKING block in dashboard/engine.py."""
    assert "TYPE_CHECKING" in _DASH_SOURCE
    assert "from __future__ import annotations" in _DASH_SOURCE
    for node in _DASH_TREE.body:
        if isinstance(node, ast.If):
            test = node.test
            if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                for child in ast.walk(node):
                    if isinstance(child, ast.ImportFrom):
                        if any(alias.name == "Portfolio" for alias in child.names):
                            return
    raise AssertionError("Portfolio not found inside TYPE_CHECKING block in dashboard/engine.py")


def test_sprint127_dashboard_engine_uses_portfolio_fit_capability():
    """Sprint 137: dashboard/engine.py uses portfolio_fit_capability; calls provider directly."""
    assert "self.portfolio_fit_capability" in _DASH_SOURCE
    assert "portfolio_fit_input_from_profile" not in _DASH_SOURCE
    assert "legacy_portfolio_to_domain_portfolio" in _DASH_SOURCE
    assert "get_portfolio_profile" in _DASH_SOURCE


def test_sprint127_dashboard_capability_injection_works():
    """DashboardEngine accepts a PortfolioIntelligenceCapability via constructor."""
    from atlas.capabilities.portfolio_intelligence import PortfolioIntelligenceCapability

    cap = PortfolioIntelligenceCapability()
    engine = DashboardEngine(portfolio_fit_capability=cap)
    assert engine.portfolio_fit_capability is cap


def test_sprint127_dashboard_portfolio_fit_card_still_works():
    """Portfolio fit card still appears when target_ticker and provider are supplied."""
    summary = DashboardEngine().build(
        DashboardInput(
            portfolio=_portfolio(),
            provider=MockCompanyAnalysisProvider(),
            target_ticker="NVDA",
        )
    )
    portfolio_section = next(s for s in summary.sections if s.title == "Portfolio Overview")
    fit_card = next((c for c in portfolio_section.cards if c.title == "Target Portfolio Fit"), None)
    assert fit_card is not None
    assert "/100" in fit_card.value

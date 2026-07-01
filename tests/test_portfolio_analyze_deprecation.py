"""Sprint 89: Tests confirming atlas portfolio analyze has been retired.

Sprint 79 deprecated the command; Sprint 89 removed the command body.
`atlas portfolio analyze` is no longer a registered CLI command.

The underlying `atlas.analysis.portfolio` engine remains on disk:
- Portfolio, PortfolioAnalysis, PortfolioIntelligenceEngine are still imported by
  atlas/intelligence, atlas/conversation, atlas/decision, atlas/dashboard,
  atlas/reasoning, atlas/home, atlas/suitability, atlas/risk_drift,
  atlas/monitoring, and atlas/portfolio_review — must be preserved.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

from typer.testing import CliRunner

from atlas.cli.deprecations import all_deprecated_commands, all_retired_commands
from atlas.cli.main import app

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI_PATH = REPO_ROOT / "atlas" / "cli" / "main.py"

runner = CliRunner()

PORTFOLIO_ENGINE_CALLERS = (
    REPO_ROOT / "atlas" / "intelligence" / "engine.py",
    REPO_ROOT / "atlas" / "conversation" / "engine.py",
    REPO_ROOT / "atlas" / "decision" / "decision_engine.py",
    REPO_ROOT / "atlas" / "dashboard" / "engine.py",
    REPO_ROOT / "atlas" / "reasoning" / "engine.py",
)


def _fake_portfolio_path(tmp_path: Path) -> Path:
    p = tmp_path / "portfolio.json"
    p.write_text(
        json.dumps({
            "positions": [{
                "ticker": "NVDA",
                "company": "NVIDIA",
                "sector": "Semiconductors",
                "country": "United States",
                "market_cap": 3_000_000_000_000,
                "weight": 0.5,
                "quality_score": 90,
                "risk_score": 70,
            }]
        }),
        encoding="utf-8",
    )
    return p


def test_portfolio_analyze_command_is_no_longer_registered(tmp_path) -> None:
    """atlas portfolio analyze must not be a recognized subcommand of atlas portfolio."""
    result = runner.invoke(app, ["portfolio", "analyze", str(_fake_portfolio_path(tmp_path)), "NVDA"])
    assert result.exit_code != 0


def test_portfolio_analyze_command_is_not_in_active_registry() -> None:
    assert "atlas portfolio analyze" not in all_deprecated_commands()


def test_portfolio_analyze_command_is_in_retired_registry() -> None:
    assert "atlas portfolio analyze" in all_retired_commands()


def test_portfolio_analyze_command_function_removed_from_cli() -> None:
    """The portfolio_analyze_command function must not exist in the CLI source."""
    source = CLI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    func_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    assert "portfolio_analyze_command" not in func_names, (
        "portfolio_analyze_command function should have been removed in Sprint 89"
    )


def test_portfolio_summary_command_is_unaffected(tmp_path) -> None:
    """atlas portfolio summary must remain functional and not deprecated."""
    p = _fake_portfolio_path(tmp_path)
    result = runner.invoke(app, ["portfolio", "summary", str(p)])
    assert result.exit_code == 0
    assert "deprecated" not in result.output.lower()


def test_portfolio_review_command_is_retired(tmp_path) -> None:
    """Sprint 90: atlas portfolio review command body retired — no longer a valid command."""
    result = runner.invoke(app, ["portfolio", "review", str(tmp_path / "p.json")])
    assert result.exit_code != 0


def test_portfolio_analysis_engine_remains_importable() -> None:
    """atlas.analysis.portfolio must still be importable — shared types still in use."""
    from atlas.analysis.portfolio import Portfolio, PortfolioAnalysis, PortfolioIntelligenceEngine
    assert Portfolio is not None
    assert PortfolioAnalysis is not None
    assert PortfolioIntelligenceEngine is not None


def test_portfolio_engine_active_callers_remain() -> None:
    """Confirm known active callers of atlas.analysis.portfolio still exist."""
    for path in PORTFOLIO_ENGINE_CALLERS:
        assert path.exists(), f"Expected active portfolio engine caller at {path}"
        source = path.read_text(encoding="utf-8")
        assert "atlas.analysis.portfolio" in source, (
            f"{path} should still import from atlas.analysis.portfolio"
        )


def test_portfolio_engine_module_remains_on_disk() -> None:
    """atlas.analysis.portfolio engine must still exist — shared types are still in use."""
    import importlib
    mod = importlib.import_module("atlas.analysis.portfolio")
    assert hasattr(mod, "Portfolio"), (
        "atlas.analysis.portfolio.Portfolio must still be importable (shared type used by many engines)"
    )
    assert hasattr(mod, "PortfolioIntelligenceEngine"), (
        "atlas.analysis.portfolio.PortfolioIntelligenceEngine must still be importable"
    )


# ── Confirm remaining deprecated commands still work ─────────────────────────

def test_daily_brief_is_retired() -> None:
    result = runner.invoke(app, ["daily", "brief"])
    assert result.exit_code != 0


def test_evidence_assess_is_retired() -> None:
    result = runner.invoke(app, ["evidence", "assess"])
    assert result.exit_code != 0


def test_reason_analyze_is_retired() -> None:
    result = runner.invoke(app, ["reason", "analyze"])
    assert result.exit_code != 0


def test_risk_size_is_retired(tmp_path) -> None:
    p = tmp_path / "r.json"
    p.write_text(json.dumps({"ticker": "NVDA"}), encoding="utf-8")
    result = runner.invoke(app, ["risk", "size", str(p)])
    assert result.exit_code != 0


def test_watchlist_analyze_is_retired(tmp_path) -> None:
    p = tmp_path / "w.json"
    p.write_text(json.dumps({"name": "Test", "tickers": ["NVDA"]}), encoding="utf-8")
    result = runner.invoke(app, ["watchlist", "analyze", str(p)])
    assert result.exit_code != 0


def test_portfolio_review_is_retired(tmp_path) -> None:
    # Sprint 90: atlas portfolio review command body retired — no longer a valid command
    p = _fake_portfolio_path(tmp_path)
    result = runner.invoke(app, ["portfolio", "review", str(p)])
    assert result.exit_code != 0

"""Sprint 79: Tests for atlas portfolio analyze deprecation.

Confirms that `atlas portfolio analyze` is deprecated, directs users to
`atlas portfolio summary`, and never calls PortfolioIntelligenceEngine or providers.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

from typer.testing import CliRunner

from atlas.cli.main import app

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI_PATH = REPO_ROOT / "atlas" / "cli" / "main.py"

runner = CliRunner()


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


def test_portfolio_analyze_command_exits_cleanly(tmp_path) -> None:
    result = runner.invoke(app, ["portfolio", "analyze", str(_fake_portfolio_path(tmp_path)), "NVDA"])
    assert result.exit_code == 0, f"Expected exit 0, got {result.exit_code}: {result.output}"


def test_portfolio_analyze_command_prints_deprecation_message(tmp_path) -> None:
    result = runner.invoke(app, ["portfolio", "analyze", str(_fake_portfolio_path(tmp_path)), "NVDA"])
    assert "deprecated" in result.output.lower()


def test_portfolio_analyze_deprecation_references_portfolio_summary(tmp_path) -> None:
    result = runner.invoke(app, ["portfolio", "analyze", str(_fake_portfolio_path(tmp_path)), "NVDA"])
    assert "portfolio summary" in result.output.lower()


def test_portfolio_analyze_does_not_call_providers(tmp_path) -> None:
    result = runner.invoke(app, ["portfolio", "analyze", str(_fake_portfolio_path(tmp_path)), "NVDA"])
    assert result.exit_code == 0
    assert "yahoo" not in result.output.lower()


def test_portfolio_analyze_help_text_marks_deprecated() -> None:
    result = runner.invoke(app, ["portfolio", "analyze", "--help"])
    assert "deprecated" in result.output.lower()


def test_portfolio_analyze_help_references_portfolio_summary() -> None:
    result = runner.invoke(app, ["portfolio", "analyze", "--help"])
    assert "portfolio summary" in result.output.lower()


def test_portfolio_summary_command_is_unaffected(tmp_path) -> None:
    """atlas portfolio summary must remain functional and not deprecated."""
    p = _fake_portfolio_path(tmp_path)
    result = runner.invoke(app, ["portfolio", "summary", str(p)])
    assert result.exit_code == 0
    assert "deprecated" not in result.output.lower()


def test_portfolio_review_command_is_unaffected(tmp_path) -> None:
    """atlas portfolio review must remain unchanged by Sprint 79."""
    result = runner.invoke(app, ["portfolio", "review", "--help"])
    assert result.exit_code == 0
    assert "deprecated" not in result.output.lower()


def test_cli_does_not_import_portfolio_intelligence_engine_at_module_level() -> None:
    """CLI must not import PortfolioIntelligenceEngine or render_portfolio_analysis."""
    source = CLI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("atlas.analysis.portfolio"):
                imported_names = [alias.name for alias in node.names]
                assert "PortfolioIntelligenceEngine" not in imported_names, (
                    f"CLI imports PortfolioIntelligenceEngine at line {node.lineno}"
                )
                assert "render_portfolio_analysis" not in imported_names, (
                    f"CLI imports render_portfolio_analysis at line {node.lineno}"
                )


def test_no_portfolio_intelligence_engine_call_in_analyze_command_body() -> None:
    """The portfolio_analyze_command function must not call PortfolioIntelligenceEngine."""
    source = CLI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "portfolio_analyze_command":
            func_source = ast.get_source_segment(source, node) or ""
            assert "PortfolioIntelligenceEngine" not in func_source, (
                "portfolio_analyze_command must not call PortfolioIntelligenceEngine (deprecated)"
            )

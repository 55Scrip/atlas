"""Sprint 80: Tests for atlas portfolio review deprecation.

Confirms that `atlas portfolio review` is deprecated, directs users to
`atlas portfolio summary`, and never calls PortfolioReviewEngine or providers.
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


def test_portfolio_review_command_exits_cleanly(tmp_path) -> None:
    result = runner.invoke(app, ["portfolio", "review", str(_fake_portfolio_path(tmp_path))])
    assert result.exit_code == 0, f"Expected exit 0, got {result.exit_code}: {result.output}"


def test_portfolio_review_command_prints_deprecation_message(tmp_path) -> None:
    result = runner.invoke(app, ["portfolio", "review", str(_fake_portfolio_path(tmp_path))])
    assert "deprecated" in result.output.lower()


def test_portfolio_review_deprecation_references_portfolio_summary(tmp_path) -> None:
    result = runner.invoke(app, ["portfolio", "review", str(_fake_portfolio_path(tmp_path))])
    assert "portfolio summary" in result.output.lower()


def test_portfolio_review_does_not_call_providers(tmp_path) -> None:
    result = runner.invoke(app, ["portfolio", "review", str(_fake_portfolio_path(tmp_path))])
    assert result.exit_code == 0
    assert "yahoo" not in result.output.lower()


def test_portfolio_review_help_text_marks_deprecated() -> None:
    result = runner.invoke(app, ["portfolio", "review", "--help"])
    assert "deprecated" in result.output.lower()


def test_portfolio_review_help_references_portfolio_summary() -> None:
    result = runner.invoke(app, ["portfolio", "review", "--help"])
    assert "portfolio summary" in result.output.lower()


def test_portfolio_summary_command_is_unaffected(tmp_path) -> None:
    """atlas portfolio summary must remain functional and not deprecated."""
    result = runner.invoke(app, ["portfolio", "summary", str(_fake_portfolio_path(tmp_path))])
    assert result.exit_code == 0
    assert "deprecated" not in result.output.lower()


def test_portfolio_analyze_is_retired(tmp_path) -> None:
    """Sprint 89: atlas portfolio analyze command body retired — no longer a valid command."""
    result = runner.invoke(app, ["portfolio", "analyze", str(_fake_portfolio_path(tmp_path)), "NVDA"])
    assert result.exit_code != 0


def test_cli_does_not_import_portfolio_review_engine_at_module_level() -> None:
    """CLI must not import PortfolioReviewEngine, PortfolioReviewInput, or render_portfolio_review."""
    source = CLI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden = {"PortfolioReviewEngine", "PortfolioReviewInput", "render_portfolio_review"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("atlas.portfolio_review"):
                imported_names = {alias.name for alias in node.names}
                violations = forbidden & imported_names
                assert not violations, (
                    f"CLI imports {violations} from atlas.portfolio_review at line {node.lineno}"
                )


def test_no_portfolio_review_engine_call_in_review_command_body() -> None:
    """The portfolio_review_command function must not call PortfolioReviewEngine."""
    source = CLI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "portfolio_review_command":
            func_source = ast.get_source_segment(source, node) or ""
            assert "PortfolioReviewEngine" not in func_source, (
                "portfolio_review_command must not call PortfolioReviewEngine (deprecated)"
            )

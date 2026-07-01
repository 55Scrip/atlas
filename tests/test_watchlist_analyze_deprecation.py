"""Sprint 78: Tests for atlas watchlist analyze deprecation.

Confirms that `atlas watchlist analyze` is deprecated, directs users to
`atlas watchlist intelligence`, and never calls WatchlistEngine or providers.
"""

from __future__ import annotations

import ast
from pathlib import Path

from typer.testing import CliRunner

from atlas.cli.main import app

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI_PATH = REPO_ROOT / "atlas" / "cli" / "main.py"

runner = CliRunner()


def _fake_watchlist_path(tmp_path: Path) -> Path:
    p = tmp_path / "watchlist.json"
    p.write_text('{"name": "Test", "tickers": ["NVDA"]}', encoding="utf-8")
    return p


def test_watchlist_analyze_command_exits_cleanly(tmp_path) -> None:
    result = runner.invoke(app, ["watchlist", "analyze", str(_fake_watchlist_path(tmp_path))])
    assert result.exit_code == 0, f"Expected exit 0, got {result.exit_code}: {result.output}"


def test_watchlist_analyze_command_prints_deprecation_message(tmp_path) -> None:
    result = runner.invoke(app, ["watchlist", "analyze", str(_fake_watchlist_path(tmp_path))])
    assert "deprecated" in result.output.lower()


def test_watchlist_analyze_deprecation_references_watchlist_intelligence(tmp_path) -> None:
    result = runner.invoke(app, ["watchlist", "analyze", str(_fake_watchlist_path(tmp_path))])
    assert "watchlist intelligence" in result.output.lower()


def test_watchlist_analyze_does_not_call_providers(tmp_path) -> None:
    result = runner.invoke(app, ["watchlist", "analyze", str(_fake_watchlist_path(tmp_path))])
    assert result.exit_code == 0
    assert "yahoo" not in result.output.lower()


def test_watchlist_analyze_help_text_marks_deprecated() -> None:
    result = runner.invoke(app, ["watchlist", "analyze", "--help"])
    assert "deprecated" in result.output.lower()


def test_watchlist_analyze_help_references_watchlist_intelligence() -> None:
    result = runner.invoke(app, ["watchlist", "analyze", "--help"])
    assert "watchlist intelligence" in result.output.lower()


def test_watchlist_intelligence_command_is_unaffected() -> None:
    """atlas watchlist intelligence help must remain functional and not deprecated."""
    result = runner.invoke(app, ["watchlist", "intelligence", "--help"])
    assert result.exit_code == 0
    output_lower = result.output.lower()
    # The intelligence command itself is not deprecated
    assert "deprecated" not in output_lower


def test_cli_does_not_import_watchlist_engine_at_module_level() -> None:
    """CLI must not import WatchlistEngine or render_watchlist_analysis at module level."""
    source = CLI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("atlas.analysis.watchlist"):
                imported_names = [alias.name for alias in node.names]
                assert "WatchlistEngine" not in imported_names, (
                    f"CLI imports WatchlistEngine from atlas.analysis.watchlist at line {node.lineno}"
                )
                assert "render_watchlist_analysis" not in imported_names, (
                    f"CLI imports render_watchlist_analysis from atlas.analysis.watchlist at line {node.lineno}"
                )


def test_no_watchlist_engine_call_in_analyze_command_body() -> None:
    """The watchlist_analyze_command function must not instantiate WatchlistEngine."""
    source = CLI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "watchlist_analyze_command":
            func_source = ast.get_source_segment(source, node) or ""
            assert "WatchlistEngine" not in func_source, (
                "watchlist_analyze_command must not instantiate WatchlistEngine (deprecated)"
            )


def test_demo_script_does_not_use_watchlist_analyze_command() -> None:
    demo_script = REPO_ROOT / "scripts" / "run_daily_brief_demo.sh"
    text = demo_script.read_text()
    assert "watchlist analyze" not in text, (
        "Demo script should not use deprecated 'atlas watchlist analyze'"
    )

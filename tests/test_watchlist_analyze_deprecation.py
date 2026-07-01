"""Sprint 91: Tests confirming atlas watchlist analyze has been retired.

Sprint 78 deprecated the command; Sprint 91 removed the command body.
`atlas watchlist analyze` is no longer a registered CLI command.

The underlying `atlas.analysis.watchlist` engine remains on disk:
- WatchlistEngine is still imported and instantiated by:
  - atlas/intelligence/engine.py
  - atlas/decision/decision_engine.py
  - atlas/monitoring/engine.py
  - atlas/watchlist_review/engine.py
  - atlas/conversation/engine.py
Engine deletion deferred until all five callers are retired.

Sprint 91 completes the CLI deprecated command retirement plan.
Active _REGISTRY is now empty — all deprecated commands have been retired.
"""

from __future__ import annotations

import ast
from pathlib import Path

from typer.testing import CliRunner

from atlas.cli.deprecations import all_deprecated_commands, all_retired_commands
from atlas.cli.main import app

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI_PATH = REPO_ROOT / "atlas" / "cli" / "main.py"

runner = CliRunner()

WATCHLIST_ENGINE_CALLERS = (
    REPO_ROOT / "atlas" / "intelligence" / "engine.py",
    REPO_ROOT / "atlas" / "decision" / "decision_engine.py",
    REPO_ROOT / "atlas" / "monitoring" / "engine.py",
    REPO_ROOT / "atlas" / "watchlist_review" / "engine.py",
    REPO_ROOT / "atlas" / "conversation" / "engine.py",
)


def _fake_watchlist_path(tmp_path: Path) -> Path:
    p = tmp_path / "watchlist.json"
    p.write_text('{"name": "Test", "tickers": ["NVDA"]}', encoding="utf-8")
    return p


def test_watchlist_analyze_command_is_no_longer_registered(tmp_path) -> None:
    """atlas watchlist analyze must not be a recognized subcommand of atlas watchlist."""
    result = runner.invoke(app, ["watchlist", "analyze", str(_fake_watchlist_path(tmp_path))])
    assert result.exit_code != 0


def test_watchlist_analyze_command_is_not_in_active_registry() -> None:
    assert "atlas watchlist analyze" not in all_deprecated_commands()


def test_watchlist_analyze_command_is_in_retired_registry() -> None:
    assert "atlas watchlist analyze" in all_retired_commands()


def test_active_deprecated_registry_is_now_empty() -> None:
    """Sprint 91: all deprecated commands retired — active registry must be empty."""
    assert all_deprecated_commands() == ()


def test_watchlist_analyze_command_function_removed_from_cli() -> None:
    """The watchlist_analyze_command function must not exist in the CLI source."""
    source = CLI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    func_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    assert "watchlist_analyze_command" not in func_names, (
        "watchlist_analyze_command function should have been removed in Sprint 91"
    )


def test_watchlist_intelligence_command_is_unaffected() -> None:
    """atlas watchlist intelligence must remain functional and not deprecated."""
    result = runner.invoke(app, ["watchlist", "intelligence", "--help"])
    assert result.exit_code == 0
    assert "deprecated" not in result.output.lower()


def test_watchlist_engine_remains_importable() -> None:
    """atlas.analysis.watchlist must still be importable — five engines depend on it."""
    from atlas.analysis.watchlist import Watchlist, WatchlistEngine
    assert WatchlistEngine is not None
    assert Watchlist is not None


def test_watchlist_engine_active_callers_remain() -> None:
    """Confirm all five known active callers of WatchlistEngine still exist."""
    for path in WATCHLIST_ENGINE_CALLERS:
        assert path.exists(), f"Expected active WatchlistEngine caller at {path}"
        source = path.read_text(encoding="utf-8")
        assert "WatchlistEngine" in source, (
            f"{path} should still import WatchlistEngine"
        )


def test_watchlist_engine_module_remains_on_disk() -> None:
    """atlas.analysis.watchlist engine must still exist — five engines depend on it."""
    import importlib
    mod = importlib.import_module("atlas.analysis.watchlist")
    assert hasattr(mod, "WatchlistEngine"), (
        "atlas.analysis.watchlist.WatchlistEngine must still be importable"
    )


def test_demo_script_does_not_use_watchlist_analyze_command() -> None:
    demo_script = REPO_ROOT / "scripts" / "run_daily_brief_demo.sh"
    text = demo_script.read_text()
    assert "watchlist analyze" not in text, (
        "Demo script should not use retired 'atlas watchlist analyze'"
    )


# ── All retired commands remain retired ───────────────────────────────────────

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
    p.write_text('{"ticker": "NVDA"}', encoding="utf-8")
    result = runner.invoke(app, ["risk", "size", str(p)])
    assert result.exit_code != 0


def test_portfolio_analyze_is_retired(tmp_path) -> None:
    p = tmp_path / "portfolio.json"
    p.write_text('{"positions": []}', encoding="utf-8")
    result = runner.invoke(app, ["portfolio", "analyze", str(p), "NVDA"])
    assert result.exit_code != 0


def test_portfolio_review_is_retired(tmp_path) -> None:
    p = tmp_path / "portfolio.json"
    p.write_text('{"positions": []}', encoding="utf-8")
    result = runner.invoke(app, ["portfolio", "review", str(p)])
    assert result.exit_code != 0

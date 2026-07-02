"""Sprint 91: Tests confirming atlas watchlist analyze has been retired.

Sprint 78 deprecated the command; Sprint 91 removed the command body.
`atlas watchlist analyze` is no longer a registered CLI command.

Sprint 99: WatchlistEngine deleted — atlas/analysis/watchlist.py slimmed to types only.
- WatchlistEngine active caller count reached 0 in Sprint 98.
- WatchlistEngine class deleted in Sprint 99; atlas/analysis/watchlist.py retained for
  Watchlist / WatchlistItem type-only imports used by 7 production modules.

Sprint 91 completes the CLI deprecated command retirement plan.
Active _REGISTRY is now empty — all deprecated commands have been retired.

Sprint 92: WatchlistEngine caller set frozen; exclusivity guardrail added.
Sprint 93: atlas/monitoring/engine.py WatchlistEngine removed — caller count reduced 5 → 4.
Sprint 94: atlas/watchlist_review/engine.py WatchlistEngine removed — caller count reduced 4 → 3.
Sprint 95: atlas/decision/decision_engine.py WatchlistEngine removed — caller count reduced 3 → 2.
Sprint 96: Audit sprint — caller count unchanged at 2 (intelligence, conversation).
Sprint 97: atlas/intelligence/engine.py WatchlistEngine removed — caller count reduced 2 → 1.
Sprint 98: atlas/conversation/engine.py WatchlistEngine removed — caller count reduced 1 → 0.
Sprint 99: WatchlistEngine deleted — all callers retired.
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

WATCHLIST_ENGINE_CALLERS: tuple = ()


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


def test_watchlist_engine_is_not_importable() -> None:
    """Sprint 99: WatchlistEngine must no longer exist in atlas.analysis.watchlist."""
    import importlib
    mod = importlib.import_module("atlas.analysis.watchlist")
    assert not hasattr(mod, "WatchlistEngine"), (
        "WatchlistEngine was deleted in Sprint 99 and must not be importable"
    )


def test_watchlist_analysis_is_not_importable() -> None:
    """Sprint 100: WatchlistAnalysis must no longer exist in atlas.analysis.watchlist."""
    import importlib
    mod = importlib.import_module("atlas.analysis.watchlist")
    assert not hasattr(mod, "WatchlistAnalysis"), (
        "WatchlistAnalysis was deleted in Sprint 99 and must not be importable"
    )


def test_watchlist_recommendation_is_not_importable() -> None:
    """Sprint 100: WatchlistRecommendation must no longer exist in atlas.analysis.watchlist."""
    import importlib
    mod = importlib.import_module("atlas.analysis.watchlist")
    assert not hasattr(mod, "WatchlistRecommendation"), (
        "WatchlistRecommendation was deleted in Sprint 99 and must not be importable"
    )


def test_render_watchlist_analysis_is_not_importable() -> None:
    """Sprint 100: render_watchlist_analysis must no longer exist in atlas.analysis.watchlist."""
    import importlib
    mod = importlib.import_module("atlas.analysis.watchlist")
    assert not hasattr(mod, "render_watchlist_analysis"), (
        "render_watchlist_analysis was deleted in Sprint 99 and must not be importable"
    )


def test_watchlist_module_contains_only_type_models() -> None:
    """Sprint 100: atlas/analysis/watchlist.py must contain only Watchlist and WatchlistItem."""
    watchlist_path = REPO_ROOT / "atlas" / "analysis" / "watchlist.py"
    source = watchlist_path.read_text(encoding="utf-8")
    forbidden = ["WatchlistEngine", "WatchlistAnalysis", "WatchlistSignal",
                 "WatchlistRecommendation", "render_watchlist_analysis"]
    found = [name for name in forbidden if name in source]
    assert not found, (
        f"Deleted legacy symbols found in watchlist.py: {found}"
    )


def test_watchlist_module_exports_watchlist_and_item() -> None:
    """Sprint 100: atlas/analysis/watchlist.py must still export Watchlist and WatchlistItem."""
    import importlib
    mod = importlib.import_module("atlas.analysis.watchlist")
    assert hasattr(mod, "Watchlist"), "Watchlist must remain in atlas.analysis.watchlist"
    assert hasattr(mod, "WatchlistItem"), "WatchlistItem must remain in atlas.analysis.watchlist"


def test_watchlist_engine_active_callers_are_zero() -> None:
    """Sprint 98: all active WatchlistEngine callers have been retired — set is empty."""
    assert WATCHLIST_ENGINE_CALLERS == (), (
        "Expected zero active WatchlistEngine callers after Sprint 98"
    )


def test_monitoring_engine_does_not_import_watchlist_engine() -> None:
    """Sprint 93: atlas/monitoring/engine.py must not import WatchlistEngine."""
    monitoring_path = REPO_ROOT / "atlas" / "monitoring" / "engine.py"
    source = monitoring_path.read_text(encoding="utf-8")
    assert "WatchlistEngine" not in source, (
        "atlas/monitoring/engine.py should no longer import WatchlistEngine after Sprint 93"
    )


def test_watchlist_review_engine_does_not_import_watchlist_engine() -> None:
    """Sprint 94: atlas/watchlist_review/engine.py must not import WatchlistEngine."""
    path = REPO_ROOT / "atlas" / "watchlist_review" / "engine.py"
    source = path.read_text(encoding="utf-8")
    assert "WatchlistEngine" not in source, (
        "atlas/watchlist_review/engine.py should no longer import WatchlistEngine after Sprint 94"
    )


def test_intelligence_engine_does_not_import_watchlist_engine() -> None:
    """Sprint 97: atlas/intelligence/engine.py must not import WatchlistEngine."""
    path = REPO_ROOT / "atlas" / "intelligence" / "engine.py"
    source = path.read_text(encoding="utf-8")
    assert "WatchlistEngine" not in source, (
        "atlas/intelligence/engine.py should no longer import WatchlistEngine after Sprint 97"
    )


def test_conversation_engine_does_not_import_watchlist_engine() -> None:
    """Sprint 98: atlas/conversation/engine.py must not import WatchlistEngine."""
    path = REPO_ROOT / "atlas" / "conversation" / "engine.py"
    source = path.read_text(encoding="utf-8")
    assert "WatchlistEngine" not in source, (
        "atlas/conversation/engine.py should no longer import WatchlistEngine after Sprint 98"
    )


def test_decision_engine_does_not_import_watchlist_engine() -> None:
    """Sprint 95: atlas/decision/decision_engine.py must not import WatchlistEngine."""
    path = REPO_ROOT / "atlas" / "decision" / "decision_engine.py"
    source = path.read_text(encoding="utf-8")
    assert "WatchlistEngine" not in source, (
        "atlas/decision/decision_engine.py should no longer import WatchlistEngine after Sprint 95"
    )


def test_watchlist_engine_callers_are_exactly_the_known_set() -> None:
    """Sprint 98 guardrail: no new WatchlistEngine callers may be added.

    The known set is now empty — all callers retired across Sprints 93–98.
    Any new direct import must be explicitly reviewed and added to WATCHLIST_ENGINE_CALLERS above.
    """
    known_paths = {path.resolve() for path in WATCHLIST_ENGINE_CALLERS}
    # Scan only atlas/ source, excluding cli/ (deprecations registry contains string references)
    search_dirs = [
        d for d in (REPO_ROOT / "atlas").iterdir()
        if d.is_dir() and d.name not in {"cli", "__pycache__"}
    ]
    unknown_callers = []
    for directory in search_dirs:
        for path in directory.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            if path.resolve() in known_paths:
                continue
            text = path.read_text(encoding="utf-8")
            # Match actual import statements, not string mentions
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if "WatchlistEngine" in stripped and (
                    stripped.startswith("from ") or stripped.startswith("import ")
                    or "WatchlistEngine(" in stripped
                ):
                    unknown_callers.append(str(path.relative_to(REPO_ROOT)))
                    break
    assert not unknown_callers, (
        "New WatchlistEngine callers found outside the frozen set — "
        "update WATCHLIST_ENGINE_CALLERS or remove the new import:\n"
        + "\n".join(unknown_callers)
    )


def test_watchlist_engine_is_deleted() -> None:
    """Sprint 99: WatchlistEngine class must be gone from atlas/analysis/watchlist.py."""
    watchlist_path = REPO_ROOT / "atlas" / "analysis" / "watchlist.py"
    source = watchlist_path.read_text(encoding="utf-8")
    assert "WatchlistEngine" not in source, (
        "WatchlistEngine was deleted in Sprint 99 and must not appear in watchlist.py"
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

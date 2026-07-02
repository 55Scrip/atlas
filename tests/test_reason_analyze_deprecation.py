"""Sprint 87: Tests confirming atlas reason analyze has been retired.

Sprint 82 deprecated the command; Sprint 87 removed the command body.
Sprint 152 removed check_reasoning_report() from atlas/principles/engine.py.
Sprint 153 deleted the atlas/reasoning/ package.
`atlas reason analyze` is no longer a registered CLI command. No legacy module remains.
"""

from __future__ import annotations

import ast
from pathlib import Path

from typer.testing import CliRunner

from atlas.cli.deprecations import all_deprecated_commands, all_retired_commands
from atlas.cli.main import app

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI_PATH = REPO_ROOT / "atlas" / "cli" / "main.py"
PRINCIPLES_ENGINE_PATH = REPO_ROOT / "atlas" / "principles" / "engine.py"

runner = CliRunner()


def test_reason_analyze_command_is_no_longer_registered() -> None:
    """atlas reason analyze must not be a recognized subcommand of atlas reason."""
    result = runner.invoke(app, ["reason", "analyze"])
    assert result.exit_code != 0


def test_reason_analyze_command_is_not_in_active_registry() -> None:
    assert "atlas reason analyze" not in all_deprecated_commands()


def test_reason_analyze_command_is_in_retired_registry() -> None:
    assert "atlas reason analyze" in all_retired_commands()


def test_reason_analyze_command_function_removed_from_cli() -> None:
    """The reason_analyze_command function must not exist in the CLI source."""
    source = CLI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    func_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    assert "reason_analyze_command" not in func_names, (
        "reason_analyze_command function should have been removed in Sprint 87"
    )


def test_cli_does_not_import_reasoning_engine_at_module_level() -> None:
    """CLI must not import ReasoningEngine or related names from atlas.reasoning."""
    source = CLI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden = {"ReasoningEngine", "ReasoningInput", "ReasoningReport", "render_reasoning_report"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("atlas.reasoning"):
                imported_names = {alias.name for alias in node.names}
                violations = forbidden & imported_names
                assert not violations, (
                    f"CLI imports {violations} from atlas.reasoning at line {node.lineno}"
                )


def test_reasoning_package_deleted() -> None:
    """Sprint 153: atlas.reasoning must not be importable — package deleted."""
    import importlib
    try:
        importlib.import_module("atlas.reasoning")
        assert False, "atlas.reasoning must not be importable after Sprint 153 deletion"
    except ModuleNotFoundError:
        pass


def test_principles_engine_no_longer_references_atlas_reasoning() -> None:
    """Sprint 152: atlas/principles/engine.py must not reference atlas.reasoning.

    check_reasoning_report() and its lazy import were removed in Sprint 152.
    No production-code dependency on atlas.reasoning remains.
    """
    source = PRINCIPLES_ENGINE_PATH.read_text(encoding="utf-8")
    assert "atlas.reasoning" not in source, (
        "atlas/principles/engine.py must not reference atlas.reasoning after Sprint 152 — "
        "check_reasoning_report() and its lazy import were removed"
    )


def test_principles_engine_does_not_export_check_reasoning_report() -> None:
    """Sprint 152: check_reasoning_report must not be importable from atlas.principles."""
    import atlas.principles as pkg
    assert not hasattr(pkg, "check_reasoning_report"), (
        "check_reasoning_report must not be exported from atlas.principles after Sprint 152"
    )
    assert "check_reasoning_report" not in pkg.__all__, (
        "check_reasoning_report must not be in atlas.principles.__all__ after Sprint 152"
    )


def test_reasoning_engine_not_instantiated_by_cli() -> None:
    """Confirm CLI source does not instantiate ReasoningEngine."""
    source = CLI_PATH.read_text(encoding="utf-8")
    assert "ReasoningEngine()" not in source


# ── Remaining deprecated commands still work ─────────────────────────────────

def test_daily_brief_is_retired() -> None:
    result = runner.invoke(app, ["daily", "brief"])
    assert result.exit_code != 0


def test_evidence_assess_is_retired() -> None:
    result = runner.invoke(app, ["evidence", "assess"])
    assert result.exit_code != 0


def test_watchlist_analyze_is_retired(tmp_path) -> None:
    import json
    p = tmp_path / "w.json"
    p.write_text(json.dumps({"name": "Test", "tickers": ["NVDA"]}), encoding="utf-8")
    result = runner.invoke(app, ["watchlist", "analyze", str(p)])
    assert result.exit_code != 0


def test_portfolio_analyze_is_retired(tmp_path) -> None:
    import json
    p = tmp_path / "portfolio.json"
    p.write_text(json.dumps({"positions": [{"ticker": "NVDA", "company": "NVIDIA",
        "sector": "Semiconductors", "country": "US", "market_cap": 1000000,
        "weight": 1.0, "quality_score": 90, "risk_score": 50}]}), encoding="utf-8")
    result = runner.invoke(app, ["portfolio", "analyze", str(p), "NVDA"])
    assert result.exit_code != 0


def test_portfolio_review_is_retired(tmp_path) -> None:
    import json
    p = tmp_path / "portfolio.json"
    p.write_text(json.dumps({"positions": [{"ticker": "NVDA", "company": "NVIDIA",
        "sector": "Semiconductors", "country": "US", "market_cap": 1000000,
        "weight": 1.0, "quality_score": 90, "risk_score": 50}]}), encoding="utf-8")
    result = runner.invoke(app, ["portfolio", "review", str(p)])
    assert result.exit_code != 0

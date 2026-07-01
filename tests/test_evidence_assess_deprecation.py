"""Sprint 86: Tests confirming atlas evidence assess has been retired.

Sprint 81 deprecated the command; Sprint 86 removed the command body.
`atlas evidence assess` is no longer a registered CLI command.

The underlying `atlas.evidence` engine (EvidenceQualityEngine) remains on disk —
it is still used by atlas/comparison, atlas/decision_journal, and
atlas/watchlist_review. Engine deletion is deferred.
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


def test_evidence_assess_command_is_no_longer_registered() -> None:
    """atlas evidence assess must not be a recognized subcommand of atlas evidence."""
    result = runner.invoke(app, ["evidence", "assess"])
    assert result.exit_code != 0


def test_evidence_assess_command_is_not_in_active_registry() -> None:
    assert "atlas evidence assess" not in all_deprecated_commands()


def test_evidence_assess_command_is_in_retired_registry() -> None:
    assert "atlas evidence assess" in all_retired_commands()


def test_evidence_assess_command_function_removed_from_cli() -> None:
    """The evidence_assess_command function must not exist in the CLI source."""
    source = CLI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    func_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    assert "evidence_assess_command" not in func_names, (
        "evidence_assess_command function should have been removed in Sprint 86"
    )


def test_cli_does_not_import_evidence_quality_engine_at_module_level() -> None:
    """CLI must not import EvidenceQualityEngine or render_evidence_assessment."""
    source = CLI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden = {"EvidenceQualityEngine", "render_evidence_assessment"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("atlas.evidence"):
                imported_names = {alias.name for alias in node.names}
                violations = forbidden & imported_names
                assert not violations, (
                    f"CLI imports {violations} from atlas.evidence at line {node.lineno}"
                )


def test_evidence_engine_module_remains_on_disk() -> None:
    """atlas.evidence engine must still exist — it has active callers in other engines."""
    import importlib
    mod = importlib.import_module("atlas.evidence")
    assert hasattr(mod, "EvidenceQualityEngine"), (
        "atlas.evidence.EvidenceQualityEngine must still be importable "
        "(used by comparison, decision_journal, watchlist_review engines)"
    )


def test_evidence_engine_active_callers_remain() -> None:
    """Confirm the three known active callers of EvidenceQualityEngine still exist."""
    caller_paths = (
        REPO_ROOT / "atlas" / "comparison" / "engine.py",
        REPO_ROOT / "atlas" / "decision_journal" / "engine.py",
        REPO_ROOT / "atlas" / "watchlist_review" / "engine.py",
    )
    for path in caller_paths:
        assert path.exists(), f"Expected active EvidenceQualityEngine caller at {path}"
        source = path.read_text(encoding="utf-8")
        assert "EvidenceQualityEngine" in source, (
            f"{path} should still reference EvidenceQualityEngine"
        )


# ── Confirm remaining deprecated commands still work ─────────────────────────

def test_daily_brief_is_retired() -> None:
    result = runner.invoke(app, ["daily", "brief"])
    assert result.exit_code != 0


def test_watchlist_analyze_remains_deprecated(tmp_path) -> None:
    import json
    p = tmp_path / "w.json"
    p.write_text(json.dumps({"name": "Test", "tickers": ["NVDA"]}), encoding="utf-8")
    result = runner.invoke(app, ["watchlist", "analyze", str(p)])
    assert result.exit_code == 0
    assert "deprecated" in result.output.lower()


def test_portfolio_analyze_is_retired(tmp_path) -> None:
    import json
    p = tmp_path / "portfolio.json"
    p.write_text(json.dumps({"positions": [{"ticker": "NVDA", "company": "NVIDIA",
        "sector": "Semiconductors", "country": "US", "market_cap": 1000000,
        "weight": 1.0, "quality_score": 90, "risk_score": 50}]}), encoding="utf-8")
    result = runner.invoke(app, ["portfolio", "analyze", str(p), "NVDA"])
    assert result.exit_code != 0


def test_portfolio_review_remains_deprecated(tmp_path) -> None:
    import json
    p = tmp_path / "portfolio.json"
    p.write_text(json.dumps({"positions": [{"ticker": "NVDA", "company": "NVIDIA",
        "sector": "Semiconductors", "country": "US", "market_cap": 1000000,
        "weight": 1.0, "quality_score": 90, "risk_score": 50}]}), encoding="utf-8")
    result = runner.invoke(app, ["portfolio", "review", str(p)])
    assert result.exit_code == 0
    assert "deprecated" in result.output.lower()

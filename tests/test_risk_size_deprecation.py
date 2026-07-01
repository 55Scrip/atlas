"""Sprint 88: Tests confirming atlas risk size has been retired.

Sprint 83 deprecated the command; Sprint 88 removed the command body.
`atlas risk size` is no longer a registered CLI command.

The underlying `atlas.risk` engine remains on disk:
- RiskAnalysis (data type) is still imported by atlas/conversation, atlas/intelligence,
  atlas/reasoning — must be preserved.
- RiskEngine has no production instantiation points, but lives in the same file as
  RiskAnalysis, so engine deletion is deferred to avoid surgery risk.
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

RISK_ANALYSIS_CALLERS = (
    REPO_ROOT / "atlas" / "conversation" / "engine.py",
    REPO_ROOT / "atlas" / "intelligence" / "engine.py",
    REPO_ROOT / "atlas" / "reasoning" / "engine.py",
)


def test_risk_size_command_is_no_longer_registered(tmp_path) -> None:
    """atlas risk size must not be a recognized subcommand of atlas risk."""
    p = tmp_path / "r.json"
    p.write_text('{"ticker": "NVDA"}', encoding="utf-8")
    result = runner.invoke(app, ["risk", "size", str(p)])
    assert result.exit_code != 0


def test_risk_size_command_is_not_in_active_registry() -> None:
    assert "atlas risk size" not in all_deprecated_commands()


def test_risk_size_command_is_in_retired_registry() -> None:
    assert "atlas risk size" in all_retired_commands()


def test_risk_size_command_function_removed_from_cli() -> None:
    """The risk_size_command function must not exist in the CLI source."""
    source = CLI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    func_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    assert "risk_size_command" not in func_names, (
        "risk_size_command function should have been removed in Sprint 88"
    )


def test_cli_does_not_import_risk_engine_at_module_level() -> None:
    """CLI must not import RiskEngine, PositionSizingInput, or render_risk_analysis."""
    source = CLI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden = {"RiskEngine", "PositionSizingInput", "render_risk_analysis"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("atlas.risk") and not node.module.startswith("atlas.risk_drift"):
                imported_names = {alias.name for alias in node.names}
                violations = forbidden & imported_names
                assert not violations, (
                    f"CLI imports {violations} from atlas.risk at line {node.lineno}"
                )


def test_risk_analysis_type_remains_importable() -> None:
    """RiskAnalysis must still be importable — it is a shared type used by other engines."""
    from atlas.risk import RiskAnalysis
    assert RiskAnalysis is not None


def test_risk_analysis_shared_type_callers_remain() -> None:
    """Confirm the three known active callers of RiskAnalysis still exist."""
    for path in RISK_ANALYSIS_CALLERS:
        assert path.exists(), f"Expected active RiskAnalysis caller at {path}"
        source = path.read_text(encoding="utf-8")
        assert "RiskAnalysis" in source, (
            f"{path} should still import RiskAnalysis"
        )


def test_risk_engine_module_remains_on_disk() -> None:
    """atlas.risk engine must still exist — RiskAnalysis type is still in use."""
    import importlib
    mod = importlib.import_module("atlas.risk")
    assert hasattr(mod, "RiskAnalysis"), (
        "atlas.risk.RiskAnalysis must still be importable (shared type used by 3 engines)"
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

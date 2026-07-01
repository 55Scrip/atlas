"""Sprint 83: Tests for atlas risk size deprecation.

Confirms that `atlas risk size` is deprecated, does not call RiskEngine or
providers, and that existing deprecated commands remain deprecated.
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


def _fake_risk_input_path(tmp_path: Path) -> Path:
    p = tmp_path / "risk_input.json"
    p.write_text(
        json.dumps({
            "ticker": "NVDA",
            "position_size": 10000,
            "portfolio_value": 100000,
        }),
        encoding="utf-8",
    )
    return p


def test_risk_size_command_exits_cleanly(tmp_path) -> None:
    result = runner.invoke(app, ["risk", "size", str(_fake_risk_input_path(tmp_path))])
    assert result.exit_code == 0, f"Expected exit 0, got {result.exit_code}: {result.output}"


def test_risk_size_command_prints_deprecation_message(tmp_path) -> None:
    result = runner.invoke(app, ["risk", "size", str(_fake_risk_input_path(tmp_path))])
    assert "deprecated" in result.output.lower()


def test_risk_size_deprecation_does_not_invent_replacement_command(tmp_path) -> None:
    """Deprecation message must not reference a non-existent replacement command."""
    result = runner.invoke(app, ["risk", "size", str(_fake_risk_input_path(tmp_path))])
    output_lower = result.output.lower()
    assert "atlas risk analyze" not in output_lower
    assert "atlas risk assess" not in output_lower


def test_risk_size_deprecation_mentions_consolidation(tmp_path) -> None:
    result = runner.invoke(app, ["risk", "size", str(_fake_risk_input_path(tmp_path))])
    output_lower = result.output.lower()
    assert "consolidat" in output_lower or "blueprint" in output_lower or "portfolio" in output_lower


def test_risk_size_does_not_call_providers(tmp_path) -> None:
    result = runner.invoke(app, ["risk", "size", str(_fake_risk_input_path(tmp_path))])
    assert result.exit_code == 0
    assert "yahoo" not in result.output.lower()


def test_risk_size_help_text_marks_deprecated() -> None:
    result = runner.invoke(app, ["risk", "size", "--help"])
    assert "deprecated" in result.output.lower()


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


def test_no_risk_engine_call_in_size_command_body() -> None:
    """The risk_size_command function must not call RiskEngine."""
    source = CLI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "risk_size_command":
            func_source = ast.get_source_segment(source, node) or ""
            assert "RiskEngine" not in func_source, (
                "risk_size_command must not call RiskEngine (deprecated)"
            )


# ── Confirm existing deprecated commands remain deprecated ────────────────────

def test_daily_brief_remains_deprecated() -> None:
    result = runner.invoke(app, ["daily", "brief"])
    assert result.exit_code == 0
    assert "deprecated" in result.output.lower()


def test_watchlist_analyze_remains_deprecated(tmp_path) -> None:
    p = tmp_path / "w.json"
    p.write_text(json.dumps({"name": "Test", "tickers": ["NVDA"]}), encoding="utf-8")
    result = runner.invoke(app, ["watchlist", "analyze", str(p)])
    assert result.exit_code == 0
    assert "deprecated" in result.output.lower()


def test_portfolio_analyze_remains_deprecated(tmp_path) -> None:
    p = tmp_path / "portfolio.json"
    p.write_text(json.dumps({"positions": [{"ticker": "NVDA", "company": "NVIDIA",
        "sector": "Semiconductors", "country": "US", "market_cap": 1000000,
        "weight": 1.0, "quality_score": 90, "risk_score": 50}]}), encoding="utf-8")
    result = runner.invoke(app, ["portfolio", "analyze", str(p), "NVDA"])
    assert result.exit_code == 0
    assert "deprecated" in result.output.lower()


def test_portfolio_review_remains_deprecated(tmp_path) -> None:
    p = tmp_path / "portfolio.json"
    p.write_text(json.dumps({"positions": [{"ticker": "NVDA", "company": "NVIDIA",
        "sector": "Semiconductors", "country": "US", "market_cap": 1000000,
        "weight": 1.0, "quality_score": 90, "risk_score": 50}]}), encoding="utf-8")
    result = runner.invoke(app, ["portfolio", "review", str(p)])
    assert result.exit_code == 0
    assert "deprecated" in result.output.lower()


def test_evidence_assess_remains_deprecated() -> None:
    result = runner.invoke(app, ["evidence", "assess"])
    assert result.exit_code == 0
    assert "deprecated" in result.output.lower()


def test_reason_analyze_remains_deprecated() -> None:
    result = runner.invoke(app, ["reason", "analyze"])
    assert result.exit_code == 0
    assert "deprecated" in result.output.lower()

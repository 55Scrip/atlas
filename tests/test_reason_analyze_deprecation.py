"""Sprint 82: Tests for atlas reason analyze deprecation.

Confirms that `atlas reason analyze` is deprecated, does not call
ReasoningEngine or providers, and that existing deprecated commands
remain deprecated.
"""

from __future__ import annotations

import ast
from pathlib import Path

from typer.testing import CliRunner

from atlas.cli.main import app

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI_PATH = REPO_ROOT / "atlas" / "cli" / "main.py"

runner = CliRunner()


def test_reason_analyze_command_exits_cleanly() -> None:
    result = runner.invoke(app, ["reason", "analyze"])
    assert result.exit_code == 0, f"Expected exit 0, got {result.exit_code}: {result.output}"


def test_reason_analyze_command_prints_deprecation_message() -> None:
    result = runner.invoke(app, ["reason", "analyze"])
    assert "deprecated" in result.output.lower()


def test_reason_analyze_deprecation_does_not_invent_replacement_command() -> None:
    """Deprecation message must not reference a non-existent replacement command."""
    result = runner.invoke(app, ["reason", "analyze"])
    output_lower = result.output.lower()
    assert "atlas reason" not in output_lower or "deprecated" in output_lower
    assert "atlas reasoning" not in output_lower


def test_reason_analyze_deprecation_mentions_consolidation() -> None:
    result = runner.invoke(app, ["reason", "analyze"])
    output_lower = result.output.lower()
    assert "consolidat" in output_lower or "blueprint" in output_lower or "research" in output_lower


def test_reason_analyze_does_not_call_providers() -> None:
    result = runner.invoke(app, ["reason", "analyze"])
    assert result.exit_code == 0
    assert "yahoo" not in result.output.lower()


def test_reason_analyze_help_text_marks_deprecated() -> None:
    result = runner.invoke(app, ["reason", "analyze", "--help"])
    assert "deprecated" in result.output.lower()


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


def test_no_reasoning_engine_call_in_analyze_command_body() -> None:
    """The reason_analyze_command function must not call ReasoningEngine."""
    source = CLI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "reason_analyze_command":
            func_source = ast.get_source_segment(source, node) or ""
            assert "ReasoningEngine" not in func_source, (
                "reason_analyze_command must not call ReasoningEngine (deprecated)"
            )


def test_build_reasoning_report_helper_is_removed() -> None:
    """The _build_reasoning_report private helper was dead code after Sprint 82 — must be gone."""
    source = CLI_PATH.read_text(encoding="utf-8")
    assert "_build_reasoning_report" not in source, (
        "_build_reasoning_report dead-code helper should have been removed in Sprint 82"
    )


# ── Confirm existing deprecated commands remain deprecated ────────────────────

def test_daily_brief_remains_deprecated() -> None:
    result = runner.invoke(app, ["daily", "brief"])
    assert result.exit_code == 0
    assert "deprecated" in result.output.lower()


def test_watchlist_analyze_remains_deprecated(tmp_path) -> None:
    import json
    p = tmp_path / "w.json"
    p.write_text(json.dumps({"name": "Test", "tickers": ["NVDA"]}), encoding="utf-8")
    result = runner.invoke(app, ["watchlist", "analyze", str(p)])
    assert result.exit_code == 0
    assert "deprecated" in result.output.lower()


def test_portfolio_analyze_remains_deprecated(tmp_path) -> None:
    import json
    p = tmp_path / "portfolio.json"
    p.write_text(json.dumps({"positions": [{"ticker": "NVDA", "company": "NVIDIA",
        "sector": "Semiconductors", "country": "US", "market_cap": 1000000,
        "weight": 1.0, "quality_score": 90, "risk_score": 50}]}), encoding="utf-8")
    result = runner.invoke(app, ["portfolio", "analyze", str(p), "NVDA"])
    assert result.exit_code == 0
    assert "deprecated" in result.output.lower()


def test_portfolio_review_remains_deprecated(tmp_path) -> None:
    import json
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

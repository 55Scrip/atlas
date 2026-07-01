"""Sprint 81: Tests for atlas evidence assess deprecation.

Confirms that `atlas evidence assess` is deprecated, does not call
EvidenceQualityEngine or providers, and that existing deprecated commands
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


def test_evidence_assess_command_exits_cleanly() -> None:
    result = runner.invoke(app, ["evidence", "assess"])
    assert result.exit_code == 0, f"Expected exit 0, got {result.exit_code}: {result.output}"


def test_evidence_assess_command_prints_deprecation_message() -> None:
    result = runner.invoke(app, ["evidence", "assess"])
    assert "deprecated" in result.output.lower()


def test_evidence_assess_deprecation_does_not_invent_replacement_command() -> None:
    """Deprecation message must not reference a non-existent replacement command."""
    result = runner.invoke(app, ["evidence", "assess"])
    # No specific 'atlas X' replacement command is invented — only general consolidation direction
    assert "deprecated" in result.output.lower()
    # Must not falsely promise an 'atlas evidence' replacement that doesn't exist
    assert "atlas evidence quality" not in result.output.lower()
    assert "atlas evidence review" not in result.output.lower()


def test_evidence_assess_deprecation_mentions_consolidation() -> None:
    result = runner.invoke(app, ["evidence", "assess"])
    output_lower = result.output.lower()
    # Should mention consolidation direction
    assert "consolidat" in output_lower or "blueprint" in output_lower or "research" in output_lower


def test_evidence_assess_does_not_call_providers() -> None:
    result = runner.invoke(app, ["evidence", "assess"])
    assert result.exit_code == 0
    assert "yahoo" not in result.output.lower()


def test_evidence_assess_help_text_marks_deprecated() -> None:
    result = runner.invoke(app, ["evidence", "assess", "--help"])
    assert "deprecated" in result.output.lower()


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


def test_no_evidence_engine_call_in_assess_command_body() -> None:
    """The evidence_assess_command function must not call EvidenceQualityEngine."""
    source = CLI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "evidence_assess_command":
            func_source = ast.get_source_segment(source, node) or ""
            assert "EvidenceQualityEngine" not in func_source, (
                "evidence_assess_command must not call EvidenceQualityEngine (deprecated)"
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

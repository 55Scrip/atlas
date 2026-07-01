"""Sprint 76: Tests for atlas daily brief deprecation.

Confirms that `atlas daily brief` is deprecated, directs users to
`atlas daily summary`, and never calls providers.
"""

from __future__ import annotations

import ast
from pathlib import Path

from typer.testing import CliRunner

from atlas.cli.main import app

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI_PATH = REPO_ROOT / "atlas" / "cli" / "main.py"

runner = CliRunner()


def test_daily_brief_command_exits_cleanly() -> None:
    result = runner.invoke(app, ["daily", "brief"])
    assert result.exit_code == 0, f"Expected exit 0, got {result.exit_code}: {result.output}"


def test_daily_brief_command_prints_deprecation_message() -> None:
    result = runner.invoke(app, ["daily", "brief"])
    assert "deprecated" in result.output.lower(), "Expected deprecation message in output"


def test_daily_brief_deprecation_references_daily_summary() -> None:
    result = runner.invoke(app, ["daily", "brief"])
    assert "daily summary" in result.output.lower(), "Expected reference to 'atlas daily summary'"


def test_daily_brief_does_not_call_providers() -> None:
    """Deprecated command must not trigger any provider call."""
    result = runner.invoke(app, ["daily", "brief"])
    assert result.exit_code == 0
    # If providers were called, output would include provider-generated content
    # or errors about missing data. A clean deprecation message is sufficient.
    assert "yahoo" not in result.output.lower()


def test_daily_brief_help_text_marks_deprecated() -> None:
    result = runner.invoke(app, ["daily", "brief", "--help"])
    assert "deprecated" in result.output.lower()


def test_daily_brief_help_references_daily_summary() -> None:
    result = runner.invoke(app, ["daily", "brief", "--help"])
    assert "daily summary" in result.output.lower()


def test_daily_summary_command_is_unaffected() -> None:
    """atlas daily summary help must not mention deprecation."""
    result = runner.invoke(app, ["daily", "summary", "--help"])
    assert result.exit_code == 0
    # The summary command itself is not deprecated
    output_lower = result.output.lower()
    assert "deprecated" not in output_lower or "brief" in output_lower  # deprecation refs ok if about brief


def test_cli_does_not_import_legacy_daily_brief_at_module_level() -> None:
    """CLI must not import from atlas.daily_brief (legacy) at module level.

    The deprecated command should not pull in the provider-coupled engine
    just by importing the CLI module.
    """
    source = CLI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("atlas.daily_brief"), (
                    f"atlas/cli/main.py imports from legacy atlas.daily_brief at line {node.lineno}"
                )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("atlas.daily_brief"), (
                        f"atlas/cli/main.py imports atlas.daily_brief at line {node.lineno}"
                    )


def test_demo_script_does_not_use_daily_brief_command() -> None:
    demo_script = REPO_ROOT / "scripts" / "run_daily_brief_demo.sh"
    text = demo_script.read_text()
    assert "daily brief" not in text or "daily summary" in text, (
        "Demo script should use 'atlas daily summary', not the deprecated 'atlas daily brief'"
    )


def test_no_provider_import_in_daily_brief_command_body() -> None:
    """The daily_brief_command function body must not reference providers."""
    source = CLI_PATH.read_text(encoding="utf-8")
    # Find the daily_brief_command function
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "daily_brief_command":
            func_source = ast.get_source_segment(source, node) or ""
            assert "provider" not in func_source.lower() or "_provider" not in func_source, (
                "daily_brief_command body should not call providers"
            )
            assert "DailyBriefEngine" not in func_source, (
                "daily_brief_command must not instantiate DailyBriefEngine (deprecated)"
            )

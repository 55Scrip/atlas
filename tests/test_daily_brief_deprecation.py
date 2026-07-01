"""Sprint 85: Tests confirming atlas daily brief has been retired.

Sprint 76 deprecated the command; Sprint 85 removed the command body entirely.
`atlas daily brief` is no longer a registered CLI command.
`atlas daily summary` remains the supported Daily Brief workflow.
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


def test_daily_brief_command_is_no_longer_registered() -> None:
    """atlas daily brief must not be a recognized subcommand of atlas daily."""
    result = runner.invoke(app, ["daily", "brief"])
    assert result.exit_code != 0


def test_daily_brief_command_is_not_in_active_registry() -> None:
    assert "atlas daily brief" not in all_deprecated_commands()


def test_daily_brief_command_is_in_retired_registry() -> None:
    assert "atlas daily brief" in all_retired_commands()


def test_daily_brief_command_function_removed_from_cli() -> None:
    """The daily_brief_command function must not exist in the CLI source."""
    source = CLI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    func_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    assert "daily_brief_command" not in func_names, (
        "daily_brief_command function should have been removed in Sprint 85"
    )


def test_daily_brief_command_decorator_removed_from_cli() -> None:
    """No @daily_app.command('brief') decorator must exist in the CLI source."""
    source = CLI_PATH.read_text(encoding="utf-8")
    assert '"brief"' not in source or 'daily_app.command("brief")' not in source, (
        "@daily_app.command('brief') should have been removed in Sprint 85"
    )


def test_cli_does_not_import_legacy_daily_brief_at_module_level() -> None:
    """CLI must not import from atlas.daily_brief (legacy engine, deleted Sprint 77)."""
    source = CLI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("atlas.daily_brief"), (
                f"atlas/cli/main.py imports from deleted atlas.daily_brief at line {node.lineno}"
            )


def test_daily_summary_command_is_unaffected() -> None:
    """atlas daily summary must still work and not mention 'deprecated'."""
    result = runner.invoke(app, ["daily", "summary", "--help"])
    assert result.exit_code == 0
    assert "deprecated" not in result.output.lower()


def test_daily_summary_is_present_in_daily_help() -> None:
    """atlas daily --help must list 'summary' as available."""
    result = runner.invoke(app, ["daily", "--help"])
    assert result.exit_code == 0
    assert "summary" in result.output.lower()


def test_demo_script_does_not_use_daily_brief_command() -> None:
    demo_script = REPO_ROOT / "scripts" / "run_daily_brief_demo.sh"
    text = demo_script.read_text()
    assert "daily brief" not in text or "daily summary" in text, (
        "Demo script should use 'atlas daily summary', not the retired 'atlas daily brief'"
    )


def test_no_daily_brief_engine_importable() -> None:
    """atlas.daily_brief module must remain deleted (Sprint 77 invariant)."""
    import importlib
    import sys
    sys.modules.pop("atlas.daily_brief", None)
    try:
        importlib.import_module("atlas.daily_brief")
        raise AssertionError("atlas.daily_brief should not be importable (deleted Sprint 77)")
    except ModuleNotFoundError:
        pass

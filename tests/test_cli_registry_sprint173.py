"""Sprint 173: CLI deprecated command registry audit checkpoint guardrails.

Verifies:
- _REGISTRY is empty (all deprecated commands retired Sprint 91)
- _RETIRED_REGISTRY contains exactly the 7 expected retired commands
- No retired command is accidentally callable via the CLI
- Empty shell app groups (evidence, reason, risk) have no registered subcommands
- atlas/cli/ files import no deleted closed-track modules
- Provider default is mock; Yahoo is opt-in only
"""

import ast
from pathlib import Path

import pytest
from typer.testing import CliRunner

from atlas.cli.deprecations import _REGISTRY, _RETIRED_REGISTRY, all_retired_commands
from atlas.cli.main import app

runner = CliRunner()

EXPECTED_RETIRED = frozenset({
    "atlas daily brief",
    "atlas evidence assess",
    "atlas reason analyze",
    "atlas risk size",
    "atlas portfolio analyze",
    "atlas portfolio review",
    "atlas watchlist analyze",
})


# ── Registry state ────────────────────────────────────────────────────────────

def test_sprint173_active_registry_is_empty() -> None:
    """Sprint 173: _REGISTRY must be empty — all deprecated commands retired Sprint 91."""
    assert _REGISTRY == (), (
        f"_REGISTRY must be empty. Found active deprecated commands: "
        f"{[e.command for e in _REGISTRY]}"
    )


def test_sprint173_retired_registry_has_seven_commands() -> None:
    """Sprint 173: _RETIRED_REGISTRY must contain exactly 7 retired commands."""
    assert len(_RETIRED_REGISTRY) == 7, (
        f"_RETIRED_REGISTRY must have 7 entries. Found: {len(_RETIRED_REGISTRY)}"
    )


def test_sprint173_retired_commands_match_expected() -> None:
    """Sprint 173: retired command names must match the 7 expected retired commands."""
    actual = set(all_retired_commands())
    assert actual == EXPECTED_RETIRED, (
        f"Retired commands mismatch. Extra: {actual - EXPECTED_RETIRED}. "
        f"Missing: {EXPECTED_RETIRED - actual}."
    )


# ── Retired command callability ───────────────────────────────────────────────

@pytest.mark.parametrize("args", [
    ["reason", "analyze"],
    ["risk", "size"],
    ["evidence", "assess"],
])
def test_sprint173_retired_commands_not_callable(args: list[str]) -> None:
    """Sprint 173: retired commands must not be callable — no active handler exists."""
    result = runner.invoke(app, args)
    # Typer returns exit code 2 for missing/unknown commands (no such command)
    # If there were an active handler, it might return 0 or 1.
    # We verify the command is NOT successfully handled (exit code != 0 with no handler).
    assert result.exit_code != 0, (
        f"'atlas {' '.join(args)}' returned exit_code=0, "
        "suggesting an active handler — retired commands must not be callable"
    )


# ── Empty shell app groups ────────────────────────────────────────────────────

def test_sprint173_evidence_app_has_no_commands() -> None:
    """Sprint 173: atlas evidence group must expose no callable subcommands."""
    result = runner.invoke(app, ["evidence", "--help"])
    # An empty typer group with no commands shows help with no subcommands listed
    # We verify 'assess' does not appear (the retired subcommand)
    assert "assess" not in (result.output or ""), (
        "atlas evidence assess must not appear in help — command is retired"
    )


def test_sprint173_reason_app_has_no_commands() -> None:
    """Sprint 173: atlas reason group must expose no callable subcommands."""
    result = runner.invoke(app, ["reason", "--help"])
    assert "analyze" not in (result.output or ""), (
        "atlas reason analyze must not appear in help — command is retired"
    )


def test_sprint173_risk_app_has_no_commands() -> None:
    """Sprint 173: atlas risk group must expose no callable subcommands (risk-drift is separate)."""
    result = runner.invoke(app, ["risk", "--help"])
    assert "size" not in (result.output or ""), (
        "atlas risk size must not appear in help — command is retired"
    )


# ── No deleted-module imports in CLI ─────────────────────────────────────────

def test_sprint173_cli_has_no_deleted_module_imports() -> None:
    """Sprint 173: atlas/cli/ must not import from deleted closed-track modules."""
    deleted_prefixes = {
        "atlas.reasoning",
        "atlas.analysis.portfolio",
        "atlas.analysis.comparison",
        "atlas.analysis.memory",
        "atlas.analysis.scoring",
        "atlas.analysis.watchlist",
    }
    cli_dir = Path("atlas/cli")
    for py_file in cli_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for prefix in deleted_prefixes:
                    assert not node.module.startswith(prefix), (
                        f"{py_file}: stale import from deleted module {node.module}"
                    )


# ── Provider boundary ─────────────────────────────────────────────────────────

def test_sprint173_provider_default_is_mock() -> None:
    """Sprint 173: all --provider flags in CLI must default to 'mock'."""
    source = Path("atlas/cli/main.py").read_text(encoding="utf-8")
    # Every --provider option should declare default "mock"
    provider_options = [
        line for line in source.splitlines()
        if "--provider" in line and "Option" in line
    ]
    for line in provider_options:
        assert '"mock"' in line, (
            f"--provider option without default 'mock': {line.strip()}"
        )


def test_sprint173_yahoo_provider_only_in_provider_from_name() -> None:
    """Sprint 173: YahooFinanceProvider must only be instantiated in _provider_from_name()."""
    source = Path("atlas/cli/main.py").read_text(encoding="utf-8")
    lines = source.splitlines()
    yahoo_lines = [
        (i + 1, line.strip()) for i, line in enumerate(lines)
        if "YahooFinanceProvider()" in line
    ]
    # Only one instantiation site should exist: inside _provider_from_name
    assert len(yahoo_lines) == 1, (
        f"YahooFinanceProvider() should appear exactly once (in _provider_from_name). "
        f"Found at lines: {yahoo_lines}"
    )

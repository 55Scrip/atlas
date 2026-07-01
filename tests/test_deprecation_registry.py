"""Sprint 84: Tests for the centralized deprecation registry.

Covers:
- registry completeness (all 7 deprecated commands are present)
- message content rules (deprecated keyword, no invented commands)
- replacement_command vs consolidation_direction exclusivity
- no engine/provider imports in the registry module itself
- all deprecated CLI commands still route through registry and exit cleanly
- Blueprint-aligned commands are unaffected
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from atlas.cli.deprecations import (
    DeprecatedCommand,
    all_deprecated_commands,
    all_retired_commands,
    deprecated_command_message,
    get_deprecated_command,
)
from atlas.cli.main import app

REGISTRY_PATH = Path(__file__).resolve().parent.parent / "atlas" / "cli" / "deprecations.py"

runner = CliRunner()

# Sprint 91: all deprecated commands retired — active registry is empty
EXPECTED_COMMANDS: tuple[str, ...] = ()

RETIRED_COMMANDS = (
    "atlas daily brief",
    "atlas evidence assess",
    "atlas reason analyze",
    "atlas risk size",
    "atlas portfolio analyze",
    "atlas portfolio review",
    "atlas watchlist analyze",
)

# ── Registry completeness ─────────────────────────────────────────────────────

def test_all_expected_commands_are_registered() -> None:
    registered = all_deprecated_commands()
    for cmd in EXPECTED_COMMANDS:
        assert cmd in registered, f"'{cmd}' missing from deprecation registry"


def test_registry_has_exactly_the_expected_commands() -> None:
    registered = set(all_deprecated_commands())
    expected = set(EXPECTED_COMMANDS)
    assert registered == expected, (
        f"Registry mismatch. Extra: {registered - expected}. Missing: {expected - registered}."
    )


# ── Message content rules ─────────────────────────────────────────────────────

@pytest.mark.parametrize("command", EXPECTED_COMMANDS)
def test_each_message_contains_deprecated(command: str) -> None:
    msg = deprecated_command_message(command)
    assert "deprecated" in msg.lower(), f"'{command}' message missing 'deprecated'"


@pytest.mark.parametrize("command", EXPECTED_COMMANDS)
def test_each_message_contains_command_name(command: str) -> None:
    # The CLI command slug (e.g. "risk size") must appear in the message
    slug = command.replace("atlas ", "")
    msg = deprecated_command_message(command)
    assert slug in msg, f"'{command}' message does not mention the command name"


def test_replacement_commands_are_only_set_where_they_exist() -> None:
    """Commands with replacement_command must reference a real Blueprint-aligned command."""
    real_replacements = {
        "atlas daily summary",
        "atlas watchlist intelligence",
        "atlas portfolio summary",
    }
    for cmd in EXPECTED_COMMANDS:
        entry = get_deprecated_command(cmd)
        if entry.replacement_command is not None:
            assert entry.replacement_command in real_replacements, (
                f"'{cmd}' points to invented replacement '{entry.replacement_command}'"
            )


def test_consolidation_direction_set_when_no_replacement() -> None:
    for cmd in EXPECTED_COMMANDS:
        entry = get_deprecated_command(cmd)
        if entry.replacement_command is None:
            assert entry.consolidation_direction, (
                f"'{cmd}' has no replacement_command and no consolidation_direction"
            )


def test_replacement_and_consolidation_not_both_set() -> None:
    for cmd in EXPECTED_COMMANDS:
        entry = get_deprecated_command(cmd)
        assert not (entry.replacement_command and entry.consolidation_direction), (
            f"'{cmd}' has both replacement_command and consolidation_direction — pick one"
        )


# ── No engine/provider imports in registry ────────────────────────────────────

def test_registry_module_does_not_import_legacy_engines() -> None:
    source = REGISTRY_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_prefixes = (
        "atlas.daily_brief",
        "atlas.evidence",
        "atlas.reasoning",
        "atlas.risk",
        "atlas.watchlist",
        "atlas.portfolio_review",
        "atlas.analysis.portfolio",
        "atlas.analysis.watchlist",
        "atlas.providers",
        "atlas.domains",
    )
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mod = getattr(node, "module", None) or ""
            for names in (getattr(node, "names", []),):
                for alias in names:
                    full = alias.name if isinstance(node, ast.Import) else mod
                    for prefix in forbidden_prefixes:
                        assert not full.startswith(prefix), (
                            f"deprecations.py must not import '{full}' (legacy engine / provider / domain)"
                        )


# ── CLI behavior via registry ─────────────────────────────────────────────────

def test_daily_brief_is_retired_not_active() -> None:
    """Sprint 85: atlas daily brief was retired — must not be in active registry."""
    assert "atlas daily brief" not in all_deprecated_commands()


def test_daily_brief_is_in_retired_registry() -> None:
    assert "atlas daily brief" in all_retired_commands()


def test_daily_brief_command_is_no_longer_callable() -> None:
    """Sprint 85: atlas daily brief is retired — CLI should not recognize it."""
    result = runner.invoke(app, ["daily", "brief"])
    assert result.exit_code != 0


def test_evidence_assess_is_retired_not_active() -> None:
    """Sprint 86: atlas evidence assess was retired — must not be in active registry."""
    assert "atlas evidence assess" not in all_deprecated_commands()


def test_evidence_assess_is_in_retired_registry() -> None:
    assert "atlas evidence assess" in all_retired_commands()


def test_evidence_assess_command_is_no_longer_callable() -> None:
    """Sprint 86: atlas evidence assess is retired — CLI should not recognize it."""
    result = runner.invoke(app, ["evidence", "assess"])
    assert result.exit_code != 0


def test_reason_analyze_is_retired_not_active() -> None:
    """Sprint 87: atlas reason analyze was retired — must not be in active registry."""
    assert "atlas reason analyze" not in all_deprecated_commands()


def test_reason_analyze_is_in_retired_registry() -> None:
    assert "atlas reason analyze" in all_retired_commands()


def test_reason_analyze_command_is_no_longer_callable() -> None:
    """Sprint 87: atlas reason analyze is retired — CLI should not recognize it."""
    result = runner.invoke(app, ["reason", "analyze"])
    assert result.exit_code != 0


def test_risk_size_is_retired_not_active() -> None:
    """Sprint 88: atlas risk size was retired — must not be in active registry."""
    assert "atlas risk size" not in all_deprecated_commands()


def test_risk_size_is_in_retired_registry() -> None:
    assert "atlas risk size" in all_retired_commands()


def test_risk_size_command_is_no_longer_callable(tmp_path) -> None:
    """Sprint 88: atlas risk size is retired — CLI should not recognize it."""
    p = tmp_path / "r.json"
    p.write_text(json.dumps({"ticker": "NVDA"}), encoding="utf-8")
    result = runner.invoke(app, ["risk", "size", str(p)])
    assert result.exit_code != 0


def test_portfolio_review_is_retired_not_active() -> None:
    """Sprint 90: atlas portfolio review was retired — must not be in active registry."""
    assert "atlas portfolio review" not in all_deprecated_commands()


def test_portfolio_review_is_in_retired_registry() -> None:
    assert "atlas portfolio review" in all_retired_commands()


def test_portfolio_review_command_is_no_longer_callable(tmp_path) -> None:
    """Sprint 90: atlas portfolio review is retired — CLI should not recognize it."""
    p = tmp_path / "portfolio.json"
    p.write_text(json.dumps({"positions": [{"ticker": "NVDA", "company": "NVIDIA",
        "sector": "Semiconductors", "country": "US", "market_cap": 1000000,
        "weight": 1.0, "quality_score": 90, "risk_score": 50}]}), encoding="utf-8")
    result = runner.invoke(app, ["portfolio", "review", str(p)])
    assert result.exit_code != 0


def test_portfolio_analyze_is_retired_not_active() -> None:
    """Sprint 89: atlas portfolio analyze was retired — must not be in active registry."""
    assert "atlas portfolio analyze" not in all_deprecated_commands()


def test_portfolio_analyze_is_in_retired_registry() -> None:
    assert "atlas portfolio analyze" in all_retired_commands()


def test_portfolio_analyze_command_is_no_longer_callable(tmp_path) -> None:
    """Sprint 89: atlas portfolio analyze is retired — CLI should not recognize it."""
    p = tmp_path / "portfolio.json"
    p.write_text(json.dumps({"positions": [{"ticker": "NVDA", "company": "NVIDIA",
        "sector": "Semiconductors", "country": "US", "market_cap": 1000000,
        "weight": 1.0, "quality_score": 90, "risk_score": 50}]}), encoding="utf-8")
    result = runner.invoke(app, ["portfolio", "analyze", str(p), "NVDA"])
    assert result.exit_code != 0


def test_watchlist_analyze_is_retired_not_active() -> None:
    """Sprint 91: atlas watchlist analyze was retired — must not be in active registry."""
    assert "atlas watchlist analyze" not in all_deprecated_commands()


def test_watchlist_analyze_is_in_retired_registry() -> None:
    assert "atlas watchlist analyze" in all_retired_commands()


def test_watchlist_analyze_command_is_no_longer_callable(tmp_path) -> None:
    """Sprint 91: atlas watchlist analyze is retired — CLI should not recognize it."""
    p = tmp_path / "w.json"
    p.write_text(json.dumps({"name": "Test", "tickers": ["NVDA"]}), encoding="utf-8")
    result = runner.invoke(app, ["watchlist", "analyze", str(p)])
    assert result.exit_code != 0


def test_active_registry_is_empty() -> None:
    """Sprint 91: all deprecated commands retired — active registry must be empty."""
    assert all_deprecated_commands() == ()


# ── Blueprint-aligned commands unaffected ─────────────────────────────────────

def test_daily_summary_command_is_unaffected() -> None:
    """atlas daily summary must not mention 'deprecated'."""
    result = runner.invoke(app, ["daily", "summary"])
    assert "deprecated" not in result.output.lower()


def test_registry_key_error_for_unknown_command() -> None:
    with pytest.raises(KeyError):
        deprecated_command_message("atlas does not exist")


# ── No recommendation language ────────────────────────────────────────────────

FORBIDDEN_PHRASES = (
    "strong buy", "strong sell", "buy now", "sell now",
    "price target", "outperform", "market-beating",
    "guaranteed", "risk-free", "urgent",
)

@pytest.mark.parametrize("command", EXPECTED_COMMANDS)
def test_no_recommendation_language_in_messages(command: str) -> None:
    msg = deprecated_command_message(command).lower()
    for phrase in FORBIDDEN_PHRASES:
        assert phrase not in msg, (
            f"'{command}' deprecation message contains forbidden phrase '{phrase}'"
        )

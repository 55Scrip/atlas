"""Sprint 174: CLI empty shell group removal guardrails.

Verifies that the three empty CLI app groups removed in Sprint 174
no longer appear in the root atlas --help output, and that active
groups remain present.
"""

from typer.testing import CliRunner
from atlas.cli.main import app

runner = CliRunner()


# ── Removed empty groups absent from root help ────────────────────────────────

def test_sprint174_evidence_group_removed_from_help() -> None:
    """Sprint 174: 'evidence' group must not appear in atlas --help (removed Sprint 174)."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    lines = result.output.splitlines()
    group_names = [line.strip().split()[0] for line in lines if line.strip() and not line.startswith("│ --")]
    assert "evidence" not in result.output.lower().split() or all(
        "evidence" not in line.strip().lower().split() or "assess" in line
        for line in lines
    ), "evidence group must not appear as a command group in atlas --help"
    # Simpler: just confirm invoking atlas evidence fails
    fail_result = runner.invoke(app, ["evidence", "--help"])
    assert fail_result.exit_code != 0, (
        "'atlas evidence' must not be a registered command group after Sprint 174 removal"
    )


def test_sprint174_reason_group_removed_from_help() -> None:
    """Sprint 174: 'reason' group must not appear in atlas --help (removed Sprint 174)."""
    fail_result = runner.invoke(app, ["reason", "--help"])
    assert fail_result.exit_code != 0, (
        "'atlas reason' must not be a registered command group after Sprint 174 removal"
    )


def test_sprint174_risk_group_removed_from_help() -> None:
    """Sprint 174: 'risk' group must not appear in atlas --help (removed Sprint 174)."""
    fail_result = runner.invoke(app, ["risk", "--help"])
    assert fail_result.exit_code != 0, (
        "'atlas risk' must not be a registered command group after Sprint 174 removal. "
        "Note: 'atlas risk-drift' is a separate active group and must remain."
    )


# ── Active groups remain present ──────────────────────────────────────────────

def test_sprint174_active_groups_remain_in_help() -> None:
    """Sprint 174: active CLI groups must still appear in atlas --help."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    expected_active = [
        "intelligence",
        "dashboard",
        "principles",
        "risk-drift",
        "watchlist",
        "daily",
        "portfolio",
    ]
    for group in expected_active:
        assert group in result.output, (
            f"Active group '{group}' must still appear in atlas --help after Sprint 174"
        )


# ── Retired commands remain not callable ──────────────────────────────────────

def test_sprint174_retired_commands_still_not_callable() -> None:
    """Sprint 174: removing empty groups must not accidentally enable retired commands."""
    retired = [
        ["evidence", "assess"],
        ["reason", "analyze"],
        ["risk", "size"],
    ]
    for args in retired:
        result = runner.invoke(app, args)
        assert result.exit_code != 0, (
            f"'atlas {' '.join(args)}' must remain not callable after Sprint 174 removal"
        )

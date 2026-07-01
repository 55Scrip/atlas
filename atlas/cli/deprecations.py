"""CLI deprecation registry for Atlas legacy commands.

Each entry documents a deprecated command, its user-facing message, and
the criteria for future deletion. This module has no runtime dependencies
on legacy engines, providers, or domains — it is a pure data/formatting
helper. It is CLI-local and must stay that way.

Usage in a CLI command body:

    from atlas.cli.deprecations import deprecated_command_message
    console.print(deprecated_command_message("atlas <command>"))
    raise typer.Exit(code=0)

Retired commands are recorded in _RETIRED_REGISTRY for audit purposes but
are no longer registered in the CLI and are not callable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DeprecatedCommand:
    """Metadata and message template for a single deprecated CLI command."""

    # Full CLI invocation string, e.g. "atlas daily brief"
    command: str

    # Rich-formatted user-facing deprecation message (printed to stdout).
    message: str

    # Blueprint-aligned replacement command, if one exists. None otherwise.
    replacement_command: Optional[str]

    # Where the work is going if no replacement command exists yet.
    consolidation_direction: Optional[str]

    # Legacy Python module still on disk behind this command.
    legacy_module: str

    # What must be true before the command body and/or engine can be deleted.
    removal_criteria: tuple[str, ...]


# ── Retired commands (no longer registered in CLI) ────────────────────────────
# Kept for historical record; these commands are not callable.

_RETIRED_REGISTRY: tuple[DeprecatedCommand, ...] = (
    DeprecatedCommand(
        command="atlas daily brief",
        message=(
            "[yellow]DEPRECATED:[/yellow] The command [bold]atlas daily brief[/bold] is deprecated.\n"
            "Use [bold]atlas daily summary[/bold] for the Blueprint-aligned Daily Brief workflow.\n"
            "\n"
            "    atlas daily summary --help"
        ),
        replacement_command="atlas daily summary",
        consolidation_direction=None,
        legacy_module="atlas.daily_brief",
        removal_criteria=(
            "atlas.daily_brief engine was deleted in Sprint 77.",
            "Command body retired in Sprint 85 — no remaining dependency.",
        ),
    ),
    DeprecatedCommand(
        command="atlas evidence assess",
        message=(
            "[yellow]DEPRECATED:[/yellow] The command [bold]atlas evidence assess[/bold] is deprecated.\n"
            "Evidence assessment is being consolidated into Blueprint-aligned decision and research capabilities."
        ),
        replacement_command=None,
        consolidation_direction="Blueprint-aligned decision and research capabilities",
        legacy_module="atlas.evidence",
        removal_criteria=(
            "Command body retired in Sprint 86.",
            "atlas.evidence engine remains on disk — still used by atlas/comparison, "
            "atlas/decision_journal, and atlas/watchlist_review. Engine deletion deferred "
            "until those callers are retired.",
        ),
    ),
)

# ── Active deprecated commands (still registered in CLI) ──────────────────────

_REGISTRY: tuple[DeprecatedCommand, ...] = (
    DeprecatedCommand(
        command="atlas watchlist analyze",
        message=(
            "[yellow]DEPRECATED:[/yellow] The command [bold]atlas watchlist analyze[/bold] is deprecated.\n"
            "Use [bold]atlas watchlist intelligence[/bold] for the Blueprint-aligned Watchlist Intelligence workflow.\n"
            "\n"
            "    atlas watchlist intelligence --help"
        ),
        replacement_command="atlas watchlist intelligence",
        consolidation_direction=None,
        legacy_module="atlas.analysis.watchlist",
        removal_criteria=(
            "WatchlistEngine is still imported by atlas/home, atlas/monitoring, atlas/decision, "
            "atlas/watchlist_review, atlas/conversation, atlas/intelligence — those must be retired first.",
            "Once WatchlistEngine has no non-deprecated callers, engine and command body can be deleted together.",
        ),
    ),
    DeprecatedCommand(
        command="atlas portfolio analyze",
        message=(
            "[yellow]DEPRECATED:[/yellow] The command [bold]atlas portfolio analyze[/bold] is deprecated.\n"
            "Use [bold]atlas portfolio summary[/bold] for the Blueprint-aligned Portfolio Domain workflow.\n"
            "\n"
            "    atlas portfolio summary --help"
        ),
        replacement_command="atlas portfolio summary",
        consolidation_direction=None,
        legacy_module="atlas.analysis.portfolio",
        removal_criteria=(
            "PortfolioIntelligenceEngine must have no remaining non-deprecated callers.",
            "Confirm atlas.analysis.portfolio is unused before deleting.",
        ),
    ),
    DeprecatedCommand(
        command="atlas portfolio review",
        message=(
            "[yellow]DEPRECATED:[/yellow] The command [bold]atlas portfolio review[/bold] is deprecated.\n"
            "Use [bold]atlas portfolio summary[/bold] for the Blueprint-aligned Portfolio Domain workflow.\n"
            "\n"
            "    atlas portfolio summary --help"
        ),
        replacement_command="atlas portfolio summary",
        consolidation_direction=None,
        legacy_module="atlas.portfolio_review",
        removal_criteria=(
            "PortfolioReviewEngine must have no remaining non-deprecated callers.",
            "Confirm atlas.portfolio_review is unused before deleting.",
        ),
    ),
    DeprecatedCommand(
        command="atlas reason analyze",
        message=(
            "[yellow]DEPRECATED:[/yellow] The command [bold]atlas reason analyze[/bold] is deprecated.\n"
            "Reasoning analysis is being consolidated into Blueprint-aligned decision and research capabilities."
        ),
        replacement_command=None,
        consolidation_direction="Blueprint-aligned decision and research capabilities",
        legacy_module="atlas.reasoning",
        removal_criteria=(
            "ReasoningEngine lazy import in atlas/principles/engine.py must be removed first.",
            "Confirm atlas.reasoning.ReasoningEngine has no non-deprecated callers before deleting.",
        ),
    ),
    DeprecatedCommand(
        command="atlas risk size",
        message=(
            "[yellow]DEPRECATED:[/yellow] The command [bold]atlas risk size[/bold] is deprecated.\n"
            "Risk sizing is being consolidated into Blueprint-aligned portfolio, decision and research capabilities."
        ),
        replacement_command=None,
        consolidation_direction="Blueprint-aligned portfolio, decision and research capabilities",
        legacy_module="atlas.risk",
        removal_criteria=(
            "RiskAnalysis type is still imported by atlas/intelligence, atlas/reasoning, atlas/conversation — "
            "confirm RiskEngine class itself has no callers.",
            "Delete RiskEngine and PositionSizingInput once confirmed unused; RiskAnalysis type may need to stay.",
        ),
    ),
)

# ── Public API ────────────────────────────────────────────────────────────────

_BY_COMMAND: dict[str, DeprecatedCommand] = {entry.command: entry for entry in _REGISTRY}


def deprecated_command_message(command: str) -> str:
    """Return the Rich-formatted deprecation message for the given CLI command.

    Raises KeyError if the command is not in the registry.
    """
    return _BY_COMMAND[command].message


def all_deprecated_commands() -> tuple[str, ...]:
    """Return the command strings for every registered deprecated command."""
    return tuple(entry.command for entry in _REGISTRY)


def get_deprecated_command(command: str) -> DeprecatedCommand:
    """Return the full DeprecatedCommand entry for the given CLI command.

    Raises KeyError if the command is not in the registry.
    """
    return _BY_COMMAND[command]


def all_retired_commands() -> tuple[str, ...]:
    """Return the command strings for every retired (removed from CLI) command."""
    return tuple(entry.command for entry in _RETIRED_REGISTRY)

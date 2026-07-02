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
            "Command body retired in Sprint 87.",
            "atlas.reasoning engine remains on disk — atlas/principles/engine.py has a lazy import "
            "of render_reasoning_report inside check_reasoning_report() (TYPE_CHECKING import of "
            "ReasoningReport is not a runtime dependency). Engine deletion requires removing or "
            "replacing check_reasoning_report() first.",
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
            "Command body retired in Sprint 88.",
            "atlas.risk engine remains on disk — RiskAnalysis type is still imported by "
            "atlas/conversation, atlas/intelligence, and atlas/reasoning engines. "
            "RiskEngine has no production instantiation points outside deprecated CLI. "
            "Engine deletion deferred: RiskEngine and RiskAnalysis live in the same file; "
            "separating them requires surgery to atlas/risk/engine.py and atlas/risk/__init__.py.",
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
            "Command body retired in Sprint 89.",
            "atlas.analysis.portfolio engine remains on disk — Portfolio, PortfolioAnalysis, and "
            "PortfolioIntelligenceEngine are still imported by atlas/intelligence, atlas/conversation, "
            "atlas/decision, atlas/dashboard, atlas/reasoning, atlas/home, atlas/suitability, "
            "atlas/risk_drift, atlas/monitoring, and atlas/portfolio_review. Engine deletion deferred "
            "until all those callers are retired.",
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
            "Command body retired in Sprint 90.",
            "atlas.portfolio_review engine remains on disk — PortfolioReviewEngine is still imported "
            "and instantiated by atlas/home/engine.py (AtlasHomeEngine). Engine deletion deferred "
            "until AtlasHomeEngine is retired or migrated to the Blueprint-aligned "
            "atlas.domains.portfolio.review.PortfolioReviewEngine.",
        ),
    ),
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
            "Command body retired in Sprint 91.",
            "WatchlistEngine deleted in Sprint 99 — all five callers retired across Sprints 93–98. "
            "atlas/analysis/watchlist.py retained as type-only module (Watchlist, WatchlistItem).",
        ),
    ),
)

# ── Active deprecated commands (still registered in CLI) ──────────────────────
# Sprint 91: all deprecated commands have been retired. _REGISTRY is now empty.

_REGISTRY: tuple[DeprecatedCommand, ...] = ()

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

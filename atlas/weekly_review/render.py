"""Placeholder renderer for the Atlas Weekly Investment Review skeleton.

Renders all 10 required section headings with safe placeholder content.
No orchestration, no engine calls, no provider dependency.

Sprint 212 will replace placeholder content with deterministic output
derived from the loaded inputs.
"""

from __future__ import annotations

from atlas.weekly_review.inputs import WeeklyReviewLoadResult, WeeklyReviewInputWarning


_TITLE = "Atlas Weekly Investment Review"
_DISCLAIMER = (
    "Atlas Weekly Investment Review — deterministic, local-only, no recommendations.\n"
    "Atlas supports better judgment. It does not replace it."
)


def render_weekly_review_skeleton(result: WeeklyReviewLoadResult) -> str:
    """Render a skeleton Weekly Investment Review from a loaded input bundle.

    All 10 required section headings are present.  Content is placeholder only
    and clearly marked as not final orchestration.  No forbidden language.
    """
    lines: list[str] = []

    lines.append(f"# {_TITLE}")
    lines.append("")
    lines.append(_DISCLAIMER)
    lines.append("")

    # Input status summary
    lines.extend(_render_input_status(result))
    lines.append("")

    # Warnings block
    if result.warnings:
        lines.extend(_render_warnings(result.warnings))
        lines.append("")

    lines.append("---")
    lines.append("")

    # Section 1
    lines.extend(_section(
        "1. Review Scope",
        _review_scope_content(result),
    ))

    # Section 2
    lines.extend(_section(
        "2. Portfolio Context",
        _portfolio_context_content(result),
    ))

    # Section 3
    lines.extend(_section(
        "3. Watchlist Review",
        _watchlist_review_content(result),
    ))

    # Section 4
    lines.extend(_section(
        "4. Company Reviews Needing Attention",
        [
            "Input loaded successfully.",
            "Evidence Gap: Detailed company evidence has not been evaluated yet.",
            "Detailed orchestration will be added in a later sprint.",
        ],
    ))

    # Section 5
    lines.extend(_section(
        "5. Portfolio Fit and Suitability Notes",
        [
            "Input loaded successfully.",
            "Portfolio fit and suitability checks will be added in a later sprint.",
            f"Investor profile: {'Available' if result.profile_available else 'Not provided — default profile will be used.'}",
            "Note: Atlas does not judge investment merit or provide personalized advice.",
        ],
    ))

    # Section 6
    lines.extend(_section(
        "6. Risk and Principle Guardrails",
        [
            "Input loaded successfully.",
            "Risk drift and principle guardrail checks will be added in a later sprint.",
        ],
    ))

    # Section 7
    lines.extend(_section(
        "7. Open Decisions",
        _open_decisions_content(result),
    ))

    # Section 8
    lines.extend(_section(
        "8. Missing Evidence",
        _missing_evidence_content(result),
    ))

    # Section 9
    lines.extend(_section(
        "9. Follow-Up Questions",
        [
            "Follow-up questions will be generated from evidence gaps and open decisions in a later sprint.",
            "Detailed orchestration will be added in a later sprint.",
        ],
    ))

    # Section 10 — always present and non-empty
    lines.extend(_section(
        "10. Non-Actions / Reasons to Wait",
        _non_actions_content(result),
    ))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section content builders
# ---------------------------------------------------------------------------


def _review_scope_content(result: WeeklyReviewLoadResult) -> list[str]:
    lines = []
    if result.as_of:
        lines.append(f"Review date: {result.as_of}")
    else:
        lines.append("Review date: Not specified.")

    holdings = result.portfolio.all_holdings
    lines.append(f"Portfolio: {len(holdings)} holding(s) across {len(result.portfolio.accounts)} account(s).")

    watchlist_count = len(result.watchlist.items)
    lines.append(f"Watchlist: {watchlist_count} item(s) in '{result.watchlist.name}'.")

    if result.scope_notes:
        lines.append(f"Scope notes: {result.scope_notes}")

    return lines


def _portfolio_context_content(result: WeeklyReviewLoadResult) -> list[str]:
    lines = []
    holdings = result.portfolio.all_holdings

    for account in result.portfolio.accounts:
        lines.append(f"Account: {account.name} — {len(account.holdings)} holding(s).")

    tickers = [h.ticker for h in holdings]
    lines.append(f"Tickers: {', '.join(tickers) if tickers else 'None.'}")

    sectors = sorted({h.sector for h in holdings if h.sector})
    lines.append(f"Sectors represented: {', '.join(sectors) if sectors else 'None.'}")

    lines.append("Detailed portfolio analysis will be added in a later sprint.")
    lines.append("Note: All values are user-supplied. No live pricing used.")

    return lines


def _watchlist_review_content(result: WeeklyReviewLoadResult) -> list[str]:
    lines = []
    for item in result.watchlist.items:
        evidence_note = (
            f" ({len(item.evidence_needed)} evidence gap(s))"
            if item.evidence_needed
            else ""
        )
        lines.append(
            f"{item.ticker} — {item.name} | Status: {item.status.value}{evidence_note}"
        )
    lines.append("Detailed watchlist review will be added in a later sprint.")
    return lines


def _open_decisions_content(result: WeeklyReviewLoadResult) -> list[str]:
    if result.journal_entry_count > 0:
        return [
            f"Decision journal loaded: {result.journal_entry_count} entry/entries found.",
            "Open decision review will be added in a later sprint.",
        ]
    return ["No decision journal provided. Open decisions not reviewed."]


def _missing_evidence_content(result: WeeklyReviewLoadResult) -> list[str]:
    lines = []
    for item in result.watchlist.items:
        for gap in item.evidence_needed:
            lines.append(f"Evidence Gap: {item.ticker} — {gap}")
    if not lines:
        lines.append("No evidence gaps identified from watchlist input.")
    lines.append("Additional evidence gaps from company reviews will be added in a later sprint.")
    return lines


def _non_actions_content(result: WeeklyReviewLoadResult) -> list[str]:
    """Section 10 is always present and never empty."""
    lines = [
        "No Action Warranted: This skeleton output does not create investment actions.",
        "Reason to Wait: Full workflow orchestration is not yet implemented.",
        "Reason to Wait: Evidence gaps identified in this review have not yet been fully evaluated.",
        "",
        "Reminder: No action is a valid and often appropriate outcome of a weekly review.",
        "Atlas supports better judgment. It does not replace it.",
    ]
    # Surface deferred watchlist items explicitly
    deferred = [
        item for item in result.watchlist.items
        if item.status.value in ("Decision Deferred", "Needs More Evidence")
    ]
    for item in deferred:
        lines.insert(0, f"Decision Deferred: {item.ticker} — {item.name}. Status: {item.status.value}.")
    return lines


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _section(heading: str, content: list[str]) -> list[str]:
    lines = [f"## {heading}", ""]
    lines.extend(f"- {line}" if line else "" for line in content)
    lines.append("")
    return lines


def _render_input_status(result: WeeklyReviewLoadResult) -> list[str]:
    lines = ["## Input Status", ""]
    lines.append(f"- Portfolio: {len(result.portfolio.all_holdings)} holding(s) loaded.")
    lines.append(f"- Watchlist: {len(result.watchlist.items)} item(s) loaded from '{result.watchlist.name}'.")
    lines.append(
        f"- Investor profile: {'Available' if result.profile_available else 'Not provided — default will be used.'}",
    )
    lines.append(
        f"- Decision journal: "
        + (f"{result.journal_entry_count} entry/entries loaded." if result.journal_entry_count else "Not provided.")
    )
    lines.append(
        f"- Company facts: {'Available' if result.company_facts_available else 'Not provided — evidence gaps noted.'}",
    )
    lines.append(
        f"- Financials: {'Available' if result.financials_available else 'Not provided — evidence gaps noted.'}",
    )
    if result.as_of:
        lines.append(f"- Review date: {result.as_of}")
    return lines


def _render_warnings(warnings: tuple[WeeklyReviewInputWarning, ...]) -> list[str]:
    lines = ["## Input Warnings", ""]
    for w in warnings:
        lines.append(f"- [{w.code}] {w.message}")
    return lines

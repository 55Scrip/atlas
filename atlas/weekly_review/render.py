"""Deterministic renderer for the Atlas Weekly Investment Review.

Renders all 10 required section headings with content derived exclusively from
the loaded WeeklyReviewLoadResult.  No engine calls, no provider dependency,
no network access, no AI.

Sprint 212: replaced placeholder content with input-derived deterministic output.
Sprint 250: added locale-to-strings dispatch helper (_strings_for_locale).
           Swedish strings are mapped but unreachable while sv is unsupported.
"""

from __future__ import annotations

import datetime
from collections import defaultdict

from atlas.weekly_review.inputs import (
    WeeklyReviewInputWarning,
    WeeklyReviewLoadResult,
    WeeklyReviewResearchNote,
    WeeklyReviewWatchlistStatus,
)
from atlas.weekly_review import strings as strings_en
from atlas.weekly_review import strings_sv as strings_sv
from atlas.locale_support import ensure_supported_locale


# ---------------------------------------------------------------------------
# Locale dispatch
# ---------------------------------------------------------------------------

def _strings_for_locale(locale: str):
    """Return the strings module for the given locale.

    Calls ensure_supported_locale — sv raises until locale_support.py is updated.
    English strings are returned for locale="en".
    Swedish strings are mapped for future locale="sv".
    """
    ensure_supported_locale(locale)
    if locale == "sv":
        return strings_sv
    return strings_en


def render_weekly_review(result: WeeklyReviewLoadResult, *, locale: str = "en") -> str:
    """Render a full deterministic Weekly Investment Review from loaded inputs.

    Only locale="en" is currently supported. Unsupported locales raise ValueError.
    The CLI does not expose a locale parameter; it always uses the default.
    """
    S = _strings_for_locale(locale)
    lines: list[str] = []

    lines.append(f"# {S.WEEKLY_REVIEW_TITLE}")
    lines.append("")
    lines.append(S.WEEKLY_REVIEW_DISCLAIMER)
    lines.append("")

    lines.extend(_render_input_status(result, S))
    lines.append("")

    if result.warnings:
        lines.extend(_render_warnings(result.warnings, S))
        lines.append("")

    lines.append("---")
    lines.append("")

    lines.extend(_section(S.SECTION_REVIEW_SCOPE, _section1_scope(result, S)))
    lines.extend(_section(S.SECTION_PORTFOLIO_CONTEXT, _section2_portfolio(result)))
    lines.extend(_section(S.SECTION_WATCHLIST_REVIEW, _section3_watchlist(result, S)))
    lines.extend(_section(S.SECTION_COMPANY_REVIEWS_NEEDING_ATTENTION, _section4_attention(result)))
    lines.extend(_section(S.SECTION_PORTFOLIO_FIT_AND_SUITABILITY_NOTES, _section5_suitability(result)))
    lines.extend(_section(S.SECTION_RISK_AND_PRINCIPLE_GUARDRAILS, _section6_guardrails(result, S)))
    lines.extend(_section(S.SECTION_OPEN_DECISIONS, _section7_decisions(result, S)))
    lines.extend(_section(S.SECTION_MISSING_EVIDENCE, _section8_evidence(result, S)))
    lines.extend(_section(S.SECTION_FOLLOW_UP_QUESTIONS, _section9_questions(result, S)))
    lines.extend(_section(S.SECTION_NON_ACTIONS_REASONS_TO_WAIT, _section10_nonactions(result, S)))

    return "\n".join(lines)


def render_weekly_review_skeleton(result: WeeklyReviewLoadResult) -> str:
    """Backward-compatible alias for render_weekly_review."""
    return render_weekly_review(result)


# ---------------------------------------------------------------------------
# Section 1: Review Scope
# ---------------------------------------------------------------------------


def _section1_scope(result: WeeklyReviewLoadResult, S) -> list[str]:
    lines: list[str] = []

    if result.as_of:
        lines.append(f"Review date: {result.as_of}")
    else:
        lines.append("Review date: Not specified")

    lines.append("Input mode: Local files only. No external data, no live pricing.")

    holdings = result.portfolio.all_holdings
    lines.append(
        f"Portfolio: {len(holdings)} holding(s) across "
        f"{len(result.portfolio.accounts)} account(s)"
    )
    lines.append(
        f"Watchlist: {len(result.watchlist.items)} item(s) in '{result.watchlist.name}'"
    )

    optionals: list[str] = []
    if result.profile_available:
        optionals.append("investor profile")
    if result.journal_entry_count:
        optionals.append(f"decision journal ({result.journal_entry_count} entries)")
    if result.company_facts_available:
        optionals.append("company facts")
    if result.financials_available:
        optionals.append("financial history")
    if result.research_notes:
        optionals.append(f"research notes ({len(result.research_notes)} ticker(s))")

    if optionals:
        lines.append(f"Optional inputs loaded: {', '.join(optionals)}")
    else:
        lines.append(
            "Optional inputs: none provided — review uses portfolio and watchlist only"
        )

    if result.scope_notes:
        lines.append(f"Scope notes: {_preview_scope_notes(result.scope_notes)}")

    if result.warnings:
        lines.append(S.WARNING_SCOPE_SUMMARY.format(count=len(result.warnings)))

    return lines


# ---------------------------------------------------------------------------
# Section 2: Portfolio Context
# ---------------------------------------------------------------------------


def _section2_portfolio(result: WeeklyReviewLoadResult) -> list[str]:
    lines: list[str] = []
    holdings = result.portfolio.all_holdings

    for account in result.portfolio.accounts:
        lines.append(f"Account: {account.name} — {len(account.holdings)} holding(s)")

    # Top holdings sorted by weight descending (stable: secondary sort by ticker)
    by_weight = sorted(holdings, key=lambda h: (-h.weight, h.ticker))
    lines.append("")
    lines.append("Holdings by weight (user-supplied values, highest first):")
    for h in by_weight:
        weight_str = f"{h.weight:.1%}" if h.weight > 0 else "weight not specified"
        sector_part = f", {h.sector}" if h.sector else ""
        role_part = f" [{h.role}]" if h.role else ""
        lines.append(f"  {h.ticker} — {h.name}{sector_part}: {weight_str}{role_part}")

    # Sector exposure (exclude cash from concentration check; include all in exposure)
    sector_weights: dict[str, float] = defaultdict(float)
    for h in holdings:
        sector = h.sector or "Unclassified"
        sector_weights[sector] += h.weight

    lines.append("")
    lines.append("Sector exposure:")
    for sector, w in sorted(sector_weights.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"  {sector}: {w:.1%}")

    # Concentration notes — single and combined
    non_cash = [h for h in by_weight if not h.sector or h.sector.lower() != "cash"]
    if non_cash and non_cash[0].weight > 0.25:
        top = non_cash[0]
        lines.append(
            f"Concentration note: {top.ticker} ({top.name}) represents "
            f"{top.weight:.1%} of loaded portfolio value. "
            "Single-position weight exceeds 25% threshold."
        )
    if len(non_cash) >= 2:
        combined = non_cash[0].weight + non_cash[1].weight
        if combined > 0.40:
            lines.append(
                f"Combined concentration: {non_cash[0].ticker} + {non_cash[1].ticker} = "
                f"{combined:.1%} of loaded portfolio value. "
                "Top-2 combined exposure may warrant review."
            )

    # Cash observation
    cash_total = sector_weights.get("Cash", 0.0)
    if cash_total > 0.20:
        lines.append(
            f"Cash position: {cash_total:.1%} of portfolio in cash or cash-equivalent holdings."
        )

    # Holdings with unclassified sector
    unclassified = [h for h in holdings if not h.sector]
    if unclassified:
        tickers = ", ".join(h.ticker for h in unclassified)
        lines.append(f"Unclassified sector: {tickers} — sector not specified in input.")

    lines.append("Note: All values are user-supplied. No live pricing or external data used.")
    return lines


# ---------------------------------------------------------------------------
# Section 3: Watchlist Review
# ---------------------------------------------------------------------------


def _section3_watchlist(result: WeeklyReviewLoadResult, S) -> list[str]:
    lines: list[str] = []

    if not result.watchlist.items:
        lines.append("No watchlist items loaded.")
        return lines

    for item in result.watchlist.items:
        lines.append(f"{item.ticker} — {item.name}: {item.status.value}")
        if item.reason:
            lines.append(f"[{item.ticker}] Reason: {item.reason}")
        for gap in item.evidence_needed:
            lines.append(f"[{item.ticker}] {S.LABEL_EVIDENCE_GAP}: {gap}")
        for q in item.open_questions:
            lines.append(f"[{item.ticker}] Question: {q}")
        for obs in item.manual_observations:
            lines.append(f"[{item.ticker}] Observation: {obs}")
        if item.notes:
            lines.append(f"[{item.ticker}] Notes: {item.notes}")
        lines.append("")

    return lines


# ---------------------------------------------------------------------------
# Section 4: Company Reviews Needing Attention
# ---------------------------------------------------------------------------


def _section4_attention(result: WeeklyReviewLoadResult) -> list[str]:
    lines: list[str] = []
    holdings = result.portfolio.all_holdings
    portfolio_tickers = {h.ticker for h in holdings}
    watchlist_by_ticker = {item.ticker: item for item in result.watchlist.items}

    # Portfolio/watchlist overlap
    overlap = sorted(portfolio_tickers & set(watchlist_by_ticker))
    for ticker in overlap:
        holding = next(h for h in holdings if h.ticker == ticker)
        item = watchlist_by_ticker[ticker]
        lines.append(
            f"{ticker} ({holding.name}): Needs Review — held in portfolio "
            f"({holding.weight:.1%}) and under active watchlist review "
            f"(Status: {item.status.value})"
        )

    # Watchlist items with 2+ evidence gaps
    for item in result.watchlist.items:
        if len(item.evidence_needed) >= 2:
            lines.append(
                f"{item.ticker} ({item.name}): Needs More Evidence — "
                f"{len(item.evidence_needed)} evidence gaps remain open. "
                f"Status: {item.status.value}."
            )

    # Large portfolio holdings (> 20% of loaded value), excluding cash
    for h in sorted(holdings, key=lambda x: -x.weight):
        sector = h.sector or ""
        if h.weight > 0.20 and sector.lower() != "cash":
            lines.append(
                f"{h.ticker} ({h.name}): Visible holding — "
                f"{h.weight:.1%} of loaded portfolio value in {h.sector or 'Unclassified'} sector."
            )

    # Holdings with unclassified or missing sector
    for h in holdings:
        if not h.sector:
            lines.append(
                f"{h.ticker}: Missing Classification — sector not specified in input."
            )

    if not lines:
        lines.append(
            "No items flagged for immediate attention from available local inputs."
        )

    lines.append(
        "Note: All observations are derived from user-supplied local inputs only. "
        "No external data, no engine analysis, no recommendations."
    )
    return lines


# ---------------------------------------------------------------------------
# Section 5: Portfolio Fit and Suitability Notes
# ---------------------------------------------------------------------------


def _section5_suitability(result: WeeklyReviewLoadResult) -> list[str]:
    lines: list[str] = []
    holdings = result.portfolio.all_holdings

    if result.profile_available:
        lines.append("Investor profile: Provided.")
        if result.profile_risk_tolerance:
            lines.append(f"Risk tolerance: {result.profile_risk_tolerance}")
        if result.profile_time_horizon:
            lines.append(f"Time horizon: {result.profile_time_horizon}")
    else:
        lines.append(
            "Investor profile: Not provided. "
            "Suitability observations below are structural only and not personalized."
        )

    # Concentration observations (non-cash)
    by_weight = sorted(holdings, key=lambda h: (-h.weight, h.ticker))
    non_cash = [h for h in by_weight if not h.sector or h.sector.lower() != "cash"]
    if non_cash and non_cash[0].weight > 0.25:
        lines.append(
            f"Concentration observation: {non_cash[0].ticker} represents "
            f"{non_cash[0].weight:.1%} of loaded portfolio value. "
            "Concentration should be reviewed in relation to stated constraints."
        )

    # Cash position
    cash_holdings = [h for h in holdings if h.sector and h.sector.lower() == "cash"]
    if cash_holdings:
        total_cash = sum(h.weight for h in cash_holdings)
        lines.append(
            f"Cash position: {total_cash:.1%} of portfolio. "
            "Review cash level in relation to investment goals."
        )

    # Invested positions count
    invested = [h for h in holdings if not h.sector or h.sector.lower() != "cash"]
    lines.append(f"Invested positions: {len(invested)} (excluding cash holdings).")

    # Sector visibility
    sectors = {h.sector for h in holdings if h.sector and h.sector.lower() != "cash"}
    if len(sectors) == 1:
        lines.append(
            f"Sector concentration: all invested holdings are in {next(iter(sectors))}. "
            "Diversification should be reviewed against stated constraints."
        )

    # Profile constraints
    if result.profile_constraints:
        lines.append("")
        lines.append("Stated constraints (from investor profile):")
        for constraint in result.profile_constraints:
            lines.append(f"  Constraint: {constraint}")

    lines.append(
        "Full suitability evaluation is deferred until engine wiring. "
        "Portfolio fit notes are limited to loaded local structure."
    )
    lines.append(
        "Note: Atlas does not judge investment merit or provide personalized guidance. "
        "Suitability assessment requires manual review."
    )
    return lines


# ---------------------------------------------------------------------------
# Section 6: Risk and Principle Guardrails
# ---------------------------------------------------------------------------


def _section6_guardrails(result: WeeklyReviewLoadResult, S) -> list[str]:
    lines: list[str] = []
    holdings = result.portfolio.all_holdings

    # Profile principles as guardrail reference
    if result.profile_principles:
        lines.append("Stated principles (from investor profile):")
        for principle in result.profile_principles:
            lines.append(f"  Principle: {principle}")
        lines.append("")

    # Holdings with elevated risk score (user-supplied)
    high_risk = [h for h in holdings if h.risk_score > 60]
    if high_risk:
        lines.append("Elevated risk scores (user-supplied, > 60):")
        for h in sorted(high_risk, key=lambda x: -x.risk_score):
            lines.append(f"  {S.LABEL_RISK_TO_MONITOR}: {h.ticker} — risk score {h.risk_score}")

    # Missing cost basis (non-cash holdings)
    no_cost = [
        h for h in holdings
        if h.cost_basis is None and (not h.sector or h.sector.lower() != "cash")
    ]
    if no_cost:
        tickers = ", ".join(h.ticker for h in no_cost)
        lines.append(
            f"Cost basis not provided for: {tickers}. "
            "Performance baseline cannot be computed from available data."
        )

    # Sector concentration check (invested, non-cash)
    sector_weights: dict[str, float] = defaultdict(float)
    for h in holdings:
        sector = h.sector or "Unclassified"
        if sector.lower() != "cash":
            sector_weights[sector] += h.weight
    for sector, w in sorted(sector_weights.items(), key=lambda x: -x[1]):
        if w > 0.35:
            lines.append(
                f"Sector concentration: {sector} represents {w:.1%} of invested holdings. "
                f"{S.LABEL_RISK_TO_MONITOR}: sector exposure may warrant review."
            )

    # Missing optional data
    if not result.company_facts_available:
        lines.append(
            f"{S.LABEL_EVIDENCE_GAP}: Company facts not loaded. "
            "Evidence quality cannot be assessed from available inputs."
        )
    if not result.financials_available:
        lines.append(
            f"{S.LABEL_EVIDENCE_GAP}: Financial history not loaded. "
            "Financial trend analysis not available."
        )

    # Deferred engine wiring note
    lines.append(
        "Risk and principle guardrail engine wiring is deferred to a later sprint."
    )
    lines.append(
        "Principle Guardrail: No action is warranted when evidence is incomplete."
    )

    if not result.profile_principles and not [l for l in lines if "Risk to Monitor" in l or "Evidence Gap" in l]:
        lines.insert(0, "No guardrail flags raised from available local inputs.")

    lines.append(
        "Note: Guardrail checks are based on user-supplied data only. "
        "No live market data or external analysis used."
    )
    return lines


# ---------------------------------------------------------------------------
# Section 7: Open Decisions
# ---------------------------------------------------------------------------


def _section7_decisions(result: WeeklyReviewLoadResult, S) -> list[str]:
    lines: list[str] = []

    if not result.journal_entries:
        if result.journal_entry_count > 0:
            lines.append(
                f"Decision journal: {result.journal_entry_count} entry/entries found. "
                "Journal entries could not be loaded for summary."
            )
        else:
            lines.append("No decision journal provided. Open decisions not reviewed.")
        return lines

    lines.append(f"Decision journal: {len(result.journal_entries)} entry/entries reviewed.")
    lines.append("")

    for entry in result.journal_entries:
        title = (
            entry.get("decision_title")
            or entry.get("asset_or_idea")
            or entry.get("entry_id", "Unknown")
        )
        raw_status = (
            entry.get("atlas_rating")
            or entry.get("decision_type")
            or "Unclassified"
        )
        date = entry.get("decision_date", "")
        date_part = f" ({date})" if date else ""

        lines.append(f"{title}{date_part}: {raw_status}")

        # Aging note
        if result.as_of and _is_journal_entry_open(entry):
            age = _journal_entry_age_days(entry, result.as_of)
            if age is not None and age > 90:
                lines.append(_render_journal_aging_note(entry, age, S))
            # If date is missing on an open entry, note it quietly
            elif age is None and _parse_journal_entry_date(entry) is None:
                lines.append("[Date Missing] No decision date recorded; aging cannot be assessed.")

        triggers = entry.get("follow_up_triggers", [])
        if isinstance(triggers, list):
            for trigger in triggers[:2]:  # show first two triggers
                lines.append(f"[Follow-up] {trigger}")

        atlas_view = entry.get("atlas_view") or entry.get("view") or ""
        if atlas_view and isinstance(atlas_view, str):
            truncated = (atlas_view[:200] + "...") if len(atlas_view) > 200 else atlas_view
            lines.append(f"[View] {truncated}")

        lines.append("")

    return lines


# ---------------------------------------------------------------------------
# Section 8: Missing Evidence
# ---------------------------------------------------------------------------


def _section8_evidence(result: WeeklyReviewLoadResult, S) -> list[str]:
    lines: list[str] = []

    # Watchlist evidence gaps (grouped by ticker)
    for item in result.watchlist.items:
        for gap in item.evidence_needed:
            lines.append(f"{S.LABEL_EVIDENCE_GAP} [{item.ticker}]: {gap}")

    # Per-ticker evidence presence (when directories are available)
    # Combine into one line per ticker when both are missing, to avoid repeating the same ticker twice.
    if result.ticker_evidence:
        for ev in result.ticker_evidence:
            missing_facts = not ev.company_facts_available and result.company_facts_available
            missing_fins = not ev.financials_available and result.financials_available
            if missing_facts and missing_fins:
                lines.append(
                    f"{S.LABEL_EVIDENCE_GAP} [{ev.ticker}]: no local company facts file or financial history file."
                )
            elif missing_facts:
                lines.append(
                    f"{S.LABEL_EVIDENCE_GAP} [{ev.ticker}]: local company facts file is missing."
                )
            elif missing_fins:
                lines.append(
                    f"{S.LABEL_EVIDENCE_GAP} [{ev.ticker}]: local financial history file is missing."
                )

    # Research note evidence gaps
    for note in result.research_notes:
        for gap in note.evidence_gaps:
            lines.append(f"{S.LABEL_EVIDENCE_GAP} [{note.ticker}] (research notes): {gap}")

    # Missing optional inputs
    if not result.profile_available:
        lines.append(f"{S.LABEL_MISSING_OPTIONAL_INPUT}: Investor profile not provided.")
    if result.journal_entry_count == 0 and not result.journal_entries:
        lines.append(f"{S.LABEL_MISSING_OPTIONAL_INPUT}: Decision journal not provided.")
    if not result.company_facts_available:
        lines.append(f"{S.LABEL_MISSING_OPTIONAL_INPUT}: Company facts directory not provided.")
    if not result.financials_available:
        lines.append(f"{S.LABEL_MISSING_OPTIONAL_INPUT}: Financial history directory not provided.")

    # Holdings with missing sector
    for h in result.portfolio.all_holdings:
        if not h.sector:
            lines.append(f"Missing Classification: {h.ticker} — sector not specified.")

    if not lines:
        lines.append("No evidence gaps identified from available local inputs.")

    return lines


# ---------------------------------------------------------------------------
# Section 9: Follow-Up Questions
# ---------------------------------------------------------------------------


def _section9_questions(result: WeeklyReviewLoadResult, S) -> list[str]:
    lines: list[str] = []

    # Watchlist open questions
    for item in result.watchlist.items:
        if item.open_questions:
            lines.append(f"[{item.ticker}] Open questions:")
            for q in item.open_questions:
                lines.append(f"  - {q}")
            lines.append("")

    # Follow-up triggers from journal (second trigger onward)
    if result.journal_entries:
        for entry in result.journal_entries:
            triggers = entry.get("follow_up_triggers", [])
            if isinstance(triggers, list) and len(triggers) > 2:
                asset = (
                    entry.get("asset_or_idea")
                    or entry.get("decision_title", "Unknown")
                )
                lines.append(f"[{asset}] Additional follow-up triggers:")
                for trigger in triggers[2:]:
                    lines.append(f"  - {trigger}")
                lines.append("")

    # Per-ticker missing evidence — grouped summary rather than one line per ticker
    if result.ticker_evidence:
        missing_facts_tickers = [
            ev.ticker for ev in result.ticker_evidence
            if not ev.company_facts_available and result.company_facts_available
        ]
        if missing_facts_tickers:
            lines.append(
                f"Tickers without local company facts ({len(missing_facts_tickers)}): "
                f"{', '.join(missing_facts_tickers)}"
            )
        missing_fins_tickers = [
            ev.ticker for ev in result.ticker_evidence
            if not ev.financials_available and result.financials_available
        ]
        if missing_fins_tickers:
            lines.append(
                f"Tickers without local financial history ({len(missing_fins_tickers)}): "
                f"{', '.join(missing_fins_tickers)}"
            )

    # Research note open questions and risks
    for note in result.research_notes:
        if note.open_questions:
            lines.append(f"[{note.ticker}] Research notes — open questions:")
            for q in note.open_questions:
                lines.append(f"  - {q}")
            lines.append("")
        if note.risks_to_monitor:
            for risk in note.risks_to_monitor:
                lines.append(f"[{note.ticker}] {S.LABEL_RISK_TO_MONITOR} (research notes): {risk}")

    # General questions when evidence directories are absent
    if not result.company_facts_available:
        lines.append(
            "What company facts are needed before changing the status of any watchlist item?"
        )
    if not result.financials_available:
        lines.append(
            "Which financial trends should be reviewed before any watchlist decision changes?"
        )

    # Evidence gap prompts
    all_gaps = [
        (item.ticker, gap)
        for item in result.watchlist.items
        for gap in item.evidence_needed
    ]
    if all_gaps:
        lines.append(
            "What evidence would confirm or weaken the current assumptions for each open watchlist item?"
        )

    if not lines:
        lines.append(
            "No follow-up questions identified. "
            "Add open_questions to watchlist items to surface them here."
        )

    return lines


# ---------------------------------------------------------------------------
# Section 10: Non-Actions / Reasons to Wait
# ---------------------------------------------------------------------------


def _section10_nonactions(result: WeeklyReviewLoadResult, S) -> list[str]:
    lines: list[str] = []

    # Deferred and needs-more-evidence watchlist items
    deferred_statuses = {
        WeeklyReviewWatchlistStatus.DECISION_DEFERRED,
        WeeklyReviewWatchlistStatus.NEEDS_MORE_EVIDENCE,
    }
    deferred = [i for i in result.watchlist.items if i.status in deferred_statuses]
    for item in deferred:
        lines.append(
            f"{S.LABEL_DECISION_DEFERRED}: {item.ticker} — {item.name}. "
            f"Status: {item.status.value}."
        )

    # Evidence gaps as reason to wait
    all_gap_count = sum(len(i.evidence_needed) for i in result.watchlist.items)
    if all_gap_count > 0:
        lines.append(
            f"{S.LABEL_REASON_TO_WAIT}: {all_gap_count} evidence gap(s) identified across "
            "watchlist items. Gathering evidence is the appropriate next step."
        )

    # Missing optional inputs as reasons to wait
    if not result.profile_available:
        lines.append(
            f"{S.LABEL_REASON_TO_WAIT}: Investor profile not provided. "
            "Structural suitability assessment is deferred."
        )
    if result.journal_entry_count == 0 and not result.journal_entries:
        lines.append(
            f"{S.LABEL_REASON_TO_WAIT}: Decision journal not provided. "
            "Open decisions and prior context are not available for this review."
        )
    # Per-ticker missing evidence — two summary lines instead of one per ticker
    if result.ticker_evidence:
        missing_facts = [
            ev.ticker for ev in result.ticker_evidence
            if not ev.company_facts_available and result.company_facts_available
        ]
        if missing_facts:
            lines.append(
                f"{S.LABEL_REASON_TO_WAIT}: Local company facts missing for {len(missing_facts)} ticker(s) "
                f"({', '.join(missing_facts)}): thesis context is incomplete for these positions."
            )
        missing_fins = [
            ev.ticker for ev in result.ticker_evidence
            if not ev.financials_available and result.financials_available
        ]
        if missing_fins:
            lines.append(
                f"{S.LABEL_REASON_TO_WAIT}: Local financial history missing for {len(missing_fins)} ticker(s) "
                f"({', '.join(missing_fins)}): financial context is incomplete for these positions."
            )

    # General reasons to wait when evidence directories are absent
    if not result.company_facts_available:
        lines.append(
            f"{S.LABEL_REASON_TO_WAIT}: Company facts not loaded. "
            "Decision-relevant evidence is incomplete."
        )
    if not result.financials_available:
        lines.append(
            f"{S.LABEL_REASON_TO_WAIT}: Financial history not loaded. "
            "Financial trend analysis is not available."
        )

    # Aged journal entries as reasons to wait
    if result.journal_entries and result.as_of:
        aged = [
            entry for entry in result.journal_entries
            if _is_journal_entry_open(entry)
            and (_journal_entry_age_days(entry, result.as_of) or 0) > 90
        ]
        for entry in aged:
            asset = (
                entry.get("asset_or_idea")
                or entry.get("decision_title", "Unknown")
            )
            age = _journal_entry_age_days(entry, result.as_of)
            lines.append(
                f"{S.LABEL_REASON_TO_WAIT}: {asset} decision journal notes are older than 90 days "
                f"({age} days). Assumptions should be refreshed before changing decision status."
            )

    # Research note reasons to wait
    notes_with_gaps = [n for n in result.research_notes if n.evidence_gaps or n.reasons_to_wait]
    for note in notes_with_gaps:
        if note.reasons_to_wait:
            for r in note.reasons_to_wait:
                lines.append(f"{S.LABEL_REASON_TO_WAIT} [{note.ticker}] (research notes): {r}")
        elif note.evidence_gaps:
            lines.append(
                f"{S.LABEL_REASON_TO_WAIT}: {note.ticker} research notes contain "
                f"{len(note.evidence_gaps)} unresolved evidence gap(s). "
                "Gathering evidence is the appropriate next step."
            )

    # Profile-derived reasons — grouped blocks to avoid N identical boilerplate lines
    if result.profile_principles:
        lines.append(
            f"{S.LABEL_REASON_TO_WAIT}: Stated principles support a measured approach to evidence and decision discipline:"
        )
        for principle in result.profile_principles:
            lines.append(f'  — "{principle}"')
    if result.profile_constraints:
        lines.append(
            f"{S.LABEL_NO_ACTION_WARRANTED}: Stated constraints apply to current portfolio and watchlist decisions:"
        )
        for constraint in result.profile_constraints:
            lines.append(f'  — "{constraint}"')

    # Universal reminders — always ensure section is non-empty
    lines.append(
        f"{S.LABEL_NO_ACTION_WARRANTED}: This review is informational only. "
        "All observations are based on user-supplied local inputs."
    )
    lines.append(S.REMINDER_NO_ACTION_VALID)
    lines.append(S.REMINDER_ATLAS_SUPPORTS_JUDGMENT)

    return lines


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Journal aging helpers
# ---------------------------------------------------------------------------

# Date fields checked in this priority order (first valid field wins).
_JOURNAL_DATE_FIELDS = ("decision_date", "date", "created_at", "created", "timestamp", "review_date")

# Status fields checked in priority order for open/closed classification.
_JOURNAL_STATUS_FIELDS = ("atlas_rating", "decision_type", "status", "decision_status", "state")

# Statuses that are clearly closed — aged alerts are suppressed for these.
_CLOSED_STATUSES = frozenset({"closed", "archived", "completed", "resolved"})


def _parse_journal_entry_date(entry: dict) -> datetime.date | None:
    """Return the first parseable date from known date fields, or None."""
    for field in _JOURNAL_DATE_FIELDS:
        raw = entry.get(field)
        if not raw or not isinstance(raw, str):
            continue
        try:
            return datetime.date.fromisoformat(raw[:10])
        except ValueError:
            continue
    return None


def _is_journal_entry_open(entry: dict) -> bool:
    """Return True if the entry status is not a clearly closed/resolved status."""
    for field in _JOURNAL_STATUS_FIELDS:
        raw = entry.get(field)
        if raw and isinstance(raw, str):
            if raw.strip().lower() in _CLOSED_STATUSES:
                return False
            return True  # has a status that is not closed → treat as open
    return True  # no status field found → treat as unresolved


def _journal_entry_age_days(entry: dict, as_of: str) -> int | None:
    """Return age in calendar days from entry date to as_of, or None if unavailable."""
    entry_date = _parse_journal_entry_date(entry)
    if entry_date is None:
        return None
    try:
        review_date = datetime.date.fromisoformat(as_of[:10])
    except ValueError:
        return None
    delta = (review_date - entry_date).days
    return delta if delta >= 0 else None


def _is_aged_journal_entry(entry: dict, as_of: str, threshold_days: int = 90) -> bool:
    """Return True when entry is open and older than threshold_days (strictly greater)."""
    if not _is_journal_entry_open(entry):
        return False
    age = _journal_entry_age_days(entry, as_of)
    return age is not None and age > threshold_days


def _render_journal_aging_note(entry: dict, age_days: int, S) -> str:
    """Return a safe aging note line for a journal entry."""
    asset = entry.get("asset_or_idea") or entry.get("decision_title", "Unknown")
    return (
        f"[{S.LABEL_AGING_NOTE}] {asset}: Review date is older than 90 days ({age_days} days). "
        "Thesis assumptions may need to be rechecked."
    )


def _preview_scope_notes(scope_notes: str) -> str:
    """Return a compact preview of scope notes, stripping markdown syntax."""
    if not scope_notes:
        return ""
    raw_lines = scope_notes.splitlines()
    # Strip markdown headers and formatting; collect substantive lines
    substantive: list[str] = []
    for line in raw_lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue  # skip markdown headers
        # Strip basic inline markdown
        cleaned = stripped.replace("**", "").replace("*", "").replace("`", "")
        if cleaned:
            substantive.append(cleaned)
    if not substantive:
        return scope_notes[:200]
    preview = " | ".join(substantive[:4])
    if len(preview) > 300:
        preview = preview[:297] + "..."
    total = len([l for l in raw_lines if l.strip()])
    if total > 4:
        preview += f" [{total} lines]"
    return preview


def _section(heading: str, content: list[str]) -> list[str]:
    out = [f"## {heading}", ""]
    for line in content:
        if line:
            out.append(f"- {line}")
        else:
            out.append("")
    out.append("")
    return out


def _render_input_status(result: WeeklyReviewLoadResult, S) -> list[str]:
    lines = [f"## {S.LABEL_INPUT_STATUS}", ""]
    lines.append(f"- {S.INPUT_STATUS_PORTFOLIO_LOADED.format(count=len(result.portfolio.all_holdings))}")
    lines.append(
        f"- {S.INPUT_STATUS_WATCHLIST_LOADED.format(count=len(result.watchlist.items), name=result.watchlist.name)}"
    )
    lines.append(
        f"- {S.INPUT_STATUS_INVESTOR_PROFILE_AVAILABLE if result.profile_available else S.INPUT_STATUS_INVESTOR_PROFILE_NOT_PROVIDED}",
    )
    lines.append(
        f"- "
        + (
            S.INPUT_STATUS_JOURNAL_LOADED.format(count=result.journal_entry_count)
            if result.journal_entry_count
            else S.INPUT_STATUS_JOURNAL_NOT_PROVIDED
        )
    )
    lines.append(
        f"- {S.INPUT_STATUS_COMPANY_FACTS_AVAILABLE if result.company_facts_available else S.INPUT_STATUS_COMPANY_FACTS_NOT_PROVIDED}",
    )
    lines.append(
        f"- {S.INPUT_STATUS_FINANCIALS_AVAILABLE if result.financials_available else S.INPUT_STATUS_FINANCIALS_NOT_PROVIDED}",
    )
    if result.research_notes:
        lines.append(f"- {S.INPUT_STATUS_RESEARCH_NOTES_LOADED.format(count=len(result.research_notes))}")
    else:
        lines.append(f"- {S.INPUT_STATUS_RESEARCH_NOTES_NOT_PROVIDED}")
    if result.as_of:
        lines.append(f"- {S.INPUT_STATUS_REVIEW_DATE.format(date=result.as_of)}")
    if result.warnings:
        lines.append(f"- {S.INPUT_STATUS_WARNINGS_COUNT.format(count=len(result.warnings))}")
    return lines


def _render_warnings(warnings: tuple[WeeklyReviewInputWarning, ...], S) -> list[str]:
    lines = [f"## {S.LABEL_INPUT_WARNINGS}", ""]
    for w in warnings:
        lines.append(S.WARNING_ROW.format(code=w.code, message=w.message))
    return lines

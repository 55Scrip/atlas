"""Sprint 214 — Journal entry aging alert tests.

Coverage:
- entry older than 90 days → aging note in Section 7
- entry older than 90 days → reason-to-wait in Section 10
- entry exactly 90 days old → NOT flagged (strictly > 90)
- entry younger than 90 days → not flagged
- missing journal date → does not fail rendering
- invalid journal date → does not fail rendering
- closed/resolved entries → not flagged
- unknown status → treated as unresolved, flagged if aged
- age calculation uses as_of deterministically
- forbidden language absent
- no provider/network imports
- date-field priority order
- status-field priority order
"""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest

from atlas.weekly_review.render import (
    _is_aged_journal_entry,
    _is_journal_entry_open,
    _journal_entry_age_days,
    _parse_journal_entry_date,
    _render_journal_aging_note,
    render_weekly_review,
)
from atlas.weekly_review import (
    WeeklyReviewInputPaths,
    WeeklyReviewLoadResult,
    load_weekly_review_inputs,
)

REALISTIC = Path(__file__).parent.parent / "examples" / "weekly_review_realistic"

FORBIDDEN_TERMS = [
    "buy", "sell", "strong buy", "strong sell", "price target", "target price",
    "urgent", "act now", "must buy", "must sell", "guaranteed", "will outperform",
    "financial advice",
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_entry(
    decision_date: str | None = None,
    date: str | None = None,
    created_at: str | None = None,
    status: str | None = None,
    atlas_rating: str | None = None,
    decision_type: str | None = None,
    asset: str = "TESTCO",
    title: str = "TESTCO — review",
) -> dict:
    e: dict = {"asset_or_idea": asset, "decision_title": title}
    if decision_date is not None:
        e["decision_date"] = decision_date
    if date is not None:
        e["date"] = date
    if created_at is not None:
        e["created_at"] = created_at
    if status is not None:
        e["status"] = status
    if atlas_rating is not None:
        e["atlas_rating"] = atlas_rating
    if decision_type is not None:
        e["decision_type"] = decision_type
    return e


def _result_with_entries(
    entries: list[dict],
    as_of: str = "2026-01-01",
) -> WeeklyReviewLoadResult:
    """Build a minimal WeeklyReviewLoadResult with given journal entries."""
    paths = WeeklyReviewInputPaths(
        portfolio_path=REALISTIC / "portfolio.json",
        watchlist_path=REALISTIC / "watchlist.json",
        as_of=as_of,
    )
    base = load_weekly_review_inputs(paths)
    # Rebuild with custom journal_entries
    return WeeklyReviewLoadResult(
        portfolio=base.portfolio,
        watchlist=base.watchlist,
        profile_available=False,
        journal_entry_count=len(entries),
        company_facts_available=False,
        financials_available=False,
        as_of=as_of,
        scope_notes="",
        journal_entries=tuple(entries),
        warnings=base.warnings,
    )


# ---------------------------------------------------------------------------
# _parse_journal_entry_date — date field priority
# ---------------------------------------------------------------------------


def test_parse_date_from_decision_date():
    entry = _make_entry(decision_date="2025-06-15", date="2025-01-01")
    assert _parse_journal_entry_date(entry) == datetime.date(2025, 6, 15)


def test_parse_date_falls_back_to_date_field():
    entry = _make_entry(date="2025-06-15")
    assert _parse_journal_entry_date(entry) == datetime.date(2025, 6, 15)


def test_parse_date_falls_back_to_created_at():
    entry = _make_entry(created_at="2025-06-15")
    assert _parse_journal_entry_date(entry) == datetime.date(2025, 6, 15)


def test_parse_date_returns_none_when_no_date():
    entry = _make_entry()
    assert _parse_journal_entry_date(entry) is None


def test_parse_date_returns_none_for_invalid_date():
    entry = _make_entry(decision_date="not-a-date")
    assert _parse_journal_entry_date(entry) is None


def test_parse_date_handles_datetime_prefix():
    entry = _make_entry(decision_date="2025-06-15T10:00:00")
    assert _parse_journal_entry_date(entry) == datetime.date(2025, 6, 15)


def test_parse_date_ignores_non_string_values():
    entry = {"decision_date": 20250615}
    assert _parse_journal_entry_date(entry) is None


# ---------------------------------------------------------------------------
# _is_journal_entry_open — status filtering
# ---------------------------------------------------------------------------


def test_open_entry_with_continue_research():
    assert _is_journal_entry_open(_make_entry(atlas_rating="Continue Research"))


def test_open_entry_with_needs_more_evidence():
    assert _is_journal_entry_open(_make_entry(atlas_rating="Needs More Evidence"))


def test_open_entry_with_decision_deferred():
    assert _is_journal_entry_open(_make_entry(atlas_rating="Decision Deferred"))


def test_open_entry_with_no_action_warranted():
    assert _is_journal_entry_open(_make_entry(atlas_rating="No Action Warranted"))


def test_closed_entry_closed_status():
    assert not _is_journal_entry_open(_make_entry(atlas_rating="Closed"))


def test_closed_entry_archived():
    assert not _is_journal_entry_open(_make_entry(atlas_rating="Archived"))


def test_closed_entry_completed():
    assert not _is_journal_entry_open(_make_entry(decision_type="Completed"))


def test_closed_entry_resolved():
    assert not _is_journal_entry_open(_make_entry(status="Resolved"))


def test_closed_case_insensitive():
    assert not _is_journal_entry_open({"atlas_rating": "CLOSED"})


def test_unknown_status_treated_as_open():
    assert _is_journal_entry_open(_make_entry(atlas_rating="Some Unknown Status"))


def test_no_status_treated_as_open():
    entry = {"asset_or_idea": "TESTCO"}
    assert _is_journal_entry_open(entry)


def test_status_field_priority_atlas_rating_over_status():
    # atlas_rating is "Closed" but status says "Needs More Evidence"
    entry = _make_entry(atlas_rating="Closed", status="Needs More Evidence")
    assert not _is_journal_entry_open(entry)


# ---------------------------------------------------------------------------
# _journal_entry_age_days
# ---------------------------------------------------------------------------


def test_age_91_days():
    entry = _make_entry(decision_date="2025-10-02")
    assert _journal_entry_age_days(entry, "2026-01-01") == 91


def test_age_90_days_exactly():
    entry = _make_entry(decision_date="2025-10-03")
    assert _journal_entry_age_days(entry, "2026-01-01") == 90


def test_age_0_days_same_date():
    entry = _make_entry(decision_date="2026-01-01")
    assert _journal_entry_age_days(entry, "2026-01-01") == 0


def test_age_returns_none_for_missing_date():
    entry = _make_entry()
    assert _journal_entry_age_days(entry, "2026-01-01") is None


def test_age_returns_none_for_invalid_date():
    entry = _make_entry(decision_date="bad-date")
    assert _journal_entry_age_days(entry, "2026-01-01") is None


def test_age_returns_none_for_invalid_as_of():
    entry = _make_entry(decision_date="2025-10-01")
    assert _journal_entry_age_days(entry, "not-a-date") is None


def test_age_returns_none_for_future_entry():
    entry = _make_entry(decision_date="2026-06-01")
    result = _journal_entry_age_days(entry, "2026-01-01")
    assert result is None  # future entries have negative delta, should return None


# ---------------------------------------------------------------------------
# _is_aged_journal_entry — boundary condition
# ---------------------------------------------------------------------------


def test_aged_entry_91_days():
    entry = _make_entry(decision_date="2025-10-02", atlas_rating="Needs More Evidence")
    assert _is_aged_journal_entry(entry, "2026-01-01")


def test_not_aged_entry_exactly_90_days():
    entry = _make_entry(decision_date="2025-10-03", atlas_rating="Needs More Evidence")
    assert not _is_aged_journal_entry(entry, "2026-01-01")


def test_not_aged_entry_89_days():
    entry = _make_entry(decision_date="2025-10-04", atlas_rating="Needs More Evidence")
    assert not _is_aged_journal_entry(entry, "2026-01-01")


def test_closed_entry_not_aged_even_if_old():
    entry = _make_entry(decision_date="2020-01-01", atlas_rating="Closed")
    assert not _is_aged_journal_entry(entry, "2026-01-01")


def test_missing_date_not_aged():
    entry = _make_entry(atlas_rating="Needs More Evidence")
    assert not _is_aged_journal_entry(entry, "2026-01-01")


def test_no_as_of_uses_default_threshold():
    entry = _make_entry(decision_date="2024-01-01", atlas_rating="Needs More Evidence")
    assert _is_aged_journal_entry(entry, "2026-01-01", threshold_days=90)


# ---------------------------------------------------------------------------
# _render_journal_aging_note
# ---------------------------------------------------------------------------


def test_aging_note_contains_asset():
    from atlas.weekly_review import strings as S
    entry = _make_entry(asset="XYL")
    note = _render_journal_aging_note(entry, 108, S)
    assert "XYL" in note


def test_aging_note_contains_age_days():
    from atlas.weekly_review import strings as S
    entry = _make_entry(asset="XYL")
    note = _render_journal_aging_note(entry, 108, S)
    assert "108" in note


def test_aging_note_contains_aging_note_label():
    from atlas.weekly_review import strings as S
    entry = _make_entry(asset="XYL")
    note = _render_journal_aging_note(entry, 108, S)
    assert "Aging Note" in note


def test_aging_note_no_forbidden_language():
    from atlas.weekly_review import strings as S
    entry = _make_entry(asset="XYL")
    note = _render_journal_aging_note(entry, 108, S).lower()
    for term in FORBIDDEN_TERMS:
        assert term not in note, f"Forbidden term {term!r} in aging note"


# ---------------------------------------------------------------------------
# Section 7 renderer integration
# ---------------------------------------------------------------------------


def test_section7_aged_entry_has_aging_note():
    entries = [_make_entry(decision_date="2024-06-01", atlas_rating="Needs More Evidence", asset="OLDCO")]
    result = _result_with_entries(entries, as_of="2026-01-01")
    output = render_weekly_review(result)
    assert "Aging Note" in output
    assert "OLDCO" in output


def test_section7_young_entry_no_aging_note():
    entries = [_make_entry(decision_date="2025-12-01", atlas_rating="Needs More Evidence", asset="NEWCO")]
    result = _result_with_entries(entries, as_of="2026-01-01")
    output = render_weekly_review(result)
    # NEWCO is 31 days old — should not have aging note
    assert "Aging Note" not in output


def test_section7_exactly_90_days_not_flagged():
    entry_date = (datetime.date(2026, 1, 1) - datetime.timedelta(days=90)).isoformat()
    entries = [_make_entry(decision_date=entry_date, atlas_rating="Needs More Evidence", asset="BOUNDCO")]
    result = _result_with_entries(entries, as_of="2026-01-01")
    output = render_weekly_review(result)
    assert "Aging Note" not in output


def test_section7_closed_entry_not_flagged():
    entries = [_make_entry(decision_date="2020-01-01", atlas_rating="Closed", asset="OLDCO")]
    result = _result_with_entries(entries, as_of="2026-01-01")
    output = render_weekly_review(result)
    assert "Aging Note" not in output


def test_section7_missing_date_renders_date_missing_note():
    entries = [_make_entry(atlas_rating="Needs More Evidence", asset="NODATECO")]
    result = _result_with_entries(entries, as_of="2026-01-01")
    output = render_weekly_review(result)
    assert "Date Missing" in output


def test_section7_missing_date_does_not_fail():
    entries = [_make_entry(atlas_rating="Needs More Evidence")]
    result = _result_with_entries(entries, as_of="2026-01-01")
    output = render_weekly_review(result)
    assert "7. Open Decisions" in output


def test_section7_invalid_date_does_not_fail():
    entries = [_make_entry(decision_date="not-a-date", atlas_rating="Needs More Evidence")]
    result = _result_with_entries(entries, as_of="2026-01-01")
    output = render_weekly_review(result)
    assert "7. Open Decisions" in output


def test_section7_no_as_of_no_aging_note():
    entries = [_make_entry(decision_date="2020-01-01", atlas_rating="Needs More Evidence", asset="OLDCO")]
    result = _result_with_entries(entries, as_of="")
    output = render_weekly_review(result)
    assert "Aging Note" not in output


def test_section7_unknown_status_aged_is_flagged():
    entries = [_make_entry(decision_date="2024-01-01", atlas_rating="Some Unknown Status", asset="MYSTCO")]
    result = _result_with_entries(entries, as_of="2026-01-01")
    output = render_weekly_review(result)
    assert "Aging Note" in output
    assert "MYSTCO" in output


# ---------------------------------------------------------------------------
# Section 10 renderer integration
# ---------------------------------------------------------------------------


def test_section10_aged_entry_creates_reason_to_wait():
    entries = [_make_entry(decision_date="2024-06-01", atlas_rating="Needs More Evidence", asset="OLDCO")]
    result = _result_with_entries(entries, as_of="2026-01-01")
    output = render_weekly_review(result)
    idx = output.index("10. Non-Actions / Reasons to Wait")
    tail = output[idx:]
    assert "Reason to Wait" in tail
    assert "OLDCO" in tail
    assert "older than 90 days" in tail


def test_section10_young_entry_no_aging_reason_to_wait():
    entries = [_make_entry(decision_date="2025-12-01", atlas_rating="Needs More Evidence", asset="NEWCO")]
    result = _result_with_entries(entries, as_of="2026-01-01")
    output = render_weekly_review(result)
    assert "older than 90 days" not in output


def test_section10_closed_entry_no_aging_reason_to_wait():
    entries = [_make_entry(decision_date="2020-01-01", atlas_rating="Closed", asset="CLOSEDCO")]
    result = _result_with_entries(entries, as_of="2026-01-01")
    output = render_weekly_review(result)
    assert "older than 90 days" not in output


def test_section10_aging_no_forbidden_language():
    entries = [_make_entry(decision_date="2024-01-01", atlas_rating="Needs More Evidence", asset="OLDCO")]
    result = _result_with_entries(entries, as_of="2026-01-01")
    output = render_weekly_review(result).lower()
    for term in FORBIDDEN_TERMS:
        assert term not in output, f"Forbidden term {term!r} in output"


# ---------------------------------------------------------------------------
# Realistic bundle integration with aging
# ---------------------------------------------------------------------------


def test_realistic_neste_aged_with_2026_01_03():
    """NESTE entry is from 2024-09-15 — 475 days before 2026-01-03. Should be flagged."""
    scope_notes_text = (REALISTIC / "scope_notes.md").read_text(encoding="utf-8")
    paths = WeeklyReviewInputPaths(
        portfolio_path=REALISTIC / "portfolio.json",
        watchlist_path=REALISTIC / "watchlist.json",
        profile_path=REALISTIC / "investor_profile.json",
        journal_path=REALISTIC / "decision_journal.json",
        company_facts_dir=REALISTIC / "company_facts",
        financials_dir=REALISTIC / "financials",
        as_of="2026-01-03",
        scope_notes=scope_notes_text,
    )
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review(result)
    assert "Aging Note" in output
    assert "NESTE" in output


def test_realistic_lvmh_not_aged_with_2026_01_03():
    """LVMH entry is from 2025-10-20 — 75 days before 2026-01-03. Should NOT be flagged."""
    paths = WeeklyReviewInputPaths(
        portfolio_path=REALISTIC / "portfolio.json",
        watchlist_path=REALISTIC / "watchlist.json",
        journal_path=REALISTIC / "decision_journal.json",
        as_of="2026-01-03",
    )
    result = load_weekly_review_inputs(paths)
    # LVMH is in the journal — check its entry is not shown as aged
    output = render_weekly_review(result)
    # The aging note for LVMH should not appear (75 days < 90)
    # We check by finding "LVMH" context near "Aging Note"
    lines = output.splitlines()
    aging_lines = [l for l in lines if "Aging Note" in l]
    assert not any("LVMH" in l for l in aging_lines)


def test_realistic_no_forbidden_language_with_aging():
    paths = WeeklyReviewInputPaths(
        portfolio_path=REALISTIC / "portfolio.json",
        watchlist_path=REALISTIC / "watchlist.json",
        journal_path=REALISTIC / "decision_journal.json",
        as_of="2026-01-03",
    )
    result = load_weekly_review_inputs(paths)
    output = render_weekly_review(result).lower()
    for term in FORBIDDEN_TERMS:
        assert term not in output, f"Forbidden term {term!r} in output"


def test_realistic_output_deterministic_with_aging():
    paths = WeeklyReviewInputPaths(
        portfolio_path=REALISTIC / "portfolio.json",
        watchlist_path=REALISTIC / "watchlist.json",
        journal_path=REALISTIC / "decision_journal.json",
        as_of="2026-01-03",
    )
    result = load_weekly_review_inputs(paths)
    assert render_weekly_review(result) == render_weekly_review(result)


# ---------------------------------------------------------------------------
# Determinism — as_of controls aging
# ---------------------------------------------------------------------------


def test_deterministic_aging_with_as_of():
    entry = _make_entry(decision_date="2025-01-01", atlas_rating="Needs More Evidence", asset="DETCO")
    r1 = _result_with_entries([entry], as_of="2026-06-01")
    r2 = _result_with_entries([entry], as_of="2026-06-01")
    assert render_weekly_review(r1) == render_weekly_review(r2)


def test_different_as_of_different_aging():
    entry = _make_entry(decision_date="2025-10-15", atlas_rating="Needs More Evidence", asset="DIFFCO")
    r_early = _result_with_entries([entry], as_of="2026-01-01")  # 78 days → not aged
    r_late = _result_with_entries([entry], as_of="2026-06-01")   # 229 days → aged
    out_early = render_weekly_review(r_early)
    out_late = render_weekly_review(r_late)
    assert "Aging Note" not in out_early
    assert "Aging Note" in out_late


# ---------------------------------------------------------------------------
# Provider/network boundary
# ---------------------------------------------------------------------------


def test_render_module_no_provider_imports_sprint214():
    import atlas.weekly_review.render as m
    source = Path(m.__file__).read_text(encoding="utf-8")
    for term in ["atlas.providers", "import requests", "import urllib", "import httpx", "import aiohttp"]:
        assert term not in source

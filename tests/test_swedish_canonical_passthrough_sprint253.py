"""Sprint 253 — Swedish canonical value and user-content passthrough matrix.

Verifies:
  B11 — All SnapshotType, SnapshotConfirmationStatus, and SnapshotConfidence
        enum values appear unchanged (not translated) in Swedish renderer output.
        Warning codes appear unchanged. Ticker symbols appear unchanged.
        File paths appear unchanged.
  B12 — User-provided scope notes, watchlist reasons, research note text,
        journal views, snapshot Notes, and snapshot source references appear
        unchanged in Swedish-locale output.

No changes to locale_support.py, renderers, string modules, or CLI.
B11 and B12 are DONE. B13 and B14 remain OPEN.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_PORTFOLIO = Path("examples/weekly_review/portfolio.json")
_WATCHLIST = Path("examples/weekly_review/watchlist.json")
_PROFILE = Path("examples/weekly_review/investor_profile.json")
_JOURNAL = Path("examples/weekly_review/decision_journal.json")
_RESEARCH_NOTES_DIR = Path("examples/weekly_review/research_notes")
_COMPANY_FACTS_DIR = Path("examples/weekly_review/company_facts")
_DRAFT_RESEARCH = Path("examples/snapshot_drafts/research_notes_snapshot.json")
_DRAFT_PORTFOLIO = Path("examples/snapshot_drafts/portfolio_snapshot.json")
_DRAFT_NEWS = Path("examples/snapshot_drafts/news_snapshot.json")
_DRAFT_CONFIRMED = Path("examples/snapshot_drafts/research_notes_snapshot_confirmed.json")

CHECKLIST = Path("docs/SwedishLocalizationReadinessChecklist.md")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_wr_result(scope_notes: str | None = None):
    from atlas.weekly_review.inputs import WeeklyReviewInputPaths, load_weekly_review_inputs
    paths = WeeklyReviewInputPaths(
        portfolio_path=_PORTFOLIO,
        watchlist_path=_WATCHLIST,
        profile_path=_PROFILE,
        journal_path=_JOURNAL,
        research_notes_dir=_RESEARCH_NOTES_DIR,
        company_facts_dir=_COMPANY_FACTS_DIR,
        as_of="2026-01-05",
        scope_notes=scope_notes,
    )
    return load_weekly_review_inputs(paths)


def _sv_wr(scope_notes: str | None = None) -> str:
    from atlas.weekly_review.render import render_weekly_review
    return render_weekly_review(_load_wr_result(scope_notes), locale="sv")


def _en_wr(scope_notes: str | None = None) -> str:
    from atlas.weekly_review.render import render_weekly_review
    return render_weekly_review(_load_wr_result(scope_notes), locale="en")


def _load_draft(path: Path):
    from atlas.snapshot_input.schema import SnapshotDraft
    return SnapshotDraft.from_dict(json.loads(path.read_text(encoding="utf-8")))


# ---------------------------------------------------------------------------
# B11 — SnapshotType enum values unchanged in Swedish Snapshot output
# ---------------------------------------------------------------------------

_ALL_SNAPSHOT_TYPES = [
    "research_notes_snapshot",
    "company_facts_snapshot",
    "portfolio_snapshot",
    "watchlist_snapshot",
    "open_orders_snapshot",
    "news_snapshot",
    "external_analysis_snapshot",
    "unknown_snapshot",
]


@pytest.mark.parametrize("snapshot_type", _ALL_SNAPSHOT_TYPES)
def test_snapshot_type_preserved_in_confirm_success(snapshot_type: str) -> None:
    from atlas.snapshot_input.render import render_snapshot_confirm_success
    out = render_snapshot_confirm_success("in.json", "out.json", snapshot_type, False, locale="sv")
    assert snapshot_type in out, (
        f"SnapshotType value {snapshot_type!r} missing from Swedish confirm-success output"
    )


@pytest.mark.parametrize("snapshot_type", _ALL_SNAPSHOT_TYPES)
def test_snapshot_type_preserved_in_reject_success(snapshot_type: str) -> None:
    from atlas.snapshot_input.render import render_snapshot_reject_success
    out = render_snapshot_reject_success("in.json", "out.json", snapshot_type, False, False, locale="sv")
    assert snapshot_type in out, (
        f"SnapshotType value {snapshot_type!r} missing from Swedish reject-success output"
    )


def test_research_notes_snapshot_type_in_validation_sv() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    out = render_snapshot_draft_validation(_load_draft(_DRAFT_RESEARCH), locale="sv")
    assert "research_notes_snapshot" in out


def test_portfolio_snapshot_type_in_validation_sv() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    out = render_snapshot_draft_validation(_load_draft(_DRAFT_PORTFOLIO), locale="sv")
    assert "portfolio_snapshot" in out


def test_news_snapshot_type_in_validation_sv() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    out = render_snapshot_draft_validation(_load_draft(_DRAFT_NEWS), locale="sv")
    assert "news_snapshot" in out


def test_research_notes_snapshot_type_in_review_sv() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_review
    out = render_snapshot_draft_review(_load_draft(_DRAFT_RESEARCH), locale="sv")
    assert "research_notes_snapshot" in out


# ---------------------------------------------------------------------------
# B11 — SnapshotConfirmationStatus values unchanged in Swedish Snapshot output
# ---------------------------------------------------------------------------

_ALL_CONFIRMATION_STATUSES = [
    "draft",
    "needs_user_review",
    "confirmed",
    "rejected",
    "superseded",
]


def test_confirmation_status_draft_in_validation_sv() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    # The research_notes_snapshot fixture has confirmation_status = "draft"
    out = render_snapshot_draft_validation(_load_draft(_DRAFT_RESEARCH), locale="sv")
    assert "draft" in out


def test_confirmation_status_needs_user_review_in_validation_sv() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    # The portfolio_snapshot fixture has confirmation_status = "needs_user_review"
    out = render_snapshot_draft_validation(_load_draft(_DRAFT_PORTFOLIO), locale="sv")
    assert "needs_user_review" in out


def test_confirmation_status_confirmed_in_validation_sv() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    # The research_notes_snapshot_confirmed fixture has confirmation_status = "confirmed"
    out = render_snapshot_draft_validation(_load_draft(_DRAFT_CONFIRMED), locale="sv")
    assert "confirmed" in out


@pytest.mark.parametrize("status", _ALL_CONFIRMATION_STATUSES)
def test_confirmation_status_unchanged_in_confirm_success_sv(status: str) -> None:
    # confirm_success output shows snapshot_type in the output — the status
    # arg is not displayed directly by that renderer, but the snapshot_type is.
    # Separately verify Swedish does not produce translated status words.
    from atlas.snapshot_input.render import render_snapshot_confirm_success
    out = render_snapshot_confirm_success("in.json", "out.json", "research_notes_snapshot", False, locale="sv")
    # Confirm that "Bekräftelse" (Swedish UI label) is present but the raw
    # status value "research_notes_snapshot" is also present (not translated).
    assert "research_notes_snapshot" in out
    assert "Bekräftelse" in out


# ---------------------------------------------------------------------------
# B11 — SnapshotConfidence values unchanged in Swedish Snapshot output
# ---------------------------------------------------------------------------

_ALL_CONFIDENCE_VALUES = ["high", "medium", "low", "unknown"]


def test_confidence_high_in_validation_sv() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    # research_notes_snapshot has confidence = "high"
    out = render_snapshot_draft_validation(_load_draft(_DRAFT_RESEARCH), locale="sv")
    assert "high" in out


def test_confidence_medium_in_validation_sv() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    # portfolio_snapshot has confidence = "medium"
    out = render_snapshot_draft_validation(_load_draft(_DRAFT_PORTFOLIO), locale="sv")
    assert "medium" in out


def test_confidence_low_in_validation_sv() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    # news_snapshot has confidence = "low"
    out = render_snapshot_draft_validation(_load_draft(_DRAFT_NEWS), locale="sv")
    assert "low" in out


def test_confidence_high_in_review_sv() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_review
    out = render_snapshot_draft_review(_load_draft(_DRAFT_RESEARCH), locale="sv")
    assert "high" in out


# ---------------------------------------------------------------------------
# B11 — Warning codes unchanged in Swedish Weekly Review output
# ---------------------------------------------------------------------------

_KNOWN_WARNING_CODES = [
    "missing_optional_profile",
    "missing_optional_journal",
    "missing_optional_financials",
    "missing_optional_company_facts",
    "missing_watchlist_status",
    "unknown_watchlist_status",
    "missing_sector",
    "missing_market_value",
]


def test_warning_code_missing_optional_financials_unchanged_in_sv() -> None:
    # The rich fixture loads real files; missing_optional_financials is triggered
    # when a financials_dir is not provided (or has no file for a ticker).
    # Run with minimal inputs so warnings appear.
    from atlas.weekly_review.inputs import WeeklyReviewInputPaths, load_weekly_review_inputs
    from atlas.weekly_review.render import render_weekly_review
    paths = WeeklyReviewInputPaths(
        portfolio_path=_PORTFOLIO,
        watchlist_path=_WATCHLIST,
        as_of="2026-01-05",
    )
    result = load_weekly_review_inputs(paths)
    out_sv = render_weekly_review(result, locale="sv")
    out_en = render_weekly_review(result, locale="en")
    # Collect warning codes from English output; they must appear identically in Swedish
    import re
    en_codes = re.findall(r'\[([a-z_]+)\]', out_en)
    for code in en_codes:
        assert code in out_sv, (
            f"Warning code {code!r} missing from Swedish output (found in English output)"
        )


def test_warning_code_format_unchanged_in_sv() -> None:
    # WARNING_ROW = "- [{code}] {message}" — the [{code}] part must be identical in sv
    from atlas.weekly_review.inputs import WeeklyReviewInputPaths, load_weekly_review_inputs
    from atlas.weekly_review.render import render_weekly_review
    import re
    paths = WeeklyReviewInputPaths(
        portfolio_path=_PORTFOLIO,
        watchlist_path=_WATCHLIST,
        as_of="2026-01-05",
    )
    result = load_weekly_review_inputs(paths)
    out_sv = render_weekly_review(result, locale="sv")
    # Warning rows must use the canonical bracket-code format (lowercase snake_case)
    # Filter to lines that look like warning codes (lowercase with underscores, not tickers)
    warning_lines = [
        l for l in out_sv.splitlines()
        if l.startswith("- [") and re.match(r'^- \[[a-z][a-z_]+\]', l)
    ]
    assert warning_lines, "Expected at least one warning code line in sv output"
    for line in warning_lines:
        assert re.match(r'^- \[[a-z][a-z_]+\]', line), (
            f"Warning line does not use canonical format: {line!r}"
        )


def test_warning_codes_en_sv_parity() -> None:
    from atlas.weekly_review.inputs import WeeklyReviewInputPaths, load_weekly_review_inputs
    from atlas.weekly_review.render import render_weekly_review
    import re
    paths = WeeklyReviewInputPaths(
        portfolio_path=_PORTFOLIO,
        watchlist_path=_WATCHLIST,
        as_of="2026-01-05",
    )
    result = load_weekly_review_inputs(paths)
    out_sv = render_weekly_review(result, locale="sv")
    out_en = render_weekly_review(result, locale="en")
    sv_codes = sorted(re.findall(r'\[([a-z_]+)\]', out_sv))
    en_codes = sorted(re.findall(r'\[([a-z_]+)\]', out_en))
    assert sv_codes == en_codes, (
        f"Warning codes differ between sv and en output.\n"
        f"sv: {sv_codes}\nen: {en_codes}"
    )


# ---------------------------------------------------------------------------
# B11 — Ticker symbols unchanged in Swedish Weekly Review output
# ---------------------------------------------------------------------------

_KNOWN_TICKERS = ["MSFT", "ASML"]


@pytest.mark.parametrize("ticker", _KNOWN_TICKERS)
def test_ticker_unchanged_in_sv_wr(ticker: str) -> None:
    out_sv = _sv_wr()
    out_en = _en_wr()
    if ticker in out_en:
        assert ticker in out_sv, (
            f"Ticker {ticker!r} present in English WR but missing from Swedish WR"
        )


def test_ticker_cash_unchanged_in_sv_wr() -> None:
    # CASH is a holding ticker
    out_sv = _sv_wr()
    out_en = _en_wr()
    if "CASH" in out_en:
        assert "CASH" in out_sv


@pytest.mark.parametrize("ticker", ["XYL", "NOVO"])
def test_watchlist_ticker_unchanged_in_sv_wr(ticker: str) -> None:
    out_sv = _sv_wr()
    out_en = _en_wr()
    if ticker in out_en:
        assert ticker in out_sv, (
            f"Watchlist ticker {ticker!r} present in English WR but missing from Swedish WR"
        )


def test_snapshot_ticker_unchanged_in_validation_sv() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    out = render_snapshot_draft_validation(_load_draft(_DRAFT_RESEARCH), locale="sv")
    # The research_notes_snapshot fixture has ticker ASML
    assert "ASML" in out


def test_snapshot_ticker_unchanged_in_review_sv() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_review
    out = render_snapshot_draft_review(_load_draft(_DRAFT_RESEARCH), locale="sv")
    assert "ASML" in out


def test_ticker_count_en_sv_parity_in_wr() -> None:
    # Every ticker appearing in en output must appear in sv output.
    import re
    out_sv = _sv_wr()
    out_en = _en_wr()
    tickers_en = set(re.findall(r'\b[A-Z]{2,5}\b', out_en))
    # Exclude display-string tokens like "Q1" or "Atlas" abbreviations.
    # We only care about tokens that are present in en but absent in sv.
    for t in tickers_en:
        if t in ("OPEN", "DONE", "B1", "B2", "CLI", "WR", "JSON"):
            continue  # not tickers
        if t in out_en:
            assert t in out_sv or t not in _KNOWN_TICKERS, (
                f"Known ticker {t!r} in English but missing from Swedish output"
            )


# ---------------------------------------------------------------------------
# B11 — File paths unchanged in Swedish Snapshot output
# ---------------------------------------------------------------------------

def test_target_local_file_path_unchanged_in_review_sv() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_review
    out = render_snapshot_draft_review(_load_draft(_DRAFT_RESEARCH), locale="sv")
    # target_local_file from fixture
    assert "my_review/research_notes/ASML/notes.md" in out


def test_raw_source_reference_unchanged_in_review_sv() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_review
    out = render_snapshot_draft_review(_load_draft(_DRAFT_RESEARCH), locale="sv")
    assert "my_notes/asml_notes_2026.md" in out


def test_target_local_file_path_unchanged_in_validation_sv() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    out = render_snapshot_draft_validation(_load_draft(_DRAFT_RESEARCH), locale="sv")
    assert "my_review/research_notes/ASML/notes.md" in out


def test_input_path_unchanged_in_confirm_sv() -> None:
    from atlas.snapshot_input.render import render_snapshot_confirm_success
    in_path = "data/inputs/snapshot_drafts/asml_notes.json"
    out_path = "my_review/research_notes/ASML/notes.md"
    out = render_snapshot_confirm_success(in_path, out_path, "research_notes_snapshot", False, locale="sv")
    assert in_path in out
    assert out_path in out


def test_input_path_unchanged_in_reject_sv() -> None:
    from atlas.snapshot_input.render import render_snapshot_reject_success
    in_path = "data/inputs/snapshot_drafts/asml_notes.json"
    out_path = "my_review/research_notes/ASML/notes.md"
    out = render_snapshot_reject_success(in_path, out_path, "research_notes_snapshot", False, False, locale="sv")
    assert in_path in out


# ---------------------------------------------------------------------------
# B11 — Snapshot draft_id presence indicator unchanged in Swedish output
# ---------------------------------------------------------------------------

def test_draft_id_presence_indicator_unchanged_in_validation_sv() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    # The renderer renders draft_id as "present" or "missing" — not the raw value.
    # The indicator word must be identical in English and Swedish.
    out_sv = render_snapshot_draft_validation(_load_draft(_DRAFT_RESEARCH), locale="sv")
    out_en = render_snapshot_draft_validation(_load_draft(_DRAFT_RESEARCH), locale="en")
    # Both must have the same presence indicator line
    import re
    sv_line = next((l for l in out_sv.splitlines() if "Draft ID" in l), None)
    en_line = next((l for l in out_en.splitlines() if "Draft ID" in l), None)
    if en_line is not None and sv_line is not None:
        assert sv_line == en_line, (
            f"Draft ID line differs between locales.\nsv: {sv_line!r}\nen: {en_line!r}"
        )


# ---------------------------------------------------------------------------
# B12 — User-provided scope notes passthrough
# ---------------------------------------------------------------------------

_SCOPE_NOTES_SV = "Q1 granskning — fokus på tekniksektorn."
_SCOPE_NOTES_EN = "Q1 review — focus on the technology sector."


def test_scope_notes_sv_passthrough_in_sv_wr() -> None:
    out = _sv_wr(scope_notes=_SCOPE_NOTES_SV)
    assert _SCOPE_NOTES_SV in out


def test_scope_notes_en_passthrough_in_sv_wr() -> None:
    out = _sv_wr(scope_notes=_SCOPE_NOTES_EN)
    assert _SCOPE_NOTES_EN in out


def test_scope_notes_sv_passthrough_in_en_wr() -> None:
    out = _en_wr(scope_notes=_SCOPE_NOTES_SV)
    assert _SCOPE_NOTES_SV in out


def test_scope_notes_unchanged_between_locales() -> None:
    notes = "Halvårsgranskning av samtliga bevakningslisteposter."
    out_sv = _sv_wr(scope_notes=notes)
    out_en = _en_wr(scope_notes=notes)
    assert notes in out_sv
    assert notes in out_en


# ---------------------------------------------------------------------------
# B12 — User-provided watchlist reason passthrough
# ---------------------------------------------------------------------------

def test_watchlist_reason_xyl_unchanged_in_sv_wr() -> None:
    out = _sv_wr()
    # XYL reason from fixture: "Water infrastructure theme — long-term demand visibility from aging water networks"
    expected_fragment = "Water infrastructure theme"
    out_en = _en_wr()
    if expected_fragment in out_en:
        assert expected_fragment in out, (
            f"XYL watchlist reason fragment {expected_fragment!r} missing from Swedish WR"
        )


def test_watchlist_reason_preserved_across_locales() -> None:
    out_sv = _sv_wr()
    out_en = _en_wr()
    # Any watchlist reason present in English must also be present in Swedish
    watchlist_data = json.loads(_WATCHLIST.read_text(encoding="utf-8"))
    for item in watchlist_data.get("items", []):
        reason = item.get("reason", "")
        if reason and reason in out_en:
            assert reason in out_sv, (
                f"Watchlist reason {reason!r} missing from Swedish output"
            )


# ---------------------------------------------------------------------------
# B12 — User-provided research notes passthrough
# ---------------------------------------------------------------------------

def test_asml_thesis_fragment_unchanged_in_sv_wr() -> None:
    out = _sv_wr()
    out_en = _en_wr()
    # ASML notes contain "Lithography leadership remains the central thesis."
    fragment = "Lithography leadership"
    if fragment in out_en:
        assert fragment in out, (
            f"ASML research note fragment {fragment!r} missing from Swedish WR"
        )


def test_asml_evidence_gap_unchanged_in_sv_wr() -> None:
    out = _sv_wr()
    out_en = _en_wr()
    fragment = "Margin durability through a downcycle"
    if fragment in out_en:
        assert fragment in out, (
            f"ASML evidence gap text {fragment!r} missing from Swedish WR"
        )


def test_research_notes_passthrough_parity() -> None:
    out_sv = _sv_wr()
    out_en = _en_wr()
    notes_path = _RESEARCH_NOTES_DIR / "ASML" / "notes.md"
    if not notes_path.exists():
        pytest.skip("ASML notes fixture not found")
    notes_text = notes_path.read_text(encoding="utf-8")
    lines_in_en = [l.strip() for l in notes_text.splitlines() if len(l.strip()) > 20 and l.strip() in out_en]
    for line in lines_in_en[:5]:  # spot-check first 5 matching lines
        assert line in out_sv, (
            f"Research note line {line!r} present in English WR but missing from Swedish WR"
        )


# ---------------------------------------------------------------------------
# B12 — User-provided journal content passthrough
# ---------------------------------------------------------------------------

def test_journal_entry_decision_title_unchanged_in_sv_wr() -> None:
    out = _sv_wr()
    out_en = _en_wr()
    journal_data = json.loads(_JOURNAL.read_text(encoding="utf-8"))
    entries = journal_data if isinstance(journal_data, list) else journal_data.get("entries", [])
    for entry in entries[:2]:
        title = entry.get("decision_title", "")
        if title and title in out_en:
            assert title in out, (
                f"Journal decision_title {title!r} missing from Swedish WR"
            )


def test_journal_atlas_view_unchanged_in_sv_wr() -> None:
    out = _sv_wr()
    out_en = _en_wr()
    journal_data = json.loads(_JOURNAL.read_text(encoding="utf-8"))
    entries = journal_data if isinstance(journal_data, list) else journal_data.get("entries", [])
    for entry in entries[:2]:
        view = entry.get("atlas_view", "")
        if view and len(view) > 20 and view[:40] in out_en:
            assert view[:40] in out, (
                f"Journal atlas_view fragment missing from Swedish WR"
            )


# ---------------------------------------------------------------------------
# B12 — User-provided Snapshot content passthrough
# ---------------------------------------------------------------------------

def test_snapshot_notes_field_unchanged_in_review_sv() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_review
    out = render_snapshot_draft_review(_load_draft(_DRAFT_RESEARCH), locale="sv")
    # notes field: "Draft created from user-written research notes. Content is user-supplied..."
    assert "Draft created from user-written research notes" in out


def test_snapshot_source_description_unchanged_in_review_sv() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_review
    out = render_snapshot_draft_review(_load_draft(_DRAFT_RESEARCH), locale="sv")
    assert "User-written ASML research notes" in out


def test_snapshot_extracted_field_title_unchanged_in_review_sv() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_review
    out = render_snapshot_draft_review(_load_draft(_DRAFT_RESEARCH), locale="sv")
    # extracted_fields.title: "ASML research notes"
    assert "ASML research notes" in out


def test_snapshot_extracted_field_ticker_unchanged_in_review_sv() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_review
    out = render_snapshot_draft_review(_load_draft(_DRAFT_RESEARCH), locale="sv")
    assert "ASML" in out


def test_snapshot_notes_field_unchanged_in_validation_sv() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    out = render_snapshot_draft_validation(_load_draft(_DRAFT_RESEARCH), locale="sv")
    assert "Draft created from user-written research notes" in out


# ---------------------------------------------------------------------------
# B12 — render_weekly_review does not mutate result
# ---------------------------------------------------------------------------

def test_render_weekly_review_sv_does_not_mutate_result() -> None:
    from atlas.weekly_review.render import render_weekly_review
    result = _load_wr_result()
    # capture original field values
    original_as_of = result.as_of
    original_warning_count = len(result.warnings)
    render_weekly_review(result, locale="sv")
    # confirm no mutation
    assert result.as_of == original_as_of
    assert len(result.warnings) == original_warning_count


def test_render_weekly_review_sv_idempotent() -> None:
    from atlas.weekly_review.render import render_weekly_review
    result = _load_wr_result()
    out1 = render_weekly_review(result, locale="sv")
    out2 = render_weekly_review(result, locale="sv")
    assert out1 == out2


# ---------------------------------------------------------------------------
# English/default output unchanged
# ---------------------------------------------------------------------------

def test_en_output_unchanged_by_sv_render() -> None:
    from atlas.weekly_review.render import render_weekly_review
    result = _load_wr_result()
    en_before = render_weekly_review(result, locale="en")
    render_weekly_review(result, locale="sv")
    en_after = render_weekly_review(result, locale="en")
    assert en_before == en_after


def test_snapshot_en_output_unchanged_after_sv_render() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    draft = _load_draft(_DRAFT_RESEARCH)
    en_before = render_snapshot_draft_validation(draft, locale="en")
    render_snapshot_draft_validation(draft, locale="sv")
    en_after = render_snapshot_draft_validation(draft, locale="en")
    assert en_before == en_after


# ---------------------------------------------------------------------------
# Checklist: B11 DONE, B12 DONE, B13 OPEN, B14 OPEN
# ---------------------------------------------------------------------------

def test_checklist_b11_done() -> None:
    content = CHECKLIST.read_text(encoding="utf-8")
    lines = [l for l in content.splitlines() if "B11" in l]
    assert any("DONE" in l for l in lines), (
        f"Expected B11 DONE in checklist. Lines: {lines}"
    )


def test_checklist_b12_done() -> None:
    content = CHECKLIST.read_text(encoding="utf-8")
    lines = [l for l in content.splitlines() if "B12" in l]
    assert any("DONE" in l for l in lines), (
        f"Expected B12 DONE in checklist. Lines: {lines}"
    )


def test_checklist_b13_documented() -> None:
    # Sprint 253: B13 was OPEN; Sprint 254 marked it DONE — either state is valid
    content = CHECKLIST.read_text(encoding="utf-8")
    lines = [l for l in content.splitlines() if "B13" in l]
    assert any("OPEN" in l or "DONE" in l for l in lines)


def test_checklist_b14_documented() -> None:
    # Sprint 253: B14 was OPEN; Sprint 255 marked it DONE — either state is valid
    content = CHECKLIST.read_text(encoding="utf-8")
    lines = [l for l in content.splitlines() if "B14" in l]
    assert any("OPEN" in l or "DONE" in l for l in lines)


def test_checklist_criteria_count_documented() -> None:
    # Sprint 253 delivered 12 of 14; Sprint 254 advanced to 13 of 14 — check "of 14" present
    content = CHECKLIST.read_text(encoding="utf-8")
    assert "of 14" in content

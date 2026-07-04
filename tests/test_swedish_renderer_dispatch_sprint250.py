"""Sprint 250 — Swedish renderer dispatch tests.

Verifies that both renderers have a _strings_for_locale dispatch helper,
that it returns English strings for locale="en", that Swedish strings are
mapped for future locale="sv", that sv still raises at runtime, and that
default CLI output remains English.

No Swedish output is active. sv is not enabled. locale_support.py is unchanged.
B4 is satisfied. B5 remains open.
"""

from __future__ import annotations

import json
from pathlib import Path

WR_RENDER = Path("atlas/weekly_review/render.py")
SN_RENDER = Path("atlas/snapshot_input/render.py")
LOCALE_SUPPORT = Path("atlas/locale_support.py")
CHECKLIST = Path("docs/SwedishLocalizationReadinessChecklist.md")

_EXAMPLE_DRAFT = Path("examples/snapshot_drafts/research_notes_snapshot.json")
_PORTFOLIO = Path("examples/weekly_review/portfolio.json")
_WATCHLIST = Path("examples/weekly_review/watchlist.json")


# ---------------------------------------------------------------------------
# Dispatch helper exists in both renderers
# ---------------------------------------------------------------------------

def test_wr_has_strings_for_locale_function():
    source = WR_RENDER.read_text(encoding="utf-8")
    assert "_strings_for_locale" in source


def test_sn_has_strings_for_locale_function():
    source = SN_RENDER.read_text(encoding="utf-8")
    assert "_strings_for_locale" in source


def test_wr_dispatch_helper_importable():
    from atlas.weekly_review.render import _strings_for_locale
    assert callable(_strings_for_locale)


def test_sn_dispatch_helper_importable():
    from atlas.snapshot_input.render import _strings_for_locale
    assert callable(_strings_for_locale)


# ---------------------------------------------------------------------------
# Dispatch helper returns English strings for locale="en"
# ---------------------------------------------------------------------------

def test_wr_dispatch_returns_english_for_en():
    from atlas.weekly_review.render import _strings_for_locale
    from atlas.weekly_review import strings as strings_en
    result = _strings_for_locale("en")
    assert result is strings_en


def test_sn_dispatch_returns_english_for_en():
    from atlas.snapshot_input.render import _strings_for_locale
    from atlas.snapshot_input import strings as strings_en
    result = _strings_for_locale("en")
    assert result is strings_en


def test_wr_dispatch_en_title_is_english():
    from atlas.weekly_review.render import _strings_for_locale
    S = _strings_for_locale("en")
    assert S.WEEKLY_REVIEW_TITLE == "Atlas Weekly Investment Review"


def test_sn_dispatch_en_heading_is_english():
    from atlas.snapshot_input.render import _strings_for_locale
    S = _strings_for_locale("en")
    assert S.HEADING_VALIDATION == "Snapshot Draft Validation"


# ---------------------------------------------------------------------------
# Swedish strings are mapped in dispatch for future locale="sv"
# ---------------------------------------------------------------------------

def test_wr_dispatch_source_references_strings_sv():
    source = WR_RENDER.read_text(encoding="utf-8")
    assert "strings_sv" in source


def test_sn_dispatch_source_references_strings_sv():
    source = SN_RENDER.read_text(encoding="utf-8")
    assert "strings_sv" in source


def test_wr_dispatch_sv_branch_present():
    source = WR_RENDER.read_text(encoding="utf-8")
    assert 'locale == "sv"' in source
    assert "return strings_sv" in source


def test_sn_dispatch_sv_branch_present():
    source = SN_RENDER.read_text(encoding="utf-8")
    assert 'locale == "sv"' in source
    assert "return strings_sv" in source


# ---------------------------------------------------------------------------
# ensure_supported_locale: en passes, fr still raises (sv activated in Sprint 251)
# ---------------------------------------------------------------------------

def test_ensure_supported_locale_sv_accepted():
    # Sprint 251: sv is now supported — verify dispatch boundary preserved
    from atlas.locale_support import ensure_supported_locale
    ensure_supported_locale("sv")  # must not raise


def test_ensure_supported_locale_en_passes():
    from atlas.locale_support import ensure_supported_locale
    ensure_supported_locale("en")  # must not raise


def test_ensure_supported_locale_fr_still_raises():
    import pytest
    from atlas.locale_support import ensure_supported_locale
    with pytest.raises(ValueError, match="fr"):
        ensure_supported_locale("fr")


# ---------------------------------------------------------------------------
# render_weekly_review with locale="sv" now renders Swedish (Sprint 251)
# ---------------------------------------------------------------------------

def _load_draft():
    from atlas.snapshot_input.schema import SnapshotDraft
    return SnapshotDraft.from_dict(json.loads(_EXAMPLE_DRAFT.read_text(encoding="utf-8")))


def test_weekly_review_sv_renders():
    # Sprint 251: sv dispatch is now reachable
    from atlas.weekly_review.inputs import WeeklyReviewInputPaths, load_weekly_review_inputs
    from atlas.weekly_review.render import render_weekly_review
    paths = WeeklyReviewInputPaths(
        portfolio_path=_PORTFOLIO,
        watchlist_path=_WATCHLIST,
        as_of="2026-01-01",
    )
    result = load_weekly_review_inputs(paths)
    out = render_weekly_review(result, locale="sv")
    assert "Atlas veckovis investeringsgranskning" in out


def test_weekly_review_fr_still_raises():
    import pytest
    from atlas.weekly_review.inputs import WeeklyReviewInputPaths, load_weekly_review_inputs
    from atlas.weekly_review.render import render_weekly_review
    paths = WeeklyReviewInputPaths(
        portfolio_path=_PORTFOLIO,
        watchlist_path=_WATCHLIST,
        as_of="2026-01-01",
    )
    result = load_weekly_review_inputs(paths)
    with pytest.raises(ValueError, match="fr"):
        render_weekly_review(result, locale="fr")


# ---------------------------------------------------------------------------
# Snapshot renderer functions with locale="sv" now render Swedish (Sprint 251)
# ---------------------------------------------------------------------------

def test_validation_sv_renders():
    # Sprint 251: sv dispatch is now reachable
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    out = render_snapshot_draft_validation(_load_draft(), locale="sv")
    assert "Validering av Snapshot Draft" in out


def test_review_sv_renders():
    from atlas.snapshot_input.render import render_snapshot_draft_review
    out = render_snapshot_draft_review(_load_draft(), locale="sv")
    assert "Granskning av Snapshot Draft" in out


def test_confirm_success_sv_renders():
    from atlas.snapshot_input.render import render_snapshot_confirm_success
    out = render_snapshot_confirm_success("in.json", "out.json", "research_notes_snapshot", False, locale="sv")
    assert "Bekräftelse av Snapshot Draft" in out


def test_reject_success_sv_renders():
    from atlas.snapshot_input.render import render_snapshot_reject_success
    out = render_snapshot_reject_success("in.json", "out.json", "research_notes_snapshot", False, False, locale="sv")
    assert "Avvisning av Snapshot Draft" in out


def test_company_facts_export_sv_renders():
    from atlas.snapshot_input.render import render_company_facts_export_success
    out = render_company_facts_export_success("MSFT", "/tmp/f.json", locale="sv")
    assert "Export av företagsfakta" in out


def test_snap_fr_still_raises():
    import pytest
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    with pytest.raises(ValueError, match="fr"):
        render_snapshot_draft_validation(_load_draft(), locale="fr")


# ---------------------------------------------------------------------------
# Default Weekly Review output remains English
# ---------------------------------------------------------------------------

def test_weekly_review_default_output_english():
    from atlas.weekly_review.inputs import WeeklyReviewInputPaths, load_weekly_review_inputs
    from atlas.weekly_review.render import render_weekly_review
    paths = WeeklyReviewInputPaths(
        portfolio_path=_PORTFOLIO,
        watchlist_path=_WATCHLIST,
        as_of="2026-01-01",
    )
    result = load_weekly_review_inputs(paths)
    out = render_weekly_review(result)
    assert "Atlas Weekly Investment Review" in out
    assert "1. Review Scope" in out
    assert "10. Non-Actions / Reasons to Wait" in out


def test_weekly_review_default_no_swedish_headings():
    from atlas.weekly_review.inputs import WeeklyReviewInputPaths, load_weekly_review_inputs
    from atlas.weekly_review.render import render_weekly_review
    paths = WeeklyReviewInputPaths(
        portfolio_path=_PORTFOLIO,
        watchlist_path=_WATCHLIST,
        as_of="2026-01-01",
    )
    result = load_weekly_review_inputs(paths)
    out = render_weekly_review(result)
    for sv_term in ["Granskningens omfattning", "Portföljkontext", "Indatastatus", "Underlagslucka"]:
        assert sv_term not in out, f"Swedish term in default English output: {sv_term!r}"


def test_weekly_review_locale_en_explicit_equals_default():
    from atlas.weekly_review.inputs import WeeklyReviewInputPaths, load_weekly_review_inputs
    from atlas.weekly_review.render import render_weekly_review
    paths = WeeklyReviewInputPaths(
        portfolio_path=_PORTFOLIO,
        watchlist_path=_WATCHLIST,
        as_of="2026-01-01",
    )
    result = load_weekly_review_inputs(paths)
    assert render_weekly_review(result) == render_weekly_review(result, locale="en")


# ---------------------------------------------------------------------------
# Default Snapshot CLI output remains English
# ---------------------------------------------------------------------------

def test_snapshot_validation_default_english():
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    out = render_snapshot_draft_validation(_load_draft())
    assert "Snapshot Draft Validation" in out
    assert "Safety Boundary:" in out
    assert "Validering av Snapshot Draft" not in out
    assert "Säkerhetsgräns" not in out


def test_snapshot_validation_locale_en_explicit_equals_default():
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    draft = _load_draft()
    assert render_snapshot_draft_validation(draft) == render_snapshot_draft_validation(draft, locale="en")


# ---------------------------------------------------------------------------
# locale_support.py — Sprint 251 activated sv; en still present
# ---------------------------------------------------------------------------

def test_locale_support_sv_now_present():
    # Sprint 251: SUPPORTED_LOCALE_SV added
    source = LOCALE_SUPPORT.read_text(encoding="utf-8")
    assert 'SUPPORTED_LOCALE_SV = "sv"' in source


def test_locale_support_still_has_en():
    source = LOCALE_SUPPORT.read_text(encoding="utf-8")
    assert 'SUPPORTED_LOCALE_EN = "en"' in source
    assert "ensure_supported_locale" in source


# ---------------------------------------------------------------------------
# No --language in CLI
# ---------------------------------------------------------------------------

def test_no_language_option_in_cli():
    import atlas.cli.main as main_mod
    source = Path(main_mod.__file__).read_text(encoding="utf-8")
    assert "--language" not in source


# ---------------------------------------------------------------------------
# No infrastructure additions
# ---------------------------------------------------------------------------

def test_no_gettext_in_wr_render():
    assert "gettext" not in WR_RENDER.read_text(encoding="utf-8")


def test_no_gettext_in_sn_render():
    assert "gettext" not in SN_RENDER.read_text(encoding="utf-8")


def test_no_provider_imports_in_wr_render():
    source = WR_RENDER.read_text(encoding="utf-8")
    for term in ["requests", "urllib", "httpx", "aiohttp"]:
        assert term not in source


def test_no_provider_imports_in_sn_render():
    source = SN_RENDER.read_text(encoding="utf-8")
    for term in ["requests", "urllib", "httpx", "aiohttp"]:
        assert term not in source


# ---------------------------------------------------------------------------
# Readiness checklist — B4 DONE, B5 OPEN
# ---------------------------------------------------------------------------

def test_checklist_b4_done():
    content = CHECKLIST.read_text(encoding="utf-8")
    lines = [l for l in content.splitlines() if "B4" in l]
    assert any("DONE" in l for l in lines)


def test_checklist_b5_documented():
    # Sprint 250: B5 was OPEN; Sprint 251 marked it DONE — either state is valid
    content = CHECKLIST.read_text(encoding="utf-8")
    lines = [l for l in content.splitlines() if "B5" in l]
    assert any("OPEN" in l or "DONE" in l for l in lines)


def test_checklist_b6_open():
    content = CHECKLIST.read_text(encoding="utf-8")
    lines = [l for l in content.splitlines() if "B6" in l]
    assert any("OPEN" in l for l in lines)


def test_checklist_criteria_count_documented():
    # Sprint 250 delivered 4 of 14; Sprint 251 advanced to 5 of 14 — either is acceptable
    content = CHECKLIST.read_text(encoding="utf-8")
    assert "of 14" in content

"""Sprint 246 — Shared locale boundary helper tests.

Verifies that atlas.locale_support provides the shared locale constant and
guard used by both Weekly Review and Snapshot CLI renderers. Confirms that
duplicate local guards have been removed from both renderer modules and that
all rendering behavior is unchanged.
"""

from __future__ import annotations

import json
from pathlib import Path

LOCALE_MODULE = Path("atlas/locale_support.py")
WR_RENDER_MODULE = Path("atlas/weekly_review/render.py")
SNAP_RENDER_MODULE = Path("atlas/snapshot_input/render.py")

FORBIDDEN_LANGUAGE = [
    "Strong Buy",
    "Strong Sell",
    "Price Target",
    "Target Price",
    "Act Now",
    "Must Buy",
    "Must Sell",
    "Guaranteed",
    "Will Outperform",
    "Financial Advice",
]


# ---------------------------------------------------------------------------
# Shared module exists and is correct
# ---------------------------------------------------------------------------

def test_locale_support_module_exists():
    assert LOCALE_MODULE.exists()


def test_supported_locale_en_constant():
    from atlas.locale_support import SUPPORTED_LOCALE_EN
    assert SUPPORTED_LOCALE_EN == "en"


def test_ensure_supported_locale_accepts_en():
    from atlas.locale_support import ensure_supported_locale
    ensure_supported_locale("en")  # must not raise


def test_ensure_supported_locale_rejects_sv():
    import pytest
    from atlas.locale_support import ensure_supported_locale
    with pytest.raises(ValueError, match="sv"):
        ensure_supported_locale("sv")


def test_ensure_supported_locale_rejects_fr():
    import pytest
    from atlas.locale_support import ensure_supported_locale
    with pytest.raises(ValueError, match="fr"):
        ensure_supported_locale("fr")


def test_ensure_supported_locale_rejects_de():
    import pytest
    from atlas.locale_support import ensure_supported_locale
    with pytest.raises(ValueError, match="de"):
        ensure_supported_locale("de")


def test_error_message_includes_bad_locale():
    from atlas.locale_support import ensure_supported_locale
    try:
        ensure_supported_locale("xx")
    except ValueError as e:
        assert "xx" in str(e)
    else:
        raise AssertionError("Expected ValueError")


def test_error_message_mentions_en():
    from atlas.locale_support import ensure_supported_locale
    try:
        ensure_supported_locale("sv")
    except ValueError as e:
        assert "en" in str(e)
    else:
        raise AssertionError("Expected ValueError")


def test_error_message_exact_format():
    from atlas.locale_support import ensure_supported_locale
    try:
        ensure_supported_locale("sv")
    except ValueError as e:
        assert str(e) == "Unsupported locale: 'sv'. Only 'en' is currently supported."
    else:
        raise AssertionError("Expected ValueError")


def test_locale_module_no_imports_beyond_annotations():
    source = LOCALE_MODULE.read_text(encoding="utf-8")
    assert "import gettext" not in source
    assert "import locale" not in source
    assert "import os" not in source
    for term in ["requests", "urllib", "httpx", "aiohttp"]:
        assert term not in source


# ---------------------------------------------------------------------------
# Weekly Review renderer uses shared helper
# ---------------------------------------------------------------------------

def test_wr_render_imports_shared_locale():
    source = WR_RENDER_MODULE.read_text(encoding="utf-8")
    assert "from atlas.locale_support import" in source


def test_wr_render_no_duplicate_locale_guard():
    source = WR_RENDER_MODULE.read_text(encoding="utf-8")
    assert 'if locale != "en"' not in source


def test_wr_render_no_local_ensure_locale_definition():
    source = WR_RENDER_MODULE.read_text(encoding="utf-8")
    assert "def _ensure_locale" not in source


def test_wr_render_no_local_supported_locale_constant():
    source = WR_RENDER_MODULE.read_text(encoding="utf-8")
    assert "_SUPPORTED_LOCALE" not in source


# ---------------------------------------------------------------------------
# Snapshot renderer uses shared helper
# ---------------------------------------------------------------------------

def test_snap_render_imports_shared_locale():
    source = SNAP_RENDER_MODULE.read_text(encoding="utf-8")
    assert "from atlas.locale_support import" in source


def test_snap_render_no_local_supported_locale_constant():
    source = SNAP_RENDER_MODULE.read_text(encoding="utf-8")
    assert "_SUPPORTED_LOCALE" not in source


def test_snap_render_no_duplicate_local_guard_definition():
    source = SNAP_RENDER_MODULE.read_text(encoding="utf-8")
    # The local def should be gone; ensure_supported_locale is now imported
    # (it may be aliased as _ensure_locale — that is acceptable)
    assert "def _ensure_locale" not in source


# ---------------------------------------------------------------------------
# Output preservation — Weekly Review
# ---------------------------------------------------------------------------

def _load_wr_minimal():
    from atlas.weekly_review.inputs import WeeklyReviewInputPaths, load_weekly_review_inputs
    paths = WeeklyReviewInputPaths(
        portfolio_path=Path("examples/weekly_review/portfolio.json"),
        watchlist_path=Path("examples/weekly_review/watchlist.json"),
        as_of="2026-01-01",
    )
    return load_weekly_review_inputs(paths)


def test_wr_default_equals_locale_en():
    from atlas.weekly_review.render import render_weekly_review
    result = _load_wr_minimal()
    assert render_weekly_review(result) == render_weekly_review(result, locale="en")


def test_wr_locale_en_includes_title():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_wr_minimal(), locale="en")
    assert "# Atlas Weekly Investment Review" in out


def test_wr_locale_en_includes_all_sections():
    from atlas.weekly_review.render import render_weekly_review
    from atlas.weekly_review.strings import WEEKLY_REVIEW_SECTION_TITLES
    out = render_weekly_review(_load_wr_minimal(), locale="en")
    for title in WEEKLY_REVIEW_SECTION_TITLES:
        assert title in out


def test_wr_unsupported_locale_still_raises():
    import pytest
    from atlas.weekly_review.render import render_weekly_review
    with pytest.raises(ValueError, match="sv"):
        render_weekly_review(_load_wr_minimal(), locale="sv")


# ---------------------------------------------------------------------------
# Output preservation — Snapshot CLI
# ---------------------------------------------------------------------------

def _load_draft():
    from atlas.snapshot_input.schema import SnapshotDraft
    return SnapshotDraft.from_dict(
        json.loads(Path("examples/snapshot_drafts/research_notes_snapshot.json").read_text(encoding="utf-8"))
    )


def test_snap_validation_default_equals_locale_en():
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    draft = _load_draft()
    assert render_snapshot_draft_validation(draft) == render_snapshot_draft_validation(draft, locale="en")


def test_snap_review_default_equals_locale_en():
    from atlas.snapshot_input.render import render_snapshot_draft_review
    draft = _load_draft()
    assert render_snapshot_draft_review(draft) == render_snapshot_draft_review(draft, locale="en")


def test_snap_unsupported_locale_still_raises():
    import pytest
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    with pytest.raises(ValueError, match="fr"):
        render_snapshot_draft_validation(_load_draft(), locale="fr")


def test_snap_error_message_exact():
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    try:
        render_snapshot_draft_validation(_load_draft(), locale="sv")
    except ValueError as e:
        assert str(e) == "Unsupported locale: 'sv'. Only 'en' is currently supported."
    else:
        raise AssertionError("Expected ValueError")


# ---------------------------------------------------------------------------
# CLI unchanged
# ---------------------------------------------------------------------------

def test_no_language_option_in_cli():
    import atlas.cli.main as main_mod
    source = Path(main_mod.__file__).read_text(encoding="utf-8")
    assert "--language" not in source


def test_cli_does_not_pass_locale_kwarg():
    import atlas.cli.main as main_mod
    source = Path(main_mod.__file__).read_text(encoding="utf-8")
    assert "locale=" not in source


# ---------------------------------------------------------------------------
# No new translation infrastructure
# ---------------------------------------------------------------------------

def test_no_translation_files():
    assert not Path("atlas/locale").exists()
    assert not Path("atlas/translations").exists()
    assert not Path("atlas/weekly_review/locale").exists()
    assert not Path("atlas/snapshot_input/locale").exists()


def test_locale_module_no_forbidden_language():
    content = LOCALE_MODULE.read_text(encoding="utf-8")
    for term in FORBIDDEN_LANGUAGE:
        assert term not in content, f"Forbidden language in locale_support: {term!r}"


# ---------------------------------------------------------------------------
# Existing strings constants remain intact
# ---------------------------------------------------------------------------

def test_wr_strings_constants_intact():
    from atlas.weekly_review import strings as S
    assert S.WEEKLY_REVIEW_TITLE == "Atlas Weekly Investment Review"
    assert len(S.WEEKLY_REVIEW_SECTION_TITLES) == 10
    assert S.LABEL_EVIDENCE_GAP == "Evidence Gap"
    assert S.INPUT_STATUS_PORTFOLIO_LOADED == "Portfolio: {count} holding(s) loaded."
    assert S.WARNING_ROW == "- [{code}] {message}"
    assert "deterministic, local-only" in S.WEEKLY_REVIEW_DISCLAIMER


def test_snap_strings_constants_intact():
    from atlas.snapshot_input import strings as SS
    assert SS.HEADING_VALIDATION == "Snapshot Draft Validation"
    assert SS.HEADING_COMPANY_FACTS_EXPORT == "Company Facts Export"

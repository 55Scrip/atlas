"""Sprint 254 — Unsupported-locale regression matrix.

Verifies B13: after sv activation, every unsupported locale still raises
ValueError from ensure_supported_locale, render_weekly_review, and all 14
public Snapshot locale-aware renderer functions.

Supported locales remain exactly: "en" and "sv".
Unsupported locales tested: fr, de, ja, no, da, fi, es, xx, empty string,
uppercase variants (EN, SV), region variants (en-US, sv-SE).

No runtime code changes. No --language. CLI remains English.
B13 is DONE. B14 remains OPEN.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

_PORTFOLIO = Path("examples/weekly_review/portfolio.json")
_WATCHLIST = Path("examples/weekly_review/watchlist.json")
_DRAFT_RESEARCH = Path("examples/snapshot_drafts/research_notes_snapshot.json")

CHECKLIST = Path("docs/SwedishLocalizationReadinessChecklist.md")
WR_RENDER = Path("atlas/weekly_review/render.py")
SN_RENDER = Path("atlas/snapshot_input/render.py")
LOCALE_SUPPORT = Path("atlas/locale_support.py")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_wr_result():
    from atlas.weekly_review.inputs import WeeklyReviewInputPaths, load_weekly_review_inputs
    paths = WeeklyReviewInputPaths(
        portfolio_path=_PORTFOLIO,
        watchlist_path=_WATCHLIST,
        as_of="2026-01-05",
    )
    return load_weekly_review_inputs(paths)


def _load_draft():
    from atlas.snapshot_input.schema import SnapshotDraft
    return SnapshotDraft.from_dict(
        json.loads(_DRAFT_RESEARCH.read_text(encoding="utf-8"))
    )


def _atlas_cli(*args: str) -> subprocess.CompletedProcess:
    atlas_bin = str(Path(".venv/bin/atlas").resolve())
    return subprocess.run([atlas_bin, *args], capture_output=True, text=True)


_UNSUPPORTED_LOCALES = [
    "fr",
    "de",
    "ja",
    "no",
    "da",
    "fi",
    "es",
    "xx",
    "",
    "EN",
    "SV",
    "en-US",
    "sv-SE",
]


# ---------------------------------------------------------------------------
# Supported locales remain exactly en and sv
# ---------------------------------------------------------------------------

def test_supported_locale_en_constant() -> None:
    from atlas.locale_support import SUPPORTED_LOCALE_EN
    assert SUPPORTED_LOCALE_EN == "en"


def test_supported_locale_sv_constant() -> None:
    from atlas.locale_support import SUPPORTED_LOCALE_SV
    assert SUPPORTED_LOCALE_SV == "sv"


def test_supported_locales_set_is_exactly_en_sv() -> None:
    from atlas.locale_support import _SUPPORTED_LOCALES
    assert _SUPPORTED_LOCALES == frozenset({"en", "sv"})


def test_no_other_supported_locale_in_source() -> None:
    source = LOCALE_SUPPORT.read_text(encoding="utf-8")
    # Only "en" and "sv" should appear as supported locale string literals
    for lang in ("fr", "de", "ja", "no", "da", "fi", "es"):
        assert f'"{lang}"' not in source, (
            f"Locale {lang!r} unexpectedly present in locale_support.py"
        )


# ---------------------------------------------------------------------------
# ensure_supported_locale: en and sv pass
# ---------------------------------------------------------------------------

def test_ensure_supported_locale_en_passes() -> None:
    from atlas.locale_support import ensure_supported_locale
    ensure_supported_locale("en")  # must not raise


def test_ensure_supported_locale_sv_passes() -> None:
    from atlas.locale_support import ensure_supported_locale
    ensure_supported_locale("sv")  # must not raise


# ---------------------------------------------------------------------------
# ensure_supported_locale: unsupported locales raise
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("locale", _UNSUPPORTED_LOCALES)
def test_ensure_supported_locale_rejects_unsupported(locale: str) -> None:
    from atlas.locale_support import ensure_supported_locale
    with pytest.raises(ValueError):
        ensure_supported_locale(locale)


# ---------------------------------------------------------------------------
# ensure_supported_locale: error message quality
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("locale", ["fr", "de", "ja", "xx", "EN", "SV", "en-US"])
def test_ensure_supported_locale_error_includes_bad_locale(locale: str) -> None:
    from atlas.locale_support import ensure_supported_locale
    with pytest.raises(ValueError, match=repr(locale)):
        ensure_supported_locale(locale)


def test_ensure_supported_locale_error_includes_empty_string() -> None:
    from atlas.locale_support import ensure_supported_locale
    with pytest.raises(ValueError) as exc_info:
        ensure_supported_locale("")
    assert "''" in str(exc_info.value) or "empty" in str(exc_info.value).lower() or str(exc_info.value)


def test_ensure_supported_locale_error_includes_en() -> None:
    from atlas.locale_support import ensure_supported_locale
    with pytest.raises(ValueError) as exc_info:
        ensure_supported_locale("fr")
    assert "'en'" in str(exc_info.value) or "en" in str(exc_info.value)


def test_ensure_supported_locale_error_includes_sv() -> None:
    from atlas.locale_support import ensure_supported_locale
    with pytest.raises(ValueError) as exc_info:
        ensure_supported_locale("fr")
    assert "'sv'" in str(exc_info.value) or "sv" in str(exc_info.value)


def test_ensure_supported_locale_error_names_bad_locale_fr() -> None:
    from atlas.locale_support import ensure_supported_locale
    with pytest.raises(ValueError) as exc_info:
        ensure_supported_locale("fr")
    assert "fr" in str(exc_info.value)


def test_ensure_supported_locale_error_names_bad_locale_en_us() -> None:
    from atlas.locale_support import ensure_supported_locale
    with pytest.raises(ValueError) as exc_info:
        ensure_supported_locale("en-US")
    assert "en-US" in str(exc_info.value)


def test_ensure_supported_locale_empty_string_raises() -> None:
    from atlas.locale_support import ensure_supported_locale
    with pytest.raises(ValueError):
        ensure_supported_locale("")


def test_ensure_supported_locale_uppercase_en_raises() -> None:
    from atlas.locale_support import ensure_supported_locale
    with pytest.raises(ValueError):
        ensure_supported_locale("EN")


def test_ensure_supported_locale_uppercase_sv_raises() -> None:
    from atlas.locale_support import ensure_supported_locale
    with pytest.raises(ValueError):
        ensure_supported_locale("SV")


# ---------------------------------------------------------------------------
# Weekly Review renderer: unsupported locales raise
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("locale", _UNSUPPORTED_LOCALES)
def test_render_weekly_review_rejects_unsupported(locale: str) -> None:
    from atlas.weekly_review.render import render_weekly_review
    with pytest.raises(ValueError):
        render_weekly_review(_load_wr_result(), locale=locale)


def test_render_weekly_review_fr_no_partial_output() -> None:
    from atlas.weekly_review.render import render_weekly_review
    result = None
    try:
        result = render_weekly_review(_load_wr_result(), locale="fr")
    except ValueError:
        pass
    assert result is None, "render_weekly_review must not return partial output for unsupported locale"


def test_render_weekly_review_en_still_passes() -> None:
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_wr_result(), locale="en")
    assert "Atlas Weekly Investment Review" in out


def test_render_weekly_review_sv_still_passes() -> None:
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_wr_result(), locale="sv")
    assert "Atlas veckovis investeringsgranskning" in out


# ---------------------------------------------------------------------------
# Snapshot renderer: render_snapshot_draft_validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("locale", _UNSUPPORTED_LOCALES)
def test_snapshot_validation_rejects_unsupported(locale: str) -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    with pytest.raises(ValueError):
        render_snapshot_draft_validation(_load_draft(), locale=locale)


# ---------------------------------------------------------------------------
# Snapshot renderer: render_snapshot_draft_validation_error
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("locale", ["fr", "de", "ja", "xx", "EN", "en-US"])
def test_snapshot_validation_error_rejects_unsupported(locale: str) -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_validation_error
    with pytest.raises(ValueError):
        render_snapshot_draft_validation_error("some error", locale=locale)


# ---------------------------------------------------------------------------
# Snapshot renderer: render_snapshot_draft_review
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("locale", _UNSUPPORTED_LOCALES)
def test_snapshot_review_rejects_unsupported(locale: str) -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_review
    with pytest.raises(ValueError):
        render_snapshot_draft_review(_load_draft(), locale=locale)


# ---------------------------------------------------------------------------
# Snapshot renderer: render_snapshot_draft_review_error
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("locale", ["fr", "de", "ja", "xx", "EN", "en-US"])
def test_snapshot_review_error_rejects_unsupported(locale: str) -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_review_error
    with pytest.raises(ValueError):
        render_snapshot_draft_review_error("some error", locale=locale)


# ---------------------------------------------------------------------------
# Snapshot renderer: render_snapshot_confirm_success
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("locale", _UNSUPPORTED_LOCALES)
def test_snapshot_confirm_success_rejects_unsupported(locale: str) -> None:
    from atlas.snapshot_input.render import render_snapshot_confirm_success
    with pytest.raises(ValueError):
        render_snapshot_confirm_success("in.json", "out.json", "research_notes_snapshot", False, locale=locale)


# ---------------------------------------------------------------------------
# Snapshot renderer: render_snapshot_confirm_blocked
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("locale", ["fr", "de", "ja", "xx", "EN", "en-US"])
def test_snapshot_confirm_blocked_rejects_unsupported(locale: str) -> None:
    from atlas.snapshot_input.render import render_snapshot_confirm_blocked
    with pytest.raises(ValueError):
        render_snapshot_confirm_blocked("reason", locale=locale)


# ---------------------------------------------------------------------------
# Snapshot renderer: render_snapshot_confirm_error
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("locale", ["fr", "de", "ja", "xx", "EN", "en-US"])
def test_snapshot_confirm_error_rejects_unsupported(locale: str) -> None:
    from atlas.snapshot_input.render import render_snapshot_confirm_error
    with pytest.raises(ValueError):
        render_snapshot_confirm_error("some error", locale=locale)


# ---------------------------------------------------------------------------
# Snapshot renderer: render_snapshot_reject_success
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("locale", _UNSUPPORTED_LOCALES)
def test_snapshot_reject_success_rejects_unsupported(locale: str) -> None:
    from atlas.snapshot_input.render import render_snapshot_reject_success
    with pytest.raises(ValueError):
        render_snapshot_reject_success("in.json", "out.json", "research_notes_snapshot", False, False, locale=locale)


# ---------------------------------------------------------------------------
# Snapshot renderer: render_snapshot_reject_blocked
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("locale", ["fr", "de", "ja", "xx", "EN", "en-US"])
def test_snapshot_reject_blocked_rejects_unsupported(locale: str) -> None:
    from atlas.snapshot_input.render import render_snapshot_reject_blocked
    with pytest.raises(ValueError):
        render_snapshot_reject_blocked("reason", locale=locale)


# ---------------------------------------------------------------------------
# Snapshot renderer: render_snapshot_reject_error
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("locale", ["fr", "de", "ja", "xx", "EN", "en-US"])
def test_snapshot_reject_error_rejects_unsupported(locale: str) -> None:
    from atlas.snapshot_input.render import render_snapshot_reject_error
    with pytest.raises(ValueError):
        render_snapshot_reject_error("some error", locale=locale)


# ---------------------------------------------------------------------------
# Snapshot renderer: render_research_notes_export_success
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("locale", _UNSUPPORTED_LOCALES)
def test_research_notes_export_success_rejects_unsupported(locale: str) -> None:
    from atlas.snapshot_input.render import render_research_notes_export_success
    with pytest.raises(ValueError):
        render_research_notes_export_success("ASML", "/tmp/f.json", locale=locale)


# ---------------------------------------------------------------------------
# Snapshot renderer: render_research_notes_export_blocked
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("locale", ["fr", "de", "ja", "xx", "EN", "en-US"])
def test_research_notes_export_blocked_rejects_unsupported(locale: str) -> None:
    from atlas.snapshot_input.render import render_research_notes_export_blocked
    with pytest.raises(ValueError):
        render_research_notes_export_blocked("reason", locale=locale)


# ---------------------------------------------------------------------------
# Snapshot renderer: render_company_facts_export_success
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("locale", _UNSUPPORTED_LOCALES)
def test_company_facts_export_success_rejects_unsupported(locale: str) -> None:
    from atlas.snapshot_input.render import render_company_facts_export_success
    with pytest.raises(ValueError):
        render_company_facts_export_success("ASML", "/tmp/f.json", locale=locale)


# ---------------------------------------------------------------------------
# Snapshot renderer: render_company_facts_export_blocked
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("locale", ["fr", "de", "ja", "xx", "EN", "en-US"])
def test_company_facts_export_blocked_rejects_unsupported(locale: str) -> None:
    from atlas.snapshot_input.render import render_company_facts_export_blocked
    with pytest.raises(ValueError):
        render_company_facts_export_blocked("reason", locale=locale)


# ---------------------------------------------------------------------------
# Snapshot renderers en and sv still pass after all unsupported checks
# ---------------------------------------------------------------------------

def test_snapshot_validation_en_still_passes() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    out = render_snapshot_draft_validation(_load_draft(), locale="en")
    assert "Snapshot Draft Validation" in out


def test_snapshot_validation_sv_still_passes() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    out = render_snapshot_draft_validation(_load_draft(), locale="sv")
    assert "Validering av Snapshot Draft" in out


def test_snapshot_review_en_still_passes() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_review
    out = render_snapshot_draft_review(_load_draft(), locale="en")
    assert "Snapshot Draft Review" in out


def test_snapshot_review_sv_still_passes() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_review
    out = render_snapshot_draft_review(_load_draft(), locale="sv")
    assert "Granskning av Snapshot Draft" in out


# ---------------------------------------------------------------------------
# CLI preservation
# ---------------------------------------------------------------------------

def test_cli_weekly_review_output_english() -> None:
    result = _atlas_cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-05",
    )
    assert result.returncode == 0, result.stderr
    assert "Atlas Weekly Investment Review" in result.stdout
    assert "Atlas veckovis investeringsgranskning" not in result.stdout


def test_cli_snapshot_validate_output_english() -> None:
    result = _atlas_cli("snapshot", "validate", str(_DRAFT_RESEARCH))
    assert result.returncode == 0, result.stderr
    assert "Snapshot Draft Validation" in result.stdout
    assert "Validering av Snapshot Draft" not in result.stdout


def test_cli_help_no_language_option() -> None:
    result = _atlas_cli("--help")
    assert "--language" not in (result.stdout + result.stderr)


# ---------------------------------------------------------------------------
# Infrastructure: no gettext, no locale detection, no providers
# ---------------------------------------------------------------------------

def test_no_gettext_import_in_locale_support() -> None:
    assert "import gettext" not in LOCALE_SUPPORT.read_text(encoding="utf-8")


def test_no_gettext_in_wr_render() -> None:
    assert "gettext" not in WR_RENDER.read_text(encoding="utf-8")


def test_no_gettext_in_sn_render() -> None:
    assert "gettext" not in SN_RENDER.read_text(encoding="utf-8")


def test_no_locale_detection_in_locale_support() -> None:
    source = LOCALE_SUPPORT.read_text(encoding="utf-8")
    assert "import locale" not in source
    assert "locale.getlocale" not in source


def test_no_translation_catalogs() -> None:
    import atlas
    assert not any(Path(atlas.__file__).parent.glob("*.po"))
    assert not any(Path(atlas.__file__).parent.glob("*.mo"))


def test_no_provider_imports_in_locale_support() -> None:
    source = LOCALE_SUPPORT.read_text(encoding="utf-8")
    for term in ("requests", "urllib", "httpx", "aiohttp"):
        assert term not in source


# ---------------------------------------------------------------------------
# Readiness checklist: B13 DONE, B14 OPEN
# ---------------------------------------------------------------------------

def test_checklist_b13_done() -> None:
    content = CHECKLIST.read_text(encoding="utf-8")
    lines = [l for l in content.splitlines() if "B13" in l]
    assert any("DONE" in l for l in lines), (
        f"Expected B13 DONE in checklist. Lines: {lines}"
    )


def test_checklist_b14_open() -> None:
    content = CHECKLIST.read_text(encoding="utf-8")
    lines = [l for l in content.splitlines() if "B14" in l]
    assert any("OPEN" in l for l in lines)


def test_checklist_criteria_count_13_of_14() -> None:
    content = CHECKLIST.read_text(encoding="utf-8")
    assert "13 of 14" in content

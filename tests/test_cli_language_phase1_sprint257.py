"""Sprint 257 — Phase 1 CLI language option tests.

Verifies that --language {en,sv} is available on atlas weekly-review,
atlas snapshot validate, and atlas snapshot review; that default and
--language en output remains English; that --language sv renders Swedish
Atlas-generated display strings; that unsupported values fail clearly; and
that deferred commands (confirm, reject, export-*) do not expose --language.

No automatic language detection. No gettext. Supported locales remain en/sv.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

_PORTFOLIO = Path("examples/weekly_review/portfolio.json")
_WATCHLIST = Path("examples/weekly_review/watchlist.json")
_DRAFT_RESEARCH = Path("examples/snapshot_drafts/research_notes_snapshot.json")
_DRAFT_PORTFOLIO = Path("examples/snapshot_drafts/portfolio_snapshot.json")

LOCALE_SUPPORT = Path("atlas/locale_support.py")
WR_RENDER = Path("atlas/weekly_review/render.py")
SN_RENDER = Path("atlas/snapshot_input/render.py")
CLI_MAIN = Path("atlas/cli/main.py")


def _cli(*args: str) -> subprocess.CompletedProcess:
    atlas_bin = str(Path(".venv/bin/atlas").resolve())
    return subprocess.run([atlas_bin, *args], capture_output=True, text=True)


_UNSUPPORTED = ["fr", "de", "EN", "SV", "en-US", "sv-SE", "xx"]


# ---------------------------------------------------------------------------
# weekly-review: --language in help
# ---------------------------------------------------------------------------

def test_weekly_review_help_includes_language() -> None:
    r = _cli("weekly-review", "--help")
    assert "--language" in (r.stdout + r.stderr)


# ---------------------------------------------------------------------------
# weekly-review: default and --language en remain English
# ---------------------------------------------------------------------------

def test_weekly_review_default_english() -> None:
    r = _cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-05",
    )
    assert r.returncode == 0, r.stderr
    assert "Atlas Weekly Investment Review" in r.stdout
    assert "Atlas veckovis investeringsgranskning" not in r.stdout


def test_weekly_review_language_en_equals_default() -> None:
    base = _cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-05",
    )
    with_en = _cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-05",
        "--language", "en",
    )
    assert base.returncode == 0
    assert with_en.returncode == 0
    assert base.stdout == with_en.stdout


# ---------------------------------------------------------------------------
# weekly-review: --language sv renders Swedish
# ---------------------------------------------------------------------------

def test_weekly_review_language_sv_swedish_title() -> None:
    r = _cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-05",
        "--language", "sv",
    )
    assert r.returncode == 0, r.stderr
    assert "Atlas veckovis investeringsgranskning" in r.stdout


def test_weekly_review_language_sv_section_title() -> None:
    r = _cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-05",
        "--language", "sv",
    )
    assert r.returncode == 0, r.stderr
    assert "Granskningens omfattning" in r.stdout


def test_weekly_review_language_sv_disclaimer() -> None:
    r = _cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-05",
        "--language", "sv",
    )
    assert r.returncode == 0, r.stderr
    # Join lines to handle Rich terminal line-wrapping
    joined = r.stdout.replace("\n", " ")
    assert "deterministisk" in joined
    assert "utan" in joined
    assert "rekommendationer" in joined


def test_weekly_review_language_sv_no_english_title() -> None:
    r = _cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-05",
        "--language", "sv",
    )
    assert r.returncode == 0, r.stderr
    assert "Atlas Weekly Investment Review" not in r.stdout


def test_weekly_review_language_sv_differs_from_en() -> None:
    en = _cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-05",
        "--language", "en",
    )
    sv = _cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-05",
        "--language", "sv",
    )
    assert en.stdout != sv.stdout


# ---------------------------------------------------------------------------
# weekly-review: --language sv preserves canonical values
# ---------------------------------------------------------------------------

def test_weekly_review_sv_preserves_warning_codes() -> None:
    import re
    en = _cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-05",
        "--language", "en",
    )
    sv = _cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-05",
        "--language", "sv",
    )
    en_codes = sorted(re.findall(r'\[([a-z][a-z_]+)\]', en.stdout))
    sv_codes = sorted(re.findall(r'\[([a-z][a-z_]+)\]', sv.stdout))
    assert en_codes == sv_codes, (
        f"Warning codes differ.\nen: {en_codes}\nsv: {sv_codes}"
    )


def test_weekly_review_sv_preserves_ticker_msft() -> None:
    en = _cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-05",
        "--language", "en",
    )
    sv = _cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-05",
        "--language", "sv",
    )
    if "MSFT" in en.stdout:
        assert "MSFT" in sv.stdout
    if "ASML" in en.stdout:
        assert "ASML" in sv.stdout


# ---------------------------------------------------------------------------
# weekly-review: --language sv preserves user-provided content
# ---------------------------------------------------------------------------

def test_weekly_review_sv_preserves_watchlist_reason() -> None:
    import json
    sv = _cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-05",
        "--language", "sv",
    )
    en = _cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-05",
        "--language", "en",
    )
    wl = json.loads(_WATCHLIST.read_text(encoding="utf-8"))
    for item in wl.get("items", []):
        reason = item.get("reason", "")
        if reason and reason in en.stdout:
            assert reason in sv.stdout, (
                f"Watchlist reason {reason!r} missing from --language sv output"
            )


# ---------------------------------------------------------------------------
# weekly-review: unsupported --language fails
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("lang", _UNSUPPORTED)
def test_weekly_review_unsupported_language_nonzero(lang: str) -> None:
    r = _cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-05",
        "--language", lang,
    )
    assert r.returncode != 0, (
        f"Expected non-zero exit for --language {lang!r}, got 0"
    )


def test_weekly_review_unsupported_language_no_partial_output() -> None:
    r = _cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-05",
        "--language", "fr",
    )
    assert r.returncode != 0
    assert "Atlas Weekly Investment Review" not in r.stdout
    assert "Atlas veckovis investeringsgranskning" not in r.stdout


def test_weekly_review_unsupported_language_error_names_value() -> None:
    r = _cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-05",
        "--language", "fr",
    )
    output = r.stdout + r.stderr
    assert "fr" in output


def test_weekly_review_unsupported_language_error_names_supported() -> None:
    r = _cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-05",
        "--language", "fr",
    )
    output = r.stdout + r.stderr
    assert "en" in output
    assert "sv" in output


# ---------------------------------------------------------------------------
# snapshot validate: --language in help
# ---------------------------------------------------------------------------

def test_snapshot_validate_help_includes_language() -> None:
    r = _cli("snapshot", "validate", "--help")
    assert "--language" in (r.stdout + r.stderr)


# ---------------------------------------------------------------------------
# snapshot validate: default and --language en remain English
# ---------------------------------------------------------------------------

def test_snapshot_validate_default_english() -> None:
    r = _cli("snapshot", "validate", str(_DRAFT_RESEARCH))
    assert r.returncode == 0, r.stderr
    assert "Snapshot Draft Validation" in r.stdout
    assert "Validering av Snapshot Draft" not in r.stdout


def test_snapshot_validate_language_en_equals_default() -> None:
    base = _cli("snapshot", "validate", str(_DRAFT_RESEARCH))
    with_en = _cli("snapshot", "validate", str(_DRAFT_RESEARCH), "--language", "en")
    assert base.returncode == 0
    assert with_en.returncode == 0
    assert base.stdout == with_en.stdout


# ---------------------------------------------------------------------------
# snapshot validate: --language sv renders Swedish
# ---------------------------------------------------------------------------

def test_snapshot_validate_sv_swedish_heading() -> None:
    r = _cli("snapshot", "validate", str(_DRAFT_RESEARCH), "--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Validering av Snapshot Draft" in r.stdout


def test_snapshot_validate_sv_safety_boundary() -> None:
    r = _cli("snapshot", "validate", str(_DRAFT_RESEARCH), "--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Säkerhetsgräns" in r.stdout


def test_snapshot_validate_sv_no_english_heading() -> None:
    r = _cli("snapshot", "validate", str(_DRAFT_RESEARCH), "--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Snapshot Draft Validation" not in r.stdout


def test_snapshot_validate_sv_preserves_snapshot_type() -> None:
    r = _cli("snapshot", "validate", str(_DRAFT_RESEARCH), "--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "research_notes_snapshot" in r.stdout


def test_snapshot_validate_sv_preserves_confidence() -> None:
    r = _cli("snapshot", "validate", str(_DRAFT_RESEARCH), "--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "high" in r.stdout


def test_snapshot_validate_sv_preserves_snapshot_notes() -> None:
    r = _cli("snapshot", "validate", str(_DRAFT_RESEARCH), "--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Draft created from user-written research notes" in r.stdout


# ---------------------------------------------------------------------------
# snapshot validate: unsupported --language fails
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("lang", _UNSUPPORTED)
def test_snapshot_validate_unsupported_language_nonzero(lang: str) -> None:
    r = _cli("snapshot", "validate", str(_DRAFT_RESEARCH), "--language", lang)
    assert r.returncode != 0, (
        f"Expected non-zero exit for --language {lang!r}, got 0"
    )


def test_snapshot_validate_unsupported_language_no_partial_output() -> None:
    r = _cli("snapshot", "validate", str(_DRAFT_RESEARCH), "--language", "fr")
    assert r.returncode != 0
    assert "Snapshot Draft Validation" not in r.stdout
    assert "Validering av Snapshot Draft" not in r.stdout


def test_snapshot_validate_unsupported_language_error_names_value() -> None:
    r = _cli("snapshot", "validate", str(_DRAFT_RESEARCH), "--language", "de")
    output = r.stdout + r.stderr
    assert "de" in output


# ---------------------------------------------------------------------------
# snapshot review: --language in help
# ---------------------------------------------------------------------------

def test_snapshot_review_help_includes_language() -> None:
    r = _cli("snapshot", "review", "--help")
    assert "--language" in (r.stdout + r.stderr)


# ---------------------------------------------------------------------------
# snapshot review: default and --language en remain English
# ---------------------------------------------------------------------------

def test_snapshot_review_default_english() -> None:
    r = _cli("snapshot", "review", str(_DRAFT_RESEARCH))
    assert r.returncode == 0, r.stderr
    assert "Snapshot Draft Review" in r.stdout
    assert "Granskning av Snapshot Draft" not in r.stdout


def test_snapshot_review_language_en_equals_default() -> None:
    base = _cli("snapshot", "review", str(_DRAFT_RESEARCH))
    with_en = _cli("snapshot", "review", str(_DRAFT_RESEARCH), "--language", "en")
    assert base.returncode == 0
    assert with_en.returncode == 0
    assert base.stdout == with_en.stdout


# ---------------------------------------------------------------------------
# snapshot review: --language sv renders Swedish
# ---------------------------------------------------------------------------

def test_snapshot_review_sv_swedish_heading() -> None:
    r = _cli("snapshot", "review", str(_DRAFT_RESEARCH), "--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Granskning av Snapshot Draft" in r.stdout


def test_snapshot_review_sv_safety_boundary() -> None:
    r = _cli("snapshot", "review", str(_DRAFT_RESEARCH), "--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Säkerhetsgräns" in r.stdout


def test_snapshot_review_sv_no_english_heading() -> None:
    r = _cli("snapshot", "review", str(_DRAFT_RESEARCH), "--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Snapshot Draft Review" not in r.stdout


def test_snapshot_review_sv_preserves_snapshot_type() -> None:
    r = _cli("snapshot", "review", str(_DRAFT_RESEARCH), "--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "research_notes_snapshot" in r.stdout


def test_snapshot_review_sv_preserves_confirmation_status() -> None:
    r = _cli("snapshot", "review", str(_DRAFT_RESEARCH), "--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "draft" in r.stdout


def test_snapshot_review_sv_preserves_file_path() -> None:
    r = _cli("snapshot", "review", str(_DRAFT_RESEARCH), "--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "my_review/research_notes/ASML/notes.md" in r.stdout


def test_snapshot_review_sv_preserves_source_reference() -> None:
    r = _cli("snapshot", "review", str(_DRAFT_RESEARCH), "--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "my_notes/asml_notes_2026.md" in r.stdout


# ---------------------------------------------------------------------------
# snapshot review: unsupported --language fails
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("lang", _UNSUPPORTED)
def test_snapshot_review_unsupported_language_nonzero(lang: str) -> None:
    r = _cli("snapshot", "review", str(_DRAFT_RESEARCH), "--language", lang)
    assert r.returncode != 0, (
        f"Expected non-zero exit for --language {lang!r}, got 0"
    )


def test_snapshot_review_unsupported_language_no_partial_output() -> None:
    r = _cli("snapshot", "review", str(_DRAFT_RESEARCH), "--language", "fr")
    assert r.returncode != 0
    assert "Snapshot Draft Review" not in r.stdout
    assert "Granskning av Snapshot Draft" not in r.stdout


def test_snapshot_review_unsupported_language_error_names_supported() -> None:
    r = _cli("snapshot", "review", str(_DRAFT_RESEARCH), "--language", "ja")
    output = r.stdout + r.stderr
    assert "en" in output
    assert "sv" in output


# ---------------------------------------------------------------------------
# Deferred commands must not expose --language
# ---------------------------------------------------------------------------

def test_snapshot_confirm_help_no_language() -> None:
    r = _cli("snapshot", "confirm", "--help")
    assert "--language" not in (r.stdout + r.stderr)


def test_snapshot_reject_help_no_language() -> None:
    r = _cli("snapshot", "reject", "--help")
    assert "--language" not in (r.stdout + r.stderr)


def test_snapshot_export_research_notes_help_no_language() -> None:
    r = _cli("snapshot", "export-research-notes", "--help")
    assert "--language" not in (r.stdout + r.stderr)


def test_snapshot_export_company_facts_help_no_language() -> None:
    r = _cli("snapshot", "export-company-facts", "--help")
    assert "--language" not in (r.stdout + r.stderr)


# ---------------------------------------------------------------------------
# Infrastructure unchanged
# ---------------------------------------------------------------------------

def test_no_gettext_import_in_cli() -> None:
    assert "import gettext" not in CLI_MAIN.read_text(encoding="utf-8")


def test_no_locale_detection_in_cli() -> None:
    source = CLI_MAIN.read_text(encoding="utf-8")
    assert "locale.getlocale" not in source
    assert "import locale\n" not in source


def test_no_gettext_import_in_locale_support() -> None:
    assert "import gettext" not in LOCALE_SUPPORT.read_text(encoding="utf-8")


def test_supported_locales_still_en_sv() -> None:
    from atlas.locale_support import _SUPPORTED_LOCALES
    assert _SUPPORTED_LOCALES == frozenset({"en", "sv"})


def test_no_translation_catalogs() -> None:
    import atlas
    assert not any(Path(atlas.__file__).parent.glob("*.po"))
    assert not any(Path(atlas.__file__).parent.glob("*.mo"))


def test_no_provider_imports_in_locale_support() -> None:
    source = LOCALE_SUPPORT.read_text(encoding="utf-8")
    for term in ("requests", "urllib", "httpx", "aiohttp"):
        assert term not in source

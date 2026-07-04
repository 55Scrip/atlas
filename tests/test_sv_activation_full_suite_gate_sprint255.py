"""Sprint 255 — sv activation full-suite gate.

Release gate confirming Swedish internal activation is complete across all 14
blocking criteria. This file is not a duplicate of prior sprint tests — it is
a compact gate that verifies the activation artifacts exist and that the
essential safety invariants still hold together.

Swedish remains direct-renderer/internal only.
CLI remains English. No --language option exists.
B1–B14 are DONE. 14 of 14 blocking criteria satisfied.
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
LOCALE_SUPPORT = Path("atlas/locale_support.py")
WR_RENDER = Path("atlas/weekly_review/render.py")
SN_RENDER = Path("atlas/snapshot_input/render.py")
CLI_MAIN = Path("atlas/cli/main.py")


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


# ---------------------------------------------------------------------------
# Readiness checklist: B1–B14 all DONE
# ---------------------------------------------------------------------------

def test_checklist_exists() -> None:
    assert CHECKLIST.exists()


@pytest.mark.parametrize("criterion", [
    "B1", "B2", "B3", "B4", "B5", "B6", "B7",
    "B8", "B9", "B10", "B11", "B12", "B13", "B14",
])
def test_checklist_criterion_done(criterion: str) -> None:
    content = CHECKLIST.read_text(encoding="utf-8")
    lines = [l for l in content.splitlines() if criterion in l]
    assert any("DONE" in l for l in lines), (
        f"Expected {criterion} DONE in checklist. Lines: {lines}"
    )


def test_checklist_14_of_14_satisfied() -> None:
    content = CHECKLIST.read_text(encoding="utf-8")
    assert "14 of 14" in content


# ---------------------------------------------------------------------------
# Prior sprint test matrix files exist
# ---------------------------------------------------------------------------

_PRIOR_TEST_FILES = [
    "tests/test_swedish_safe_language_guardrails_sprint247.py",
    "tests/test_swedish_localization_readiness_checklist_sprint248.py",
    "tests/test_swedish_display_string_constants_sprint249.py",
    "tests/test_swedish_renderer_dispatch_sprint250.py",
    "tests/test_swedish_locale_activation_sprint251.py",
    "tests/test_swedish_output_matrix_sprint252.py",
    "tests/test_swedish_canonical_passthrough_sprint253.py",
    "tests/test_unsupported_locale_regression_sprint254.py",
]


@pytest.mark.parametrize("path", _PRIOR_TEST_FILES)
def test_prior_sprint_test_file_exists(path: str) -> None:
    assert Path(path).exists(), f"Prior sprint test file missing: {path}"


# ---------------------------------------------------------------------------
# Locale support: supported locales are exactly en and sv
# ---------------------------------------------------------------------------

def test_supported_locale_en() -> None:
    from atlas.locale_support import SUPPORTED_LOCALE_EN
    assert SUPPORTED_LOCALE_EN == "en"


def test_supported_locale_sv() -> None:
    from atlas.locale_support import SUPPORTED_LOCALE_SV
    assert SUPPORTED_LOCALE_SV == "sv"


def test_supported_locales_set_exactly_en_sv() -> None:
    from atlas.locale_support import _SUPPORTED_LOCALES
    assert _SUPPORTED_LOCALES == frozenset({"en", "sv"})


def test_ensure_supported_locale_en_passes() -> None:
    from atlas.locale_support import ensure_supported_locale
    ensure_supported_locale("en")


def test_ensure_supported_locale_sv_passes() -> None:
    from atlas.locale_support import ensure_supported_locale
    ensure_supported_locale("sv")


def test_ensure_supported_locale_fr_raises() -> None:
    from atlas.locale_support import ensure_supported_locale
    with pytest.raises(ValueError):
        ensure_supported_locale("fr")


def test_ensure_supported_locale_en_us_raises() -> None:
    from atlas.locale_support import ensure_supported_locale
    with pytest.raises(ValueError):
        ensure_supported_locale("en-US")


def test_ensure_supported_locale_sv_se_raises() -> None:
    from atlas.locale_support import ensure_supported_locale
    with pytest.raises(ValueError):
        ensure_supported_locale("sv-SE")


# ---------------------------------------------------------------------------
# Direct Swedish rendering smoke tests
# ---------------------------------------------------------------------------

def test_sv_weekly_review_title() -> None:
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_wr_result(), locale="sv")
    assert "Atlas veckovis investeringsgranskning" in out


def test_sv_weekly_review_section_title() -> None:
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_wr_result(), locale="sv")
    assert "Granskningens omfattning" in out


def test_sv_weekly_review_disclaimer() -> None:
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_wr_result(), locale="sv")
    assert "deterministisk" in out
    assert "utan rekommendationer" in out


def test_sv_snapshot_review_heading() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_review
    out = render_snapshot_draft_review(_load_draft(), locale="sv")
    assert "Granskning av Snapshot Draft" in out


def test_sv_snapshot_validation_heading() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    out = render_snapshot_draft_validation(_load_draft(), locale="sv")
    assert "Validering av Snapshot Draft" in out


def test_sv_snapshot_safety_boundary() -> None:
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    out = render_snapshot_draft_validation(_load_draft(), locale="sv")
    assert "Säkerhetsgräns" in out


# ---------------------------------------------------------------------------
# English / CLI preservation
# ---------------------------------------------------------------------------

def test_en_weekly_review_title() -> None:
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_wr_result())
    assert "Atlas Weekly Investment Review" in out
    assert "Atlas veckovis investeringsgranskning" not in out


def test_en_explicit_weekly_review_unchanged() -> None:
    from atlas.weekly_review.render import render_weekly_review
    result = _load_wr_result()
    assert render_weekly_review(result) == render_weekly_review(result, locale="en")


def test_cli_weekly_review_english() -> None:
    result = _atlas_cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-05",
    )
    assert result.returncode == 0, result.stderr
    assert "Atlas Weekly Investment Review" in result.stdout
    assert "Atlas veckovis investeringsgranskning" not in result.stdout


def test_cli_snapshot_validate_english() -> None:
    result = _atlas_cli("snapshot", "validate", str(_DRAFT_RESEARCH))
    assert result.returncode == 0, result.stderr
    assert "Snapshot Draft Validation" in result.stdout
    assert "Validering av Snapshot Draft" not in result.stdout


def test_cli_no_language_option() -> None:
    result = _atlas_cli("--help")
    assert "--language" not in (result.stdout + result.stderr)


def test_cli_source_no_locale_sv_call() -> None:
    source = CLI_MAIN.read_text(encoding="utf-8")
    assert 'locale="sv"' not in source
    assert "locale='sv'" not in source


# ---------------------------------------------------------------------------
# Safety infrastructure
# ---------------------------------------------------------------------------

def test_no_gettext_import_in_locale_support() -> None:
    assert "import gettext" not in LOCALE_SUPPORT.read_text(encoding="utf-8")


def test_no_gettext_import_in_wr_render() -> None:
    assert "import gettext" not in WR_RENDER.read_text(encoding="utf-8")


def test_no_gettext_import_in_sn_render() -> None:
    assert "import gettext" not in SN_RENDER.read_text(encoding="utf-8")


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
        assert term not in source, f"Provider import {term!r} found in locale_support.py"


def test_no_extra_supported_locale_in_source() -> None:
    source = LOCALE_SUPPORT.read_text(encoding="utf-8")
    for lang in ("fr", "de", "ja", "no", "da", "fi", "es"):
        assert f'"{lang}"' not in source, (
            f"Unexpected locale {lang!r} found in locale_support.py"
        )


# ---------------------------------------------------------------------------
# Readiness checklist: B14 DONE (final state)
# ---------------------------------------------------------------------------

def test_checklist_b14_done() -> None:
    content = CHECKLIST.read_text(encoding="utf-8")
    lines = [l for l in content.splitlines() if "B14" in l]
    assert any("DONE" in l for l in lines), (
        f"Expected B14 DONE in checklist. Lines: {lines}"
    )

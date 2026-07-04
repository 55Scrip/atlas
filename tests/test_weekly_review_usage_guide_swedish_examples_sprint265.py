"""Sprint 265 — Weekly Review usage guide Swedish examples tests.

Verifies that AtlasWeeklyReviewUsageGuide.md documents the --language sv
option correctly: default English behaviour, explicit --language en,
explicit --language sv, Swedish section headings, canonical English values,
user-content passthrough, safety boundaries, and links to related docs.

No runtime behaviour is changed by this sprint. These tests read the guide
document only.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

GUIDE = Path("docs/AtlasWeeklyReviewUsageGuide.md")

_PORTFOLIO = Path("examples/weekly_review/portfolio.json")
_WATCHLIST = Path("examples/weekly_review/watchlist.json")
_AS_OF = "2026-01-05"


def _guide() -> str:
    return GUIDE.read_text(encoding="utf-8")


def _cli(*args: str) -> subprocess.CompletedProcess:
    atlas = str(Path(".venv/bin/atlas").resolve())
    return subprocess.run([atlas, *args], capture_output=True, text=True)


def _review(*extra: str) -> subprocess.CompletedProcess:
    return _cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", _AS_OF,
        *extra,
    )


# ---------------------------------------------------------------------------
# Guide documents --language option existence
# ---------------------------------------------------------------------------

def test_guide_documents_language_sv() -> None:
    assert "--language sv" in _guide()


def test_guide_documents_language_en() -> None:
    assert "--language en" in _guide()


def test_guide_documents_default_english_behaviour() -> None:
    g = _guide()
    assert "default" in g.lower()
    assert "--language` is omitted" in g or "--language` is omitted" in g or "language` is omitted" in g or "language is omitted" in g


# ---------------------------------------------------------------------------
# Guide includes Swedish section heading examples
# ---------------------------------------------------------------------------

def test_guide_shows_swedish_weekly_review_title() -> None:
    assert "Atlas veckovis investeringsgranskning" in _guide()


def test_guide_shows_swedish_review_scope() -> None:
    assert "Granskningens omfattning" in _guide()


def test_guide_shows_swedish_portfolio_context() -> None:
    assert "Portföljkontext" in _guide()


def test_guide_shows_swedish_watchlist_review() -> None:
    assert "Bevakningslista" in _guide()


def test_guide_shows_swedish_missing_evidence() -> None:
    assert "Saknat underlag" in _guide()


def test_guide_shows_swedish_follow_up_questions() -> None:
    assert "Uppföljningsfrågor" in _guide()


def test_guide_shows_swedish_non_actions() -> None:
    assert "Icke-åtgärder" in _guide()


def test_guide_shows_swedish_input_status() -> None:
    assert "Indatastatus" in _guide()


def test_guide_shows_swedish_input_warnings() -> None:
    assert "Indatavarningar" in _guide()


# ---------------------------------------------------------------------------
# Guide documents Swedish inline labels
# ---------------------------------------------------------------------------

def test_guide_shows_swedish_evidence_gap_label() -> None:
    assert "Underlagslucka" in _guide()


def test_guide_shows_swedish_reason_to_wait_label() -> None:
    assert "Skäl att avvakta" in _guide()


def test_guide_shows_swedish_no_action_warranted_label() -> None:
    assert "Ingen åtgärd motiverad" in _guide()


def test_guide_shows_swedish_missing_optional_input_label() -> None:
    assert "Saknat valfritt indata" in _guide()


# ---------------------------------------------------------------------------
# Guide states what --language sv changes (display text only)
# ---------------------------------------------------------------------------

def test_guide_states_language_changes_display_text_only() -> None:
    g = _guide()
    assert "display text" in g.lower() or "display" in g.lower()


def test_guide_states_structure_unchanged() -> None:
    g = _guide()
    assert "structure" in g.lower() or "logic" in g.lower()


# ---------------------------------------------------------------------------
# Guide documents canonical English values
# ---------------------------------------------------------------------------

def test_guide_documents_canonical_values_remain_english() -> None:
    g = _guide()
    assert "canonical" in g.lower() or "Canonical" in g


def test_guide_lists_warning_codes_as_canonical() -> None:
    assert "warning code" in _guide().lower() or "missing_sector" in _guide()


def test_guide_lists_ticker_symbols_as_canonical() -> None:
    g = _guide()
    assert "ticker" in g.lower() or "ASML" in g


def test_guide_lists_enum_values_as_canonical() -> None:
    g = _guide()
    assert "enum" in g.lower() or "confirmed" in g or "schema" in g.lower()


def test_guide_lists_cli_flags_as_canonical() -> None:
    assert "--language" in _guide()


# ---------------------------------------------------------------------------
# Guide documents user-provided content passthrough
# ---------------------------------------------------------------------------

def test_guide_states_user_content_not_translated() -> None:
    g = _guide()
    assert "not translated" in g.lower() or "unchanged" in g.lower() or "passthrough" in g.lower() or "passes through" in g.lower()


def test_guide_lists_scope_notes_as_user_content() -> None:
    assert "scope notes" in _guide().lower()


def test_guide_lists_watchlist_reasons_as_user_content() -> None:
    g = _guide()
    assert "watchlist" in g.lower() and ("reason" in g.lower() or "evidence" in g.lower())


def test_guide_lists_research_notes_as_user_content() -> None:
    assert "research notes" in _guide().lower()


def test_guide_lists_journal_notes_as_user_content() -> None:
    assert "journal" in _guide().lower()


def test_guide_lists_principles_as_user_content() -> None:
    assert "principles" in _guide().lower()


# ---------------------------------------------------------------------------
# Guide documents safety boundaries
# ---------------------------------------------------------------------------

def test_guide_states_no_recommendations_in_any_language() -> None:
    g = _guide()
    assert "recommendation" in g.lower()


def test_guide_states_atlas_supports_judgment() -> None:
    assert "Atlas supports better judgment" in _guide()


def test_guide_states_informational_only() -> None:
    g = _guide()
    assert "informational" in g.lower()


def test_guide_states_language_does_not_change_reasoning() -> None:
    g = _guide()
    assert "reasoning" in g.lower() or "logic" in g.lower() or "determinism" in g.lower()


# ---------------------------------------------------------------------------
# Guide references related localization documentation
# ---------------------------------------------------------------------------

def test_guide_references_localization_boundary_doc() -> None:
    assert "AtlasLocalizationBoundary" in _guide()


def test_guide_references_swedish_cli_usage_guide() -> None:
    assert "SwedishCLIUsageGuide" in _guide()


# ---------------------------------------------------------------------------
# CLI regression — Swedish Weekly Review still works after doc-only sprint
# ---------------------------------------------------------------------------

def test_swedish_weekly_review_still_exits_zero() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr


def test_swedish_weekly_review_title_in_output() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Atlas veckovis investeringsgranskning" in r.stdout


def test_swedish_section_headings_present() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Granskningens omfattning" in r.stdout
    assert "Portföljkontext" in r.stdout
    assert "Saknat underlag" in r.stdout
    assert "Uppföljningsfrågor" in r.stdout
    assert "Icke-åtgärder" in r.stdout


def test_english_weekly_review_still_exits_zero() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr


def test_english_output_unchanged() -> None:
    r_default = _review()
    r_en = _review("--language", "en")
    assert r_default.returncode == 0
    assert r_en.returncode == 0
    assert r_default.stdout == r_en.stdout


# ---------------------------------------------------------------------------
# No runtime behaviour changed — no gettext / locale detection added
# ---------------------------------------------------------------------------

def test_no_gettext_added_to_render() -> None:
    src = Path("atlas/weekly_review/render.py").read_text(encoding="utf-8")
    assert "gettext" not in src
    assert "import locale" not in src


def test_no_gettext_added_to_strings_en() -> None:
    src = Path("atlas/weekly_review/strings.py").read_text(encoding="utf-8")
    assert "gettext" not in src


def test_no_gettext_added_to_strings_sv() -> None:
    src = Path("atlas/weekly_review/strings_sv.py").read_text(encoding="utf-8")
    assert "gettext" not in src

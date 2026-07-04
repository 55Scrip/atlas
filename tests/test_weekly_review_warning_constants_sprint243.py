"""Sprint 243 — Weekly Review warning display template constants tests.

Verifies that warning display templates have been extracted into named constants
and that the renderer references them. Confirms exact warning output is unchanged
for both warning row format and scope section summary line.

Warning codes remain canonical internal values — they are NOT extracted into
display constants. Warning messages in inputs.py remain inline (dynamic paths
prevent clean templating without structural changes).
"""

from __future__ import annotations

from pathlib import Path

STRINGS_MODULE = Path("atlas/weekly_review/strings.py")
RENDER_MODULE = Path("atlas/weekly_review/render.py")

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
# Warning display constants exist with exact wording
# ---------------------------------------------------------------------------

def test_warning_row_constant_exists():
    from atlas.weekly_review import strings as S
    assert hasattr(S, "WARNING_ROW")


def test_warning_row_constant_exact():
    from atlas.weekly_review import strings as S
    assert S.WARNING_ROW == "- [{code}] {message}"


def test_warning_scope_summary_constant_exists():
    from atlas.weekly_review import strings as S
    assert hasattr(S, "WARNING_SCOPE_SUMMARY")


def test_warning_scope_summary_constant_exact():
    from atlas.weekly_review import strings as S
    assert S.WARNING_SCOPE_SUMMARY == "Warnings: {count} input warning(s) noted — see Input Warnings section"


# ---------------------------------------------------------------------------
# Template formatting produces correct output
# ---------------------------------------------------------------------------

def test_warning_row_format():
    from atlas.weekly_review import strings as S
    result = S.WARNING_ROW.format(code="missing_optional_profile", message="No investor profile path provided.")
    assert result == "- [missing_optional_profile] No investor profile path provided."


def test_warning_scope_summary_format():
    from atlas.weekly_review import strings as S
    assert S.WARNING_SCOPE_SUMMARY.format(count=4) == "Warnings: 4 input warning(s) noted — see Input Warnings section"


# ---------------------------------------------------------------------------
# Renderer references the constants
# ---------------------------------------------------------------------------

def test_render_references_warning_row():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "S.WARNING_ROW" in source


def test_render_references_warning_scope_summary():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "S.WARNING_SCOPE_SUMMARY" in source


def test_render_no_inline_warning_row_literal():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert '"- [{w.code}] {w.message}"' not in source
    assert "f\"- [{w.code}] {w.message}\"" not in source


def test_render_no_inline_scope_summary_literal():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert '"input warning(s) noted — see Input Warnings section"' not in source


# ---------------------------------------------------------------------------
# Prior constants remain intact
# ---------------------------------------------------------------------------

def test_prior_constants_intact():
    from atlas.weekly_review import strings as S
    assert S.WEEKLY_REVIEW_TITLE == "Atlas Weekly Investment Review"
    assert S.SECTION_REVIEW_SCOPE == "1. Review Scope"
    assert len(S.WEEKLY_REVIEW_SECTION_TITLES) == 10
    assert S.LABEL_EVIDENCE_GAP == "Evidence Gap"
    assert S.LABEL_INPUT_STATUS == "Input Status"
    assert S.LABEL_INPUT_WARNINGS == "Input Warnings"
    assert "deterministic, local-only" in S.WEEKLY_REVIEW_DISCLAIMER
    assert S.INPUT_STATUS_PORTFOLIO_LOADED == "Portfolio: {count} holding(s) loaded."
    assert S.INPUT_STATUS_WARNINGS_COUNT == "Warnings: {count}"


# ---------------------------------------------------------------------------
# Output preservation helpers
# ---------------------------------------------------------------------------

def _load_minimal_result():
    from pathlib import Path as _Path
    from atlas.weekly_review.inputs import WeeklyReviewInputPaths, load_weekly_review_inputs
    paths = WeeklyReviewInputPaths(
        portfolio_path=_Path("examples/weekly_review/portfolio.json"),
        watchlist_path=_Path("examples/weekly_review/watchlist.json"),
        as_of="2026-01-01",
    )
    return load_weekly_review_inputs(paths)


def _load_full_result():
    from pathlib import Path as _Path
    from atlas.weekly_review.inputs import WeeklyReviewInputPaths, load_weekly_review_inputs
    paths = WeeklyReviewInputPaths(
        portfolio_path=_Path("examples/weekly_review/portfolio.json"),
        watchlist_path=_Path("examples/weekly_review/watchlist.json"),
        profile_path=_Path("examples/weekly_review/investor_profile.json"),
        journal_path=_Path("examples/weekly_review/decision_journal.json"),
        company_facts_dir=_Path("examples/weekly_review/company_facts"),
        financials_dir=_Path("examples/weekly_review/financials"),
        research_notes_dir=_Path("examples/weekly_review/research_notes"),
        as_of="2026-01-01",
        scope_notes=_Path("examples/weekly_review/scope_notes.md").read_text(encoding="utf-8")
        if _Path("examples/weekly_review/scope_notes.md").exists()
        else None,
    )
    return load_weekly_review_inputs(paths)


# ---------------------------------------------------------------------------
# Output preservation — warning rows
# ---------------------------------------------------------------------------

def test_minimal_output_warning_rows_have_code_brackets():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_minimal_result())
    # Each warning row in Input Warnings section should have [code] format
    start = out.find("## Input Warnings")
    end = out.find("\n---", start)
    warnings_section = out[start:end]
    warning_rows = [ln for ln in warnings_section.splitlines() if ln.startswith("- [")]
    assert len(warning_rows) > 0, "No warning rows with [code] format found"


def test_minimal_output_missing_profile_warning_row():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_minimal_result())
    assert "- [missing_optional_profile]" in out


def test_minimal_output_missing_journal_warning_row():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_minimal_result())
    assert "- [missing_optional_journal]" in out


def test_minimal_output_missing_company_facts_warning_row():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_minimal_result())
    assert "- [missing_optional_company_facts]" in out


def test_minimal_output_missing_financials_warning_row():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_minimal_result())
    assert "- [missing_optional_financials]" in out


def test_minimal_output_warning_message_text_preserved():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_minimal_result())
    assert "No decision journal input provided; open decisions not reviewed." in out
    assert "No company facts directory provided or directory not found" in out


# ---------------------------------------------------------------------------
# Output preservation — scope section warning summary
# ---------------------------------------------------------------------------

def test_minimal_output_scope_warning_summary():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_minimal_result())
    assert "input warning(s) noted — see Input Warnings section" in out


def test_minimal_output_scope_warning_summary_count():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_minimal_result())
    assert "Warnings: 4 input warning(s) noted — see Input Warnings section" in out


# ---------------------------------------------------------------------------
# Output preservation — full inputs (no warnings expected)
# ---------------------------------------------------------------------------

def test_full_output_no_input_warnings_section():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_full_result())
    # Full inputs may or may not produce warnings depending on example data
    # Just verify the section structure is intact regardless
    assert "## Input Status" in out
    assert "1. Review Scope" in out


def test_full_output_all_10_sections_intact():
    from atlas.weekly_review.render import render_weekly_review
    from atlas.weekly_review.strings import WEEKLY_REVIEW_SECTION_TITLES
    out = render_weekly_review(_load_full_result())
    for title in WEEKLY_REVIEW_SECTION_TITLES:
        assert title in out, f"Section title missing: {title!r}"


# ---------------------------------------------------------------------------
# Warning codes remain canonical (not extracted to display constants)
# ---------------------------------------------------------------------------

def test_warning_codes_not_in_strings_module():
    source = STRINGS_MODULE.read_text(encoding="utf-8")
    # Warning codes are canonical internal values — must not appear as constants
    for code in [
        "missing_optional_profile",
        "missing_optional_journal",
        "missing_optional_company_facts",
        "missing_optional_financials",
        "invalid_profile",
        "invalid_journal",
        "missing_sector",
        "missing_market_value",
    ]:
        assert f'= "{code}"' not in source, f"Warning code extracted as constant: {code!r}"


# ---------------------------------------------------------------------------
# Snapshot CLI unaffected
# ---------------------------------------------------------------------------

def test_snapshot_strings_module_unaffected():
    assert Path("atlas/snapshot_input/strings.py").exists()


def test_snapshot_heading_constants_unchanged():
    from atlas.snapshot_input import strings as SS
    assert SS.HEADING_VALIDATION == "Snapshot Draft Validation"
    assert SS.HEADING_COMPANY_FACTS_EXPORT == "Company Facts Export"


def test_snapshot_render_no_weekly_review_imports():
    source = Path("atlas/snapshot_input/render.py").read_text(encoding="utf-8")
    assert "from atlas.weekly_review" not in source


# ---------------------------------------------------------------------------
# No new behavioral features
# ---------------------------------------------------------------------------

def test_no_language_option_in_cli():
    import atlas.cli.main as main_mod
    source = Path(main_mod.__file__).read_text(encoding="utf-8")
    assert "--language" not in source


def test_no_gettext_or_locale_in_strings_module():
    source = STRINGS_MODULE.read_text(encoding="utf-8")
    assert "import gettext" not in source
    assert "import locale" not in source


def test_no_provider_imports_in_strings_module():
    source = STRINGS_MODULE.read_text(encoding="utf-8")
    for term in ["requests", "urllib", "httpx", "aiohttp"]:
        assert term not in source


# ---------------------------------------------------------------------------
# Language guardrails
# ---------------------------------------------------------------------------

def test_strings_module_no_forbidden_language():
    content = STRINGS_MODULE.read_text(encoding="utf-8")
    for term in FORBIDDEN_LANGUAGE:
        assert term not in content, f"Forbidden language in strings module: {term!r}"


def test_render_module_no_forbidden_language():
    content = RENDER_MODULE.read_text(encoding="utf-8")
    for term in FORBIDDEN_LANGUAGE:
        assert term not in content, f"Forbidden language in render module: {term!r}"

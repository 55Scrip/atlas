"""Sprint 242 — Weekly Review input status message constants tests.

Verifies that _render_input_status message templates have been extracted into
named constants and that the renderer references them. Confirms exact output
wording is unchanged for both full-input and missing-input cases.
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
# Constants exist with exact wording
# ---------------------------------------------------------------------------

def test_input_status_portfolio_loaded_constant():
    from atlas.weekly_review import strings as S
    assert S.INPUT_STATUS_PORTFOLIO_LOADED == "Portfolio: {count} holding(s) loaded."


def test_input_status_watchlist_loaded_constant():
    from atlas.weekly_review import strings as S
    assert S.INPUT_STATUS_WATCHLIST_LOADED == "Watchlist: {count} item(s) loaded from '{name}'."


def test_input_status_investor_profile_available_constant():
    from atlas.weekly_review import strings as S
    assert S.INPUT_STATUS_INVESTOR_PROFILE_AVAILABLE == "Investor profile: Available"


def test_input_status_investor_profile_not_provided_constant():
    from atlas.weekly_review import strings as S
    assert S.INPUT_STATUS_INVESTOR_PROFILE_NOT_PROVIDED == "Investor profile: Not provided — default will be used."


def test_input_status_journal_loaded_constant():
    from atlas.weekly_review import strings as S
    assert S.INPUT_STATUS_JOURNAL_LOADED == "Decision journal: {count} entry/entries loaded."


def test_input_status_journal_not_provided_constant():
    from atlas.weekly_review import strings as S
    assert S.INPUT_STATUS_JOURNAL_NOT_PROVIDED == "Decision journal: Not provided."


def test_input_status_company_facts_available_constant():
    from atlas.weekly_review import strings as S
    assert S.INPUT_STATUS_COMPANY_FACTS_AVAILABLE == "Company facts: Available"


def test_input_status_company_facts_not_provided_constant():
    from atlas.weekly_review import strings as S
    assert S.INPUT_STATUS_COMPANY_FACTS_NOT_PROVIDED == "Company facts: Not provided — evidence gaps noted."


def test_input_status_financials_available_constant():
    from atlas.weekly_review import strings as S
    assert S.INPUT_STATUS_FINANCIALS_AVAILABLE == "Financials: Available"


def test_input_status_financials_not_provided_constant():
    from atlas.weekly_review import strings as S
    assert S.INPUT_STATUS_FINANCIALS_NOT_PROVIDED == "Financials: Not provided — evidence gaps noted."


def test_input_status_research_notes_loaded_constant():
    from atlas.weekly_review import strings as S
    assert S.INPUT_STATUS_RESEARCH_NOTES_LOADED == "Research notes: {count} ticker(s) with local notes."


def test_input_status_research_notes_not_provided_constant():
    from atlas.weekly_review import strings as S
    assert S.INPUT_STATUS_RESEARCH_NOTES_NOT_PROVIDED == "Research notes: Not provided."


def test_input_status_review_date_constant():
    from atlas.weekly_review import strings as S
    assert S.INPUT_STATUS_REVIEW_DATE == "Review date: {date}"


def test_input_status_warnings_count_constant():
    from atlas.weekly_review import strings as S
    assert S.INPUT_STATUS_WARNINGS_COUNT == "Warnings: {count}"


# ---------------------------------------------------------------------------
# Template formatting produces correct output
# ---------------------------------------------------------------------------

def test_portfolio_loaded_format():
    from atlas.weekly_review import strings as S
    assert S.INPUT_STATUS_PORTFOLIO_LOADED.format(count=3) == "Portfolio: 3 holding(s) loaded."


def test_watchlist_loaded_format():
    from atlas.weekly_review import strings as S
    result = S.INPUT_STATUS_WATCHLIST_LOADED.format(count=2, name="Core Research Watchlist")
    assert result == "Watchlist: 2 item(s) loaded from 'Core Research Watchlist'."


def test_journal_loaded_format():
    from atlas.weekly_review import strings as S
    assert S.INPUT_STATUS_JOURNAL_LOADED.format(count=1) == "Decision journal: 1 entry/entries loaded."


def test_research_notes_loaded_format():
    from atlas.weekly_review import strings as S
    assert S.INPUT_STATUS_RESEARCH_NOTES_LOADED.format(count=2) == "Research notes: 2 ticker(s) with local notes."


def test_review_date_format():
    from atlas.weekly_review import strings as S
    assert S.INPUT_STATUS_REVIEW_DATE.format(date="2026-01-01") == "Review date: 2026-01-01"


def test_warnings_count_format():
    from atlas.weekly_review import strings as S
    assert S.INPUT_STATUS_WARNINGS_COUNT.format(count=4) == "Warnings: 4"


# ---------------------------------------------------------------------------
# Sprint 239/240/241 constants still intact
# ---------------------------------------------------------------------------

def test_prior_constants_intact():
    from atlas.weekly_review import strings as S
    assert S.WEEKLY_REVIEW_TITLE == "Atlas Weekly Investment Review"
    assert S.SECTION_REVIEW_SCOPE == "1. Review Scope"
    assert S.SECTION_NON_ACTIONS_REASONS_TO_WAIT == "10. Non-Actions / Reasons to Wait"
    assert len(S.WEEKLY_REVIEW_SECTION_TITLES) == 10
    assert S.LABEL_EVIDENCE_GAP == "Evidence Gap"
    assert S.LABEL_INPUT_STATUS == "Input Status"
    assert S.LABEL_INPUT_WARNINGS == "Input Warnings"
    assert "deterministic, local-only" in S.WEEKLY_REVIEW_DISCLAIMER


# ---------------------------------------------------------------------------
# Renderer references constants
# ---------------------------------------------------------------------------

def test_render_references_portfolio_loaded():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "S.INPUT_STATUS_PORTFOLIO_LOADED" in source


def test_render_references_watchlist_loaded():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "S.INPUT_STATUS_WATCHLIST_LOADED" in source


def test_render_references_investor_profile_available():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "S.INPUT_STATUS_INVESTOR_PROFILE_AVAILABLE" in source


def test_render_references_investor_profile_not_provided():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "S.INPUT_STATUS_INVESTOR_PROFILE_NOT_PROVIDED" in source


def test_render_references_journal_loaded():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "S.INPUT_STATUS_JOURNAL_LOADED" in source


def test_render_references_company_facts():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "S.INPUT_STATUS_COMPANY_FACTS_AVAILABLE" in source
    assert "S.INPUT_STATUS_COMPANY_FACTS_NOT_PROVIDED" in source


def test_render_references_financials():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "S.INPUT_STATUS_FINANCIALS_AVAILABLE" in source
    assert "S.INPUT_STATUS_FINANCIALS_NOT_PROVIDED" in source


def test_render_references_research_notes():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "S.INPUT_STATUS_RESEARCH_NOTES_LOADED" in source
    assert "S.INPUT_STATUS_RESEARCH_NOTES_NOT_PROVIDED" in source


# ---------------------------------------------------------------------------
# Output preservation — full inputs
# ---------------------------------------------------------------------------

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


def _load_minimal_result():
    from pathlib import Path as _Path
    from atlas.weekly_review.inputs import WeeklyReviewInputPaths, load_weekly_review_inputs
    paths = WeeklyReviewInputPaths(
        portfolio_path=_Path("examples/weekly_review/portfolio.json"),
        watchlist_path=_Path("examples/weekly_review/watchlist.json"),
        as_of="2026-01-01",
    )
    return load_weekly_review_inputs(paths)


def test_full_output_portfolio_line():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_full_result())
    assert "- Portfolio: 3 holding(s) loaded." in out


def test_full_output_watchlist_line():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_full_result())
    assert "- Watchlist: 2 item(s) loaded from 'Core Research Watchlist'." in out


def test_full_output_investor_profile_available():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_full_result())
    assert "- Investor profile: Available" in out


def test_full_output_journal_loaded():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_full_result())
    assert "entry/entries loaded." in out


def test_full_output_company_facts_available():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_full_result())
    assert "- Company facts: Available" in out


def test_full_output_financials_available():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_full_result())
    assert "- Financials: Available" in out


def test_full_output_research_notes_loaded():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_full_result())
    assert "ticker(s) with local notes." in out


def test_full_output_review_date():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_full_result())
    assert "- Review date: 2026-01-01" in out


# ---------------------------------------------------------------------------
# Output preservation — missing optional inputs
# ---------------------------------------------------------------------------

def test_minimal_output_investor_profile_not_provided():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_minimal_result())
    assert "- Investor profile: Not provided — default will be used." in out


def test_minimal_output_journal_not_provided():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_minimal_result())
    assert "- Decision journal: Not provided." in out


def test_minimal_output_company_facts_not_provided():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_minimal_result())
    assert "- Company facts: Not provided — evidence gaps noted." in out


def test_minimal_output_financials_not_provided():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_minimal_result())
    assert "- Financials: Not provided — evidence gaps noted." in out


def test_minimal_output_research_notes_not_provided():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_minimal_result())
    assert "- Research notes: Not provided." in out


def test_minimal_output_warnings_count_line():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_minimal_result())
    assert "- Warnings:" in out


def test_minimal_output_input_warnings_heading():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_minimal_result())
    assert "## Input Warnings" in out


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

"""Sprint 241 — Weekly Review disclaimer constant tests.

Verifies that the Weekly Review disclaimer has been extracted into a named
constant and that the renderer references it. Confirms exact disclaimer text
and overall output structure are unchanged.
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

EXPECTED_DISCLAIMER = (
    "Atlas Weekly Investment Review — deterministic, local-only, no recommendations.\n"
    "Atlas supports better judgment. It does not replace it."
)


# ---------------------------------------------------------------------------
# Constant exists and has exact wording
# ---------------------------------------------------------------------------

def test_disclaimer_constant_exists():
    from atlas.weekly_review import strings as S
    assert hasattr(S, "WEEKLY_REVIEW_DISCLAIMER")


def test_disclaimer_constant_exact_text():
    from atlas.weekly_review import strings as S
    assert S.WEEKLY_REVIEW_DISCLAIMER == EXPECTED_DISCLAIMER


def test_disclaimer_first_line():
    from atlas.weekly_review import strings as S
    first_line = S.WEEKLY_REVIEW_DISCLAIMER.split("\n")[0]
    assert first_line == "Atlas Weekly Investment Review — deterministic, local-only, no recommendations."


def test_disclaimer_second_line():
    from atlas.weekly_review import strings as S
    second_line = S.WEEKLY_REVIEW_DISCLAIMER.split("\n")[1]
    assert second_line == "Atlas supports better judgment. It does not replace it."


def test_disclaimer_has_exactly_two_lines():
    from atlas.weekly_review import strings as S
    assert S.WEEKLY_REVIEW_DISCLAIMER.count("\n") == 1


# ---------------------------------------------------------------------------
# Renderer references the constant; inline definition removed
# ---------------------------------------------------------------------------

def test_render_module_references_disclaimer_constant():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "S.WEEKLY_REVIEW_DISCLAIMER" in source


def test_render_module_no_inline_disclaimer_definition():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "_DISCLAIMER =" not in source


def test_render_module_no_inline_disclaimer_text():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "deterministic, local-only, no recommendations" not in source


# ---------------------------------------------------------------------------
# Sprint 239 and 240 constants still intact
# ---------------------------------------------------------------------------

def test_weekly_review_title_intact():
    from atlas.weekly_review import strings as S
    assert S.WEEKLY_REVIEW_TITLE == "Atlas Weekly Investment Review"


def test_section_title_constants_intact():
    from atlas.weekly_review import strings as S
    assert S.SECTION_REVIEW_SCOPE == "1. Review Scope"
    assert S.SECTION_NON_ACTIONS_REASONS_TO_WAIT == "10. Non-Actions / Reasons to Wait"
    assert len(S.WEEKLY_REVIEW_SECTION_TITLES) == 10


def test_label_constants_intact():
    from atlas.weekly_review import strings as S
    assert S.LABEL_EVIDENCE_GAP == "Evidence Gap"
    assert S.LABEL_RISK_TO_MONITOR == "Risk to Monitor"
    assert S.LABEL_REASON_TO_WAIT == "Reason to Wait"
    assert S.LABEL_DECISION_DEFERRED == "Decision Deferred"
    assert S.LABEL_NO_ACTION_WARRANTED == "No Action Warranted"
    assert S.LABEL_AGING_NOTE == "Aging Note"
    assert S.LABEL_MISSING_OPTIONAL_INPUT == "Missing Optional Input"
    assert S.LABEL_INPUT_STATUS == "Input Status"
    assert S.LABEL_INPUT_WARNINGS == "Input Warnings"


# ---------------------------------------------------------------------------
# Output preservation
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


def test_output_includes_disclaimer_first_line():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_minimal_result())
    assert "Atlas Weekly Investment Review — deterministic, local-only, no recommendations." in out


def test_output_includes_disclaimer_second_line():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_minimal_result())
    assert "Atlas supports better judgment. It does not replace it." in out


def test_output_disclaimer_appears_near_top():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_minimal_result())
    lines = out.splitlines()
    disclaimer_line = next(
        (i for i, l in enumerate(lines) if "deterministic, local-only" in l), None
    )
    assert disclaimer_line is not None
    assert disclaimer_line < 5


def test_output_title_before_disclaimer():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_minimal_result())
    title_pos = out.index("# Atlas Weekly Investment Review")
    disclaimer_pos = out.index("deterministic, local-only")
    assert title_pos < disclaimer_pos


def test_output_all_10_section_titles_unchanged():
    from atlas.weekly_review.render import render_weekly_review
    from atlas.weekly_review.strings import WEEKLY_REVIEW_SECTION_TITLES
    out = render_weekly_review(_load_minimal_result())
    for title in WEEKLY_REVIEW_SECTION_TITLES:
        assert title in out, f"Section title missing: {title!r}"


def test_output_full_includes_disclaimer():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_full_result())
    assert "deterministic, local-only, no recommendations." in out
    assert "Atlas supports better judgment. It does not replace it." in out


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
    # Sprint 257: --language added to Phase 1 read-only commands (weekly-review,
    # snapshot validate, snapshot review). Deferred commands remain without it.
    import atlas.cli.main as main_mod
    source = Path(main_mod.__file__).read_text(encoding="utf-8")
    # Phase 1 implementation is present
    assert "--language" in source


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

"""Sprint 239 — Weekly Review section title constants tests.

Verifies that the 10 Weekly Review section titles have been extracted into a
constants module and that the renderer references them. Confirms exact wording,
numbering, and output structure are unchanged.

No runtime behavior changes are expected or tested here.
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

EXPECTED_SECTION_TITLES = (
    "1. Review Scope",
    "2. Portfolio Context",
    "3. Watchlist Review",
    "4. Company Reviews Needing Attention",
    "5. Portfolio Fit and Suitability Notes",
    "6. Risk and Principle Guardrails",
    "7. Open Decisions",
    "8. Missing Evidence",
    "9. Follow-Up Questions",
    "10. Non-Actions / Reasons to Wait",
)


# ---------------------------------------------------------------------------
# Constants module existence and structure
# ---------------------------------------------------------------------------

def test_strings_module_exists():
    assert STRINGS_MODULE.exists(), f"{STRINGS_MODULE} not found"


def test_strings_module_is_nonempty():
    assert len(STRINGS_MODULE.read_text(encoding="utf-8").strip()) > 100


def test_strings_module_has_no_imports_beyond_annotations():
    source = STRINGS_MODULE.read_text(encoding="utf-8")
    assert "import requests" not in source
    assert "import urllib" not in source
    assert "import gettext" not in source
    assert "import locale" not in source


def test_strings_module_has_no_language_parameter():
    source = STRINGS_MODULE.read_text(encoding="utf-8")
    assert "--language" not in source
    assert "language=" not in source


# ---------------------------------------------------------------------------
# Section title constants — exact wording and numbering
# ---------------------------------------------------------------------------

def test_section_review_scope_constant():
    from atlas.weekly_review import strings as S
    assert S.SECTION_REVIEW_SCOPE == "1. Review Scope"


def test_section_portfolio_context_constant():
    from atlas.weekly_review import strings as S
    assert S.SECTION_PORTFOLIO_CONTEXT == "2. Portfolio Context"


def test_section_watchlist_review_constant():
    from atlas.weekly_review import strings as S
    assert S.SECTION_WATCHLIST_REVIEW == "3. Watchlist Review"


def test_section_company_reviews_needing_attention_constant():
    from atlas.weekly_review import strings as S
    assert S.SECTION_COMPANY_REVIEWS_NEEDING_ATTENTION == "4. Company Reviews Needing Attention"


def test_section_portfolio_fit_and_suitability_notes_constant():
    from atlas.weekly_review import strings as S
    assert S.SECTION_PORTFOLIO_FIT_AND_SUITABILITY_NOTES == "5. Portfolio Fit and Suitability Notes"


def test_section_risk_and_principle_guardrails_constant():
    from atlas.weekly_review import strings as S
    assert S.SECTION_RISK_AND_PRINCIPLE_GUARDRAILS == "6. Risk and Principle Guardrails"


def test_section_open_decisions_constant():
    from atlas.weekly_review import strings as S
    assert S.SECTION_OPEN_DECISIONS == "7. Open Decisions"


def test_section_missing_evidence_constant():
    from atlas.weekly_review import strings as S
    assert S.SECTION_MISSING_EVIDENCE == "8. Missing Evidence"


def test_section_follow_up_questions_constant():
    from atlas.weekly_review import strings as S
    assert S.SECTION_FOLLOW_UP_QUESTIONS == "9. Follow-Up Questions"


def test_section_non_actions_reasons_to_wait_constant():
    from atlas.weekly_review import strings as S
    assert S.SECTION_NON_ACTIONS_REASONS_TO_WAIT == "10. Non-Actions / Reasons to Wait"


# ---------------------------------------------------------------------------
# Document title constant
# ---------------------------------------------------------------------------

def test_weekly_review_title_constant():
    from atlas.weekly_review import strings as S
    assert S.WEEKLY_REVIEW_TITLE == "Atlas Weekly Investment Review"


# ---------------------------------------------------------------------------
# Ordered tuple of all section titles
# ---------------------------------------------------------------------------

def test_section_titles_tuple_exists():
    from atlas.weekly_review import strings as S
    assert hasattr(S, "WEEKLY_REVIEW_SECTION_TITLES")


def test_section_titles_tuple_has_10_entries():
    from atlas.weekly_review import strings as S
    assert len(S.WEEKLY_REVIEW_SECTION_TITLES) == 10


def test_section_titles_tuple_matches_individual_constants():
    from atlas.weekly_review import strings as S
    assert S.WEEKLY_REVIEW_SECTION_TITLES == EXPECTED_SECTION_TITLES


def test_section_titles_tuple_order_is_1_through_10():
    from atlas.weekly_review import strings as S
    for i, title in enumerate(S.WEEKLY_REVIEW_SECTION_TITLES, start=1):
        assert title.startswith(f"{i}. "), f"Title at position {i} does not start with '{i}. ': {title!r}"


# ---------------------------------------------------------------------------
# Renderer references constants module
# ---------------------------------------------------------------------------

def test_render_module_imports_strings():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "from atlas.weekly_review import strings" in source or \
           "from atlas.weekly_review.strings import" in source


def test_render_module_references_section_constants():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "S.SECTION_REVIEW_SCOPE" in source
    assert "S.SECTION_NON_ACTIONS_REASONS_TO_WAIT" in source


def test_render_module_references_title_constant():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "S.WEEKLY_REVIEW_TITLE" in source or "WEEKLY_REVIEW_TITLE" in source


def test_render_module_no_inline_section_titles():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    # Inline string literals for section titles must be gone from render.py
    for title in EXPECTED_SECTION_TITLES:
        assert f'"{title}"' not in source, f"Inline title literal still in render.py: {title!r}"
        assert f"'{title}'" not in source, f"Inline title literal still in render.py: {title!r}"


# ---------------------------------------------------------------------------
# Output preservation — section titles appear in output
# ---------------------------------------------------------------------------

def _make_minimal_result():
    """Build a minimal WeeklyReviewLoadResult using real example inputs."""
    from pathlib import Path as _Path
    from atlas.weekly_review.inputs import WeeklyReviewInputPaths, load_weekly_review_inputs
    paths = WeeklyReviewInputPaths(
        portfolio_path=_Path("examples/weekly_review/portfolio.json"),
        watchlist_path=_Path("examples/weekly_review/watchlist.json"),
        as_of="2026-01-01",
    )
    return load_weekly_review_inputs(paths)


def test_weekly_review_output_includes_all_10_section_headings():
    from atlas.weekly_review.render import render_weekly_review
    result = _make_minimal_result()
    output = render_weekly_review(result)
    for title in EXPECTED_SECTION_TITLES:
        assert title in output, f"Section title missing from output: {title!r}"


def test_weekly_review_output_includes_document_title():
    from atlas.weekly_review.render import render_weekly_review
    result = _make_minimal_result()
    output = render_weekly_review(result)
    assert "Atlas Weekly Investment Review" in output


def test_weekly_review_output_section_order():
    from atlas.weekly_review.render import render_weekly_review
    result = _make_minimal_result()
    output = render_weekly_review(result)
    positions = [output.index(title) for title in EXPECTED_SECTION_TITLES]
    assert positions == sorted(positions), "Section titles appear out of order in output"


def test_weekly_review_section_1_heading_format():
    from atlas.weekly_review.render import render_weekly_review
    result = _make_minimal_result()
    output = render_weekly_review(result)
    assert "## 1. Review Scope" in output


def test_weekly_review_section_10_heading_format():
    from atlas.weekly_review.render import render_weekly_review
    result = _make_minimal_result()
    output = render_weekly_review(result)
    assert "## 10. Non-Actions / Reasons to Wait" in output


# ---------------------------------------------------------------------------
# Snapshot CLI constants unaffected
# ---------------------------------------------------------------------------

def test_snapshot_strings_module_still_exists():
    assert Path("atlas/snapshot_input/strings.py").exists()


def test_snapshot_heading_constants_unchanged():
    from atlas.snapshot_input import strings as SS
    assert SS.HEADING_VALIDATION == "Snapshot Draft Validation"
    assert SS.HEADING_REVIEW == "Snapshot Draft Review"
    assert SS.HEADING_CONFIRMATION == "Snapshot Draft Confirmation"
    assert SS.HEADING_REJECTION == "Snapshot Draft Rejection"
    assert SS.HEADING_RESEARCH_NOTES_EXPORT == "Research Notes Export"
    assert SS.HEADING_COMPANY_FACTS_EXPORT == "Company Facts Export"


def test_snapshot_safety_constants_unchanged():
    from atlas.snapshot_input import strings as SS
    assert SS.SAFETY_REVIEW_READONLY == "  - Review is read-only."
    assert SS.SAFETY_ORIGINAL_NOT_MODIFIED == "  - Original draft was not modified."
    assert SS.SAFETY_REJECT_NOT_EXPORTABLE == "  - Rejected drafts are not exportable."


# ---------------------------------------------------------------------------
# No new behavioral features introduced
# ---------------------------------------------------------------------------

def test_no_language_option_in_cli():
    import atlas.cli.main as main_mod
    source = Path(main_mod.__file__).read_text(encoding="utf-8")
    assert "--language" not in source


def test_no_gettext_or_locale_in_weekly_review_strings():
    source = STRINGS_MODULE.read_text(encoding="utf-8")
    assert "import gettext" not in source
    assert "import locale" not in source


def test_no_gettext_or_locale_in_weekly_review_render():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "import gettext" not in source
    assert "import locale" not in source


def test_no_provider_imports_in_strings_module():
    source = STRINGS_MODULE.read_text(encoding="utf-8")
    for term in ["requests", "urllib", "httpx", "aiohttp", "boto"]:
        assert term not in source


def test_snapshot_render_module_unaffected():
    source = Path("atlas/snapshot_input/render.py").read_text(encoding="utf-8")
    assert "from atlas.weekly_review" not in source


# ---------------------------------------------------------------------------
# Forbidden language guardrails
# ---------------------------------------------------------------------------

def test_strings_module_no_forbidden_language():
    content = STRINGS_MODULE.read_text(encoding="utf-8")
    for term in FORBIDDEN_LANGUAGE:
        assert term not in content, f"Forbidden language in strings module: {term!r}"


def test_render_module_no_new_forbidden_language():
    content = RENDER_MODULE.read_text(encoding="utf-8")
    for term in FORBIDDEN_LANGUAGE:
        assert term not in content, f"Forbidden language in render module: {term!r}"

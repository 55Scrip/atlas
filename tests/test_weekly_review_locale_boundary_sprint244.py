"""Sprint 244 — Weekly Review locale boundary tests.

Verifies that render_weekly_review accepts an explicit locale parameter,
that locale="en" produces identical output to the default, that unsupported
locales raise a clear ValueError, and that the CLI is unchanged.

No translations are implemented. Only "en" is currently supported.
"""

from __future__ import annotations

from pathlib import Path

RENDER_MODULE = Path("atlas/weekly_review/render.py")
STRINGS_MODULE = Path("atlas/weekly_review/strings.py")

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
# Helpers
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
# Locale parameter accepted
# ---------------------------------------------------------------------------

def test_render_accepts_locale_en():
    from atlas.weekly_review.render import render_weekly_review
    result = _load_minimal_result()
    out = render_weekly_review(result, locale="en")
    assert isinstance(out, str)
    assert len(out) > 0


def test_render_default_equals_locale_en():
    from atlas.weekly_review.render import render_weekly_review
    result = _load_minimal_result()
    assert render_weekly_review(result) == render_weekly_review(result, locale="en")


def test_render_default_equals_locale_en_full_inputs():
    from atlas.weekly_review.render import render_weekly_review
    result = _load_full_result()
    assert render_weekly_review(result) == render_weekly_review(result, locale="en")


# ---------------------------------------------------------------------------
# locale="en" output correctness
# ---------------------------------------------------------------------------

def test_locale_en_output_includes_title():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_minimal_result(), locale="en")
    assert "# Atlas Weekly Investment Review" in out


def test_locale_en_output_includes_all_10_sections():
    from atlas.weekly_review.render import render_weekly_review
    from atlas.weekly_review.strings import WEEKLY_REVIEW_SECTION_TITLES
    out = render_weekly_review(_load_minimal_result(), locale="en")
    for title in WEEKLY_REVIEW_SECTION_TITLES:
        assert title in out, f"Section title missing in locale=en output: {title!r}"


def test_locale_en_output_includes_disclaimer():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_minimal_result(), locale="en")
    assert "deterministic, local-only, no recommendations." in out


def test_locale_en_output_includes_input_status():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_minimal_result(), locale="en")
    assert "## Input Status" in out


# ---------------------------------------------------------------------------
# Unsupported locale raises explicit error
# ---------------------------------------------------------------------------

def test_unsupported_locale_sv_raises():
    import pytest
    from atlas.weekly_review.render import render_weekly_review
    with pytest.raises(ValueError, match="sv"):
        render_weekly_review(_load_minimal_result(), locale="sv")


def test_unsupported_locale_fr_raises():
    import pytest
    from atlas.weekly_review.render import render_weekly_review
    with pytest.raises(ValueError, match="fr"):
        render_weekly_review(_load_minimal_result(), locale="fr")


def test_unsupported_locale_de_raises():
    import pytest
    from atlas.weekly_review.render import render_weekly_review
    with pytest.raises(ValueError, match="de"):
        render_weekly_review(_load_minimal_result(), locale="de")


def test_unsupported_locale_error_message_mentions_en():
    import pytest
    from atlas.weekly_review.render import render_weekly_review
    with pytest.raises(ValueError, match="en"):
        render_weekly_review(_load_minimal_result(), locale="xx")


def test_unsupported_locale_does_not_return_output():
    from atlas.weekly_review.render import render_weekly_review
    raised = False
    try:
        render_weekly_review(_load_minimal_result(), locale="sv")
    except ValueError:
        raised = True
    assert raised, "Expected ValueError for unsupported locale"


def test_locale_parameter_is_keyword_only():
    """locale must be passed as a keyword argument, not positional."""
    import inspect
    from atlas.weekly_review.render import render_weekly_review
    sig = inspect.signature(render_weekly_review)
    locale_param = sig.parameters.get("locale")
    assert locale_param is not None
    assert locale_param.kind == inspect.Parameter.KEYWORD_ONLY


def test_locale_default_is_en():
    import inspect
    from atlas.weekly_review.render import render_weekly_review
    sig = inspect.signature(render_weekly_review)
    assert sig.parameters["locale"].default == "en"


# ---------------------------------------------------------------------------
# Renderer source confirms locale guard
# ---------------------------------------------------------------------------

def test_render_module_has_locale_parameter():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "locale: str" in source


def test_render_module_has_locale_default_en():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert 'locale: str = "en"' in source


def test_render_module_has_locale_guard():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    # Guard may be inline or via shared helper import
    assert ('locale != "en"' in source) or ("ensure_supported_locale" in source)


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
# No gettext / locale detection introduced
# ---------------------------------------------------------------------------

def test_no_gettext_in_render_module():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "import gettext" not in source


def test_no_locale_module_import_in_render():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "import locale" not in source


def test_no_gettext_in_strings_module():
    source = STRINGS_MODULE.read_text(encoding="utf-8")
    assert "import gettext" not in source


def test_no_translation_files_added():
    """No locale/ or translations/ directory should exist."""
    assert not Path("atlas/weekly_review/locale").exists()
    assert not Path("atlas/weekly_review/translations").exists()
    assert not Path("atlas/locale").exists()
    assert not Path("locale").exists()


# ---------------------------------------------------------------------------
# No provider/network imports
# ---------------------------------------------------------------------------

def test_no_provider_imports_in_render_module():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    for term in ["requests", "urllib", "httpx", "aiohttp"]:
        assert term not in source


# ---------------------------------------------------------------------------
# Existing constants remain intact
# ---------------------------------------------------------------------------

def test_prior_constants_intact():
    from atlas.weekly_review import strings as S
    assert S.WEEKLY_REVIEW_TITLE == "Atlas Weekly Investment Review"
    assert len(S.WEEKLY_REVIEW_SECTION_TITLES) == 10
    assert S.LABEL_EVIDENCE_GAP == "Evidence Gap"
    assert S.LABEL_INPUT_STATUS == "Input Status"
    assert S.INPUT_STATUS_PORTFOLIO_LOADED == "Portfolio: {count} holding(s) loaded."
    assert S.WARNING_ROW == "- [{code}] {message}"
    assert "deterministic, local-only" in S.WEEKLY_REVIEW_DISCLAIMER


# ---------------------------------------------------------------------------
# Snapshot CLI unaffected
# ---------------------------------------------------------------------------

def test_snapshot_strings_module_unaffected():
    assert Path("atlas/snapshot_input/strings.py").exists()


def test_snapshot_render_no_weekly_review_imports():
    source = Path("atlas/snapshot_input/render.py").read_text(encoding="utf-8")
    assert "from atlas.weekly_review" not in source


def test_snapshot_heading_constants_unchanged():
    from atlas.snapshot_input import strings as SS
    assert SS.HEADING_VALIDATION == "Snapshot Draft Validation"


# ---------------------------------------------------------------------------
# Language guardrails
# ---------------------------------------------------------------------------

def test_render_module_no_forbidden_language():
    content = RENDER_MODULE.read_text(encoding="utf-8")
    for term in FORBIDDEN_LANGUAGE:
        assert term not in content, f"Forbidden language in render module: {term!r}"


def test_strings_module_no_forbidden_language():
    content = STRINGS_MODULE.read_text(encoding="utf-8")
    for term in FORBIDDEN_LANGUAGE:
        assert term not in content, f"Forbidden language in strings module: {term!r}"

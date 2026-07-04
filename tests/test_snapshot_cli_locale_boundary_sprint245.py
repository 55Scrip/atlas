"""Sprint 245 — Snapshot CLI locale boundary tests.

Verifies that all public Snapshot CLI renderer functions accept an explicit
locale parameter, that locale="en" produces identical output to the default,
that unsupported locales raise a clear ValueError, and that the CLI is unchanged.

No translations are implemented. Only "en" is currently supported.
"""

from __future__ import annotations

import json
from pathlib import Path

RENDER_MODULE = Path("atlas/snapshot_input/render.py")
STRINGS_MODULE = Path("atlas/snapshot_input/strings.py")

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

_EXAMPLE_DRAFT_PATH = Path("examples/snapshot_drafts/research_notes_snapshot.json")
_CONFIRMED_DRAFT_PATH = Path("examples/snapshot_drafts/company_facts_snapshot_confirmed.json")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_draft(path: Path):
    from atlas.snapshot_input.schema import SnapshotDraft
    return SnapshotDraft.from_dict(json.loads(path.read_text(encoding="utf-8")))


# ---------------------------------------------------------------------------
# All renderers accept locale="en"
# ---------------------------------------------------------------------------

def test_validation_accepts_locale_en():
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    draft = _load_draft(_EXAMPLE_DRAFT_PATH)
    out = render_snapshot_draft_validation(draft, locale="en")
    assert isinstance(out, str) and len(out) > 0


def test_validation_error_accepts_locale_en():
    from atlas.snapshot_input.render import render_snapshot_draft_validation_error
    out = render_snapshot_draft_validation_error("test error", locale="en")
    assert isinstance(out, str) and len(out) > 0


def test_review_accepts_locale_en():
    from atlas.snapshot_input.render import render_snapshot_draft_review
    draft = _load_draft(_EXAMPLE_DRAFT_PATH)
    out = render_snapshot_draft_review(draft, locale="en")
    assert isinstance(out, str) and len(out) > 0


def test_review_error_accepts_locale_en():
    from atlas.snapshot_input.render import render_snapshot_draft_review_error
    out = render_snapshot_draft_review_error("test error", locale="en")
    assert isinstance(out, str) and len(out) > 0


def test_confirm_success_accepts_locale_en():
    from atlas.snapshot_input.render import render_snapshot_confirm_success
    out = render_snapshot_confirm_success("in.json", "out.json", "research_notes_snapshot", False, locale="en")
    assert isinstance(out, str) and len(out) > 0


def test_confirm_blocked_accepts_locale_en():
    from atlas.snapshot_input.render import render_snapshot_confirm_blocked
    out = render_snapshot_confirm_blocked("test reason", locale="en")
    assert isinstance(out, str) and len(out) > 0


def test_confirm_error_accepts_locale_en():
    from atlas.snapshot_input.render import render_snapshot_confirm_error
    out = render_snapshot_confirm_error("test error", locale="en")
    assert isinstance(out, str) and len(out) > 0


def test_reject_success_accepts_locale_en():
    from atlas.snapshot_input.render import render_snapshot_reject_success
    out = render_snapshot_reject_success("in.json", "out.json", "research_notes_snapshot", False, False, locale="en")
    assert isinstance(out, str) and len(out) > 0


def test_reject_blocked_accepts_locale_en():
    from atlas.snapshot_input.render import render_snapshot_reject_blocked
    out = render_snapshot_reject_blocked("test reason", locale="en")
    assert isinstance(out, str) and len(out) > 0


def test_reject_error_accepts_locale_en():
    from atlas.snapshot_input.render import render_snapshot_reject_error
    out = render_snapshot_reject_error("test error", locale="en")
    assert isinstance(out, str) and len(out) > 0


def test_research_notes_export_success_accepts_locale_en():
    from atlas.snapshot_input.render import render_research_notes_export_success
    out = render_research_notes_export_success("MSFT", "/tmp/notes.md", locale="en")
    assert isinstance(out, str) and len(out) > 0


def test_research_notes_export_blocked_accepts_locale_en():
    from atlas.snapshot_input.render import render_research_notes_export_blocked
    out = render_research_notes_export_blocked("test reason", locale="en")
    assert isinstance(out, str) and len(out) > 0


def test_company_facts_export_success_accepts_locale_en():
    from atlas.snapshot_input.render import render_company_facts_export_success
    out = render_company_facts_export_success("MSFT", "/tmp/facts.json", locale="en")
    assert isinstance(out, str) and len(out) > 0


def test_company_facts_export_blocked_accepts_locale_en():
    from atlas.snapshot_input.render import render_company_facts_export_blocked
    out = render_company_facts_export_blocked("test reason", locale="en")
    assert isinstance(out, str) and len(out) > 0


# ---------------------------------------------------------------------------
# default == locale="en" for key renderers
# ---------------------------------------------------------------------------

def test_validation_default_equals_locale_en():
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    draft = _load_draft(_EXAMPLE_DRAFT_PATH)
    assert render_snapshot_draft_validation(draft) == render_snapshot_draft_validation(draft, locale="en")


def test_review_default_equals_locale_en():
    from atlas.snapshot_input.render import render_snapshot_draft_review
    draft = _load_draft(_EXAMPLE_DRAFT_PATH)
    assert render_snapshot_draft_review(draft) == render_snapshot_draft_review(draft, locale="en")


def test_confirm_success_default_equals_locale_en():
    from atlas.snapshot_input.render import render_snapshot_confirm_success
    assert (
        render_snapshot_confirm_success("in.json", "out.json", "research_notes_snapshot", False)
        == render_snapshot_confirm_success("in.json", "out.json", "research_notes_snapshot", False, locale="en")
    )


def test_reject_success_default_equals_locale_en():
    from atlas.snapshot_input.render import render_snapshot_reject_success
    assert (
        render_snapshot_reject_success("in.json", "out.json", "research_notes_snapshot", False, False)
        == render_snapshot_reject_success("in.json", "out.json", "research_notes_snapshot", False, False, locale="en")
    )


# ---------------------------------------------------------------------------
# Unsupported locale raises explicit ValueError
# ---------------------------------------------------------------------------

def test_validation_rejects_unsupported_locale():
    import pytest
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    with pytest.raises(ValueError, match="sv"):
        render_snapshot_draft_validation(_load_draft(_EXAMPLE_DRAFT_PATH), locale="sv")


def test_review_rejects_unsupported_locale():
    import pytest
    from atlas.snapshot_input.render import render_snapshot_draft_review
    with pytest.raises(ValueError, match="fr"):
        render_snapshot_draft_review(_load_draft(_EXAMPLE_DRAFT_PATH), locale="fr")


def test_confirm_success_rejects_unsupported_locale():
    import pytest
    from atlas.snapshot_input.render import render_snapshot_confirm_success
    with pytest.raises(ValueError, match="de"):
        render_snapshot_confirm_success("in.json", "out.json", "t", False, locale="de")


def test_reject_success_rejects_unsupported_locale():
    import pytest
    from atlas.snapshot_input.render import render_snapshot_reject_success
    with pytest.raises(ValueError, match="xx"):
        render_snapshot_reject_success("in.json", "out.json", "t", False, False, locale="xx")


def test_unsupported_locale_error_mentions_en():
    import pytest
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    with pytest.raises(ValueError, match="en"):
        render_snapshot_draft_validation(_load_draft(_EXAMPLE_DRAFT_PATH), locale="sv")


def test_locale_parameters_are_keyword_only():
    import inspect
    from atlas.snapshot_input import render as render_mod
    for fn_name in [
        "render_snapshot_draft_validation",
        "render_snapshot_draft_review",
        "render_snapshot_confirm_success",
        "render_snapshot_reject_success",
        "render_research_notes_export_success",
        "render_company_facts_export_success",
    ]:
        fn = getattr(render_mod, fn_name)
        sig = inspect.signature(fn)
        locale_p = sig.parameters.get("locale")
        assert locale_p is not None, f"{fn_name} has no locale param"
        assert locale_p.kind == inspect.Parameter.KEYWORD_ONLY, f"{fn_name} locale is not keyword-only"
        assert locale_p.default == "en", f"{fn_name} locale default is not 'en'"


# ---------------------------------------------------------------------------
# Renderer source confirms guard helper
# ---------------------------------------------------------------------------

def test_render_module_has_ensure_locale_helper():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "_ensure_locale" in source


def test_render_module_has_locale_guard():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    # Guard may be inline or via shared helper import (Sprint 246 centralized it)
    assert ("_SUPPORTED_LOCALE" in source) or ("ensure_supported_locale" in source)


def test_render_module_locale_default_is_en():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert 'locale: str = "en"' in source


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
# No translation/locale infrastructure added
# ---------------------------------------------------------------------------

def test_no_gettext_in_render_module():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "import gettext" not in source


def test_no_locale_module_import_in_render():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "import locale" not in source


def test_no_translation_files_added():
    assert not Path("atlas/snapshot_input/locale").exists()
    assert not Path("atlas/snapshot_input/translations").exists()


def test_no_provider_imports_in_render_module():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    for term in ["requests", "urllib", "httpx", "aiohttp"]:
        assert term not in source


# ---------------------------------------------------------------------------
# Weekly Review locale boundary remains intact
# ---------------------------------------------------------------------------

def test_weekly_review_locale_boundary_intact():
    import inspect
    from atlas.weekly_review.render import render_weekly_review
    sig = inspect.signature(render_weekly_review)
    locale_p = sig.parameters.get("locale")
    assert locale_p is not None
    assert locale_p.kind == inspect.Parameter.KEYWORD_ONLY
    assert locale_p.default == "en"


def test_weekly_review_unsupported_locale_still_raises():
    import pytest
    from atlas.weekly_review.render import render_weekly_review
    from atlas.weekly_review.inputs import WeeklyReviewInputPaths, load_weekly_review_inputs
    paths = WeeklyReviewInputPaths(
        portfolio_path=Path("examples/weekly_review/portfolio.json"),
        watchlist_path=Path("examples/weekly_review/watchlist.json"),
        as_of="2026-01-01",
    )
    result = load_weekly_review_inputs(paths)
    with pytest.raises(ValueError):
        render_weekly_review(result, locale="sv")


# ---------------------------------------------------------------------------
# Snapshot strings constants unaffected
# ---------------------------------------------------------------------------

def test_snapshot_heading_constants_unchanged():
    from atlas.snapshot_input import strings as SS
    assert SS.HEADING_VALIDATION == "Snapshot Draft Validation"
    assert SS.HEADING_COMPANY_FACTS_EXPORT == "Company Facts Export"


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

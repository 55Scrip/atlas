"""Sprint 240 — Weekly Review section label constants tests.

Verifies that repeated Weekly Review section labels have been extracted into
constants and that the renderer references them. Confirms exact wording
and output structure are unchanged.

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


# ---------------------------------------------------------------------------
# Constants module — label constants exist
# ---------------------------------------------------------------------------

def test_label_evidence_gap_constant():
    from atlas.weekly_review import strings as S
    assert S.LABEL_EVIDENCE_GAP == "Evidence Gap"


def test_label_risk_to_monitor_constant():
    from atlas.weekly_review import strings as S
    assert S.LABEL_RISK_TO_MONITOR == "Risk to Monitor"


def test_label_reason_to_wait_constant():
    from atlas.weekly_review import strings as S
    assert S.LABEL_REASON_TO_WAIT == "Reason to Wait"


def test_label_decision_deferred_constant():
    from atlas.weekly_review import strings as S
    assert S.LABEL_DECISION_DEFERRED == "Decision Deferred"


def test_label_no_action_warranted_constant():
    from atlas.weekly_review import strings as S
    assert S.LABEL_NO_ACTION_WARRANTED == "No Action Warranted"


def test_label_aging_note_constant():
    from atlas.weekly_review import strings as S
    assert S.LABEL_AGING_NOTE == "Aging Note"


def test_label_missing_optional_input_constant():
    from atlas.weekly_review import strings as S
    assert S.LABEL_MISSING_OPTIONAL_INPUT == "Missing Optional Input"


def test_label_input_status_constant():
    from atlas.weekly_review import strings as S
    assert S.LABEL_INPUT_STATUS == "Input Status"


def test_label_input_warnings_constant():
    from atlas.weekly_review import strings as S
    assert S.LABEL_INPUT_WARNINGS == "Input Warnings"


# ---------------------------------------------------------------------------
# Sprint 239 section title constants still intact
# ---------------------------------------------------------------------------

def test_sprint239_section_titles_intact():
    from atlas.weekly_review import strings as S
    assert S.SECTION_REVIEW_SCOPE == "1. Review Scope"
    assert S.SECTION_NON_ACTIONS_REASONS_TO_WAIT == "10. Non-Actions / Reasons to Wait"
    assert len(S.WEEKLY_REVIEW_SECTION_TITLES) == 10


def test_weekly_review_title_intact():
    from atlas.weekly_review import strings as S
    assert S.WEEKLY_REVIEW_TITLE == "Atlas Weekly Investment Review"


# ---------------------------------------------------------------------------
# Renderer references label constants
# ---------------------------------------------------------------------------

def test_render_module_references_evidence_gap_label():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "S.LABEL_EVIDENCE_GAP" in source


def test_render_module_references_risk_to_monitor_label():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "S.LABEL_RISK_TO_MONITOR" in source


def test_render_module_references_reason_to_wait_label():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "S.LABEL_REASON_TO_WAIT" in source


def test_render_module_references_decision_deferred_label():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "S.LABEL_DECISION_DEFERRED" in source


def test_render_module_references_no_action_warranted_label():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "S.LABEL_NO_ACTION_WARRANTED" in source


def test_render_module_references_aging_note_label():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "S.LABEL_AGING_NOTE" in source


def test_render_module_references_input_status_label():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "S.LABEL_INPUT_STATUS" in source


def test_render_module_references_input_warnings_label():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "S.LABEL_INPUT_WARNINGS" in source


def test_render_module_no_inline_label_literals():
    """Key label literals must not appear as bare inline strings in render.py."""
    source = RENDER_MODULE.read_text(encoding="utf-8")
    # These patterns indicate the constants were not applied
    for pattern in [
        '"Evidence Gap:',
        '"Evidence Gap [',
        '] Evidence Gap:',
        '"Risk to Monitor:',
        '] Risk to Monitor (',
        '"Reason to Wait:',
        '] (research notes): ',  # too generic — skip
        '"Decision Deferred:',
        '"No Action Warranted:',
        '"[Aging Note]',
        '"## Input Status"',
        '"## Input Warnings"',
        '"Missing Optional Input:',
    ]:
        if pattern == '] (research notes): ':
            continue  # skip — too broad
        assert pattern not in source, f"Inline label literal still in render.py: {pattern!r}"


# ---------------------------------------------------------------------------
# Output preservation — representative Weekly Review with full inputs
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
        scope_notes=_Path("examples/weekly_review/scope_notes.md").read_text(encoding="utf-8") if _Path("examples/weekly_review/scope_notes.md").exists() else None,
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


def test_output_includes_input_status_heading():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_minimal_result())
    assert "## Input Status" in out


def test_output_includes_evidence_gap_label():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_full_result())
    assert "Evidence Gap" in out


def test_output_includes_risk_to_monitor_label():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_full_result())
    assert "Risk to Monitor" in out


def test_output_includes_reason_to_wait_label():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_full_result())
    assert "Reason to Wait" in out


def test_output_includes_no_action_warranted_label():
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_minimal_result())
    assert "No Action Warranted" in out


def test_output_evidence_gap_format_watchlist():
    """Watchlist evidence gaps appear as '[TICKER] Evidence Gap: text'."""
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_full_result())
    assert "] Evidence Gap:" in out


def test_output_evidence_gap_format_section8():
    """Section 8 evidence gaps appear as 'Evidence Gap [TICKER]: text'."""
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_full_result())
    assert "Evidence Gap [" in out


def test_output_risk_to_monitor_research_notes_format():
    """Research notes risks appear as '[TICKER] Risk to Monitor (research notes): text'."""
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_full_result())
    assert "Risk to Monitor (research notes):" in out


def test_output_reason_to_wait_with_evidence_count():
    """Evidence gap count appears in Reason to Wait."""
    from atlas.weekly_review.render import render_weekly_review
    out = render_weekly_review(_load_full_result())
    assert "Reason to Wait:" in out
    assert "evidence gap(s)" in out


def test_output_all_10_section_titles_unchanged():
    from atlas.weekly_review.render import render_weekly_review
    from atlas.weekly_review.strings import WEEKLY_REVIEW_SECTION_TITLES
    out = render_weekly_review(_load_minimal_result())
    for title in WEEKLY_REVIEW_SECTION_TITLES:
        assert title in out, f"Section title missing: {title!r}"


# ---------------------------------------------------------------------------
# Snapshot CLI constants unaffected
# ---------------------------------------------------------------------------

def test_snapshot_strings_module_unaffected():
    assert Path("atlas/snapshot_input/strings.py").exists()


def test_snapshot_heading_constants_unchanged():
    from atlas.snapshot_input import strings as SS
    assert SS.HEADING_VALIDATION == "Snapshot Draft Validation"
    assert SS.HEADING_COMPANY_FACTS_EXPORT == "Company Facts Export"


def test_snapshot_render_module_unaffected():
    source = Path("atlas/snapshot_input/render.py").read_text(encoding="utf-8")
    assert "from atlas.weekly_review" not in source


# ---------------------------------------------------------------------------
# No new behavioral features introduced
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

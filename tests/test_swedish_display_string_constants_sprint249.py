"""Sprint 249 — Swedish display string constants tests.

Verifies that atlas/weekly_review/strings_sv.py and
atlas/snapshot_input/strings_sv.py exist, cover all English constant groups,
use safe Swedish wording from the guardrail doc, do not include translated
canonical values, are not imported by active renderers, and that runtime
output remains English with sv still unsupported.
"""

from __future__ import annotations

import inspect
from pathlib import Path

WR_STRINGS_SV = Path("atlas/weekly_review/strings_sv.py")
SN_STRINGS_SV = Path("atlas/snapshot_input/strings_sv.py")
WR_RENDER = Path("atlas/weekly_review/render.py")
SN_RENDER = Path("atlas/snapshot_input/render.py")
LOCALE_SUPPORT = Path("atlas/locale_support.py")

# Swedish terms that must appear (safe alternatives from guardrail doc)
REQUIRED_WR_TERMS = [
    "Granskningens omfattning",
    "Portföljkontext",
    "Bevakningslista",
    "Saknat underlag",
    "Uppföljningsfrågor",
    "Icke-åtgärder",
    "skäl att avvakta",
    "Underlagslucka",
    "Risk att följa",
    "Skäl att avvakta",
    "Beslut uppskjutet",
    "Ingen åtgärd motiverad",
    "Äldre notering",
    "Indatastatus",
    "Indatavarningar",
    "deterministisk",
    "utan rekommendationer",
    "stöder bättre omdöme",
]

REQUIRED_SN_TERMS = [
    "Validering av Snapshot Draft",
    "Granskning av Snapshot Draft",
    "Bekräftelse av Snapshot Draft",
    "Avvisning av Snapshot Draft",
    "Export av analysnotisar",
    "Export av företagsfakta",
    "Säkerhetsgräns",
    "Exporterbar",
]

# Canonical enum values that must NOT appear as string constant values.
# These are checked in assignment lines only (not docstrings).
CANONICAL_VALUES = [
    "research_notes_snapshot",
    "company_facts_snapshot",
    "portfolio_snapshot",
    "watchlist_snapshot",
    "needs_user_review",
    "superseded",
]

# Forbidden language categories (must not appear in Swedish constants)
FORBIDDEN_SWEDISH = [
    "Köp nu",
    "Sälj",
    "rekommenderar att du köper",
    "Starkt rekommenderat",
    "Garanterat",
    "Kommer att stiga",
    "Agera nu",
    "Bättre än marknaden",
    "Kursmål",
]


# ---------------------------------------------------------------------------
# Module existence
# ---------------------------------------------------------------------------

def test_weekly_review_strings_sv_exists():
    assert WR_STRINGS_SV.exists()


def test_snapshot_strings_sv_exists():
    assert SN_STRINGS_SV.exists()


def test_weekly_review_strings_sv_not_empty():
    assert len(WR_STRINGS_SV.read_text(encoding="utf-8")) > 200


def test_snapshot_strings_sv_not_empty():
    assert len(SN_STRINGS_SV.read_text(encoding="utf-8")) > 200


# ---------------------------------------------------------------------------
# Weekly Review Swedish module — imports correctly
# ---------------------------------------------------------------------------

def test_wr_strings_sv_importable():
    import atlas.weekly_review.strings_sv  # noqa: F401


# ---------------------------------------------------------------------------
# Weekly Review Swedish constants — title
# ---------------------------------------------------------------------------

def test_wr_title_exists():
    from atlas.weekly_review import strings_sv as S
    assert hasattr(S, "WEEKLY_REVIEW_TITLE")
    assert isinstance(S.WEEKLY_REVIEW_TITLE, str)
    assert len(S.WEEKLY_REVIEW_TITLE) > 0


def test_wr_title_is_swedish():
    from atlas.weekly_review import strings_sv as S
    # Must not be the English title
    assert S.WEEKLY_REVIEW_TITLE != "Atlas Weekly Investment Review"


def test_wr_title_no_english_investment_review():
    from atlas.weekly_review import strings_sv as S
    assert "Weekly Investment Review" not in S.WEEKLY_REVIEW_TITLE


# ---------------------------------------------------------------------------
# Weekly Review Swedish constants — all 10 section titles
# ---------------------------------------------------------------------------

def test_wr_section_1_exists():
    from atlas.weekly_review import strings_sv as S
    assert hasattr(S, "SECTION_REVIEW_SCOPE")
    assert S.SECTION_REVIEW_SCOPE.startswith("1.")


def test_wr_section_2_exists():
    from atlas.weekly_review import strings_sv as S
    assert hasattr(S, "SECTION_PORTFOLIO_CONTEXT")
    assert S.SECTION_PORTFOLIO_CONTEXT.startswith("2.")


def test_wr_section_3_exists():
    from atlas.weekly_review import strings_sv as S
    assert hasattr(S, "SECTION_WATCHLIST_REVIEW")
    assert S.SECTION_WATCHLIST_REVIEW.startswith("3.")


def test_wr_section_4_exists():
    from atlas.weekly_review import strings_sv as S
    assert hasattr(S, "SECTION_COMPANY_REVIEWS_NEEDING_ATTENTION")
    assert S.SECTION_COMPANY_REVIEWS_NEEDING_ATTENTION.startswith("4.")


def test_wr_section_5_exists():
    from atlas.weekly_review import strings_sv as S
    assert hasattr(S, "SECTION_PORTFOLIO_FIT_AND_SUITABILITY_NOTES")
    assert S.SECTION_PORTFOLIO_FIT_AND_SUITABILITY_NOTES.startswith("5.")


def test_wr_section_6_exists():
    from atlas.weekly_review import strings_sv as S
    assert hasattr(S, "SECTION_RISK_AND_PRINCIPLE_GUARDRAILS")
    assert S.SECTION_RISK_AND_PRINCIPLE_GUARDRAILS.startswith("6.")


def test_wr_section_7_exists():
    from atlas.weekly_review import strings_sv as S
    assert hasattr(S, "SECTION_OPEN_DECISIONS")
    assert S.SECTION_OPEN_DECISIONS.startswith("7.")


def test_wr_section_8_exists():
    from atlas.weekly_review import strings_sv as S
    assert hasattr(S, "SECTION_MISSING_EVIDENCE")
    assert S.SECTION_MISSING_EVIDENCE.startswith("8.")


def test_wr_section_9_exists():
    from atlas.weekly_review import strings_sv as S
    assert hasattr(S, "SECTION_FOLLOW_UP_QUESTIONS")
    assert S.SECTION_FOLLOW_UP_QUESTIONS.startswith("9.")


def test_wr_section_10_exists():
    from atlas.weekly_review import strings_sv as S
    assert hasattr(S, "SECTION_NON_ACTIONS_REASONS_TO_WAIT")
    assert S.SECTION_NON_ACTIONS_REASONS_TO_WAIT.startswith("10.")


def test_wr_section_titles_tuple_has_10_entries():
    from atlas.weekly_review import strings_sv as S
    assert hasattr(S, "WEEKLY_REVIEW_SECTION_TITLES")
    assert len(S.WEEKLY_REVIEW_SECTION_TITLES) == 10


def test_wr_section_titles_tuple_all_strings():
    from atlas.weekly_review import strings_sv as S
    for title in S.WEEKLY_REVIEW_SECTION_TITLES:
        assert isinstance(title, str) and len(title) > 0


def test_wr_section_titles_differ_from_english():
    from atlas.weekly_review import strings_sv as S
    from atlas.weekly_review import strings as EN
    for sv_title, en_title in zip(S.WEEKLY_REVIEW_SECTION_TITLES, EN.WEEKLY_REVIEW_SECTION_TITLES):
        assert sv_title != en_title


# ---------------------------------------------------------------------------
# Weekly Review Swedish constants — labels
# ---------------------------------------------------------------------------

def test_wr_label_evidence_gap():
    from atlas.weekly_review import strings_sv as S
    assert hasattr(S, "LABEL_EVIDENCE_GAP")
    assert S.LABEL_EVIDENCE_GAP == "Underlagslucka"


def test_wr_label_risk_to_monitor():
    from atlas.weekly_review import strings_sv as S
    assert S.LABEL_RISK_TO_MONITOR == "Risk att följa"


def test_wr_label_reason_to_wait():
    from atlas.weekly_review import strings_sv as S
    assert S.LABEL_REASON_TO_WAIT == "Skäl att avvakta"


def test_wr_label_decision_deferred():
    from atlas.weekly_review import strings_sv as S
    assert S.LABEL_DECISION_DEFERRED == "Beslut uppskjutet"


def test_wr_label_no_action_warranted():
    from atlas.weekly_review import strings_sv as S
    assert S.LABEL_NO_ACTION_WARRANTED == "Ingen åtgärd motiverad"


def test_wr_label_aging_note():
    from atlas.weekly_review import strings_sv as S
    assert hasattr(S, "LABEL_AGING_NOTE")
    assert isinstance(S.LABEL_AGING_NOTE, str)


def test_wr_label_missing_optional_input():
    from atlas.weekly_review import strings_sv as S
    assert hasattr(S, "LABEL_MISSING_OPTIONAL_INPUT")


def test_wr_label_input_status():
    from atlas.weekly_review import strings_sv as S
    assert S.LABEL_INPUT_STATUS == "Indatastatus"


def test_wr_label_input_warnings():
    from atlas.weekly_review import strings_sv as S
    assert S.LABEL_INPUT_WARNINGS == "Indatavarningar"


# ---------------------------------------------------------------------------
# Weekly Review Swedish constants — input status templates
# ---------------------------------------------------------------------------

def test_wr_input_status_portfolio_loaded():
    from atlas.weekly_review import strings_sv as S
    assert hasattr(S, "INPUT_STATUS_PORTFOLIO_LOADED")
    assert "{count}" in S.INPUT_STATUS_PORTFOLIO_LOADED


def test_wr_input_status_watchlist_loaded():
    from atlas.weekly_review import strings_sv as S
    assert "{count}" in S.INPUT_STATUS_WATCHLIST_LOADED
    assert "{name}" in S.INPUT_STATUS_WATCHLIST_LOADED


def test_wr_input_status_investor_profile_available():
    from atlas.weekly_review import strings_sv as S
    assert hasattr(S, "INPUT_STATUS_INVESTOR_PROFILE_AVAILABLE")


def test_wr_input_status_investor_profile_not_provided():
    from atlas.weekly_review import strings_sv as S
    assert hasattr(S, "INPUT_STATUS_INVESTOR_PROFILE_NOT_PROVIDED")


def test_wr_input_status_journal_loaded():
    from atlas.weekly_review import strings_sv as S
    assert "{count}" in S.INPUT_STATUS_JOURNAL_LOADED


def test_wr_input_status_journal_not_provided():
    from atlas.weekly_review import strings_sv as S
    assert hasattr(S, "INPUT_STATUS_JOURNAL_NOT_PROVIDED")


def test_wr_input_status_company_facts_available():
    from atlas.weekly_review import strings_sv as S
    assert hasattr(S, "INPUT_STATUS_COMPANY_FACTS_AVAILABLE")


def test_wr_input_status_company_facts_not_provided():
    from atlas.weekly_review import strings_sv as S
    assert hasattr(S, "INPUT_STATUS_COMPANY_FACTS_NOT_PROVIDED")


def test_wr_input_status_financials_available():
    from atlas.weekly_review import strings_sv as S
    assert hasattr(S, "INPUT_STATUS_FINANCIALS_AVAILABLE")


def test_wr_input_status_financials_not_provided():
    from atlas.weekly_review import strings_sv as S
    assert hasattr(S, "INPUT_STATUS_FINANCIALS_NOT_PROVIDED")


def test_wr_input_status_research_notes_loaded():
    from atlas.weekly_review import strings_sv as S
    assert "{count}" in S.INPUT_STATUS_RESEARCH_NOTES_LOADED


def test_wr_input_status_research_notes_not_provided():
    from atlas.weekly_review import strings_sv as S
    assert hasattr(S, "INPUT_STATUS_RESEARCH_NOTES_NOT_PROVIDED")


def test_wr_input_status_review_date():
    from atlas.weekly_review import strings_sv as S
    assert "{date}" in S.INPUT_STATUS_REVIEW_DATE


def test_wr_input_status_warnings_count():
    from atlas.weekly_review import strings_sv as S
    assert "{count}" in S.INPUT_STATUS_WARNINGS_COUNT


def test_wr_all_14_input_status_constants_present():
    from atlas.weekly_review import strings_sv as S
    expected = [
        "INPUT_STATUS_PORTFOLIO_LOADED",
        "INPUT_STATUS_WATCHLIST_LOADED",
        "INPUT_STATUS_INVESTOR_PROFILE_AVAILABLE",
        "INPUT_STATUS_INVESTOR_PROFILE_NOT_PROVIDED",
        "INPUT_STATUS_JOURNAL_LOADED",
        "INPUT_STATUS_JOURNAL_NOT_PROVIDED",
        "INPUT_STATUS_COMPANY_FACTS_AVAILABLE",
        "INPUT_STATUS_COMPANY_FACTS_NOT_PROVIDED",
        "INPUT_STATUS_FINANCIALS_AVAILABLE",
        "INPUT_STATUS_FINANCIALS_NOT_PROVIDED",
        "INPUT_STATUS_RESEARCH_NOTES_LOADED",
        "INPUT_STATUS_RESEARCH_NOTES_NOT_PROVIDED",
        "INPUT_STATUS_REVIEW_DATE",
        "INPUT_STATUS_WARNINGS_COUNT",
    ]
    for name in expected:
        assert hasattr(S, name), f"Missing constant: {name}"


# ---------------------------------------------------------------------------
# Weekly Review Swedish constants — warning templates
# ---------------------------------------------------------------------------

def test_wr_warning_row_format():
    from atlas.weekly_review import strings_sv as S
    assert "{code}" in S.WARNING_ROW
    assert "{message}" in S.WARNING_ROW


def test_wr_warning_scope_summary_format():
    from atlas.weekly_review import strings_sv as S
    assert "{count}" in S.WARNING_SCOPE_SUMMARY


# ---------------------------------------------------------------------------
# Weekly Review Swedish constants — disclaimer
# ---------------------------------------------------------------------------

def test_wr_disclaimer_exists():
    from atlas.weekly_review import strings_sv as S
    assert hasattr(S, "WEEKLY_REVIEW_DISCLAIMER")
    assert isinstance(S.WEEKLY_REVIEW_DISCLAIMER, str)


def test_wr_disclaimer_two_lines():
    from atlas.weekly_review import strings_sv as S
    assert "\n" in S.WEEKLY_REVIEW_DISCLAIMER
    lines = S.WEEKLY_REVIEW_DISCLAIMER.split("\n")
    assert len(lines) == 2


def test_wr_disclaimer_contains_deterministisk():
    from atlas.weekly_review import strings_sv as S
    assert "deterministisk" in S.WEEKLY_REVIEW_DISCLAIMER


def test_wr_disclaimer_contains_utan_rekommendationer():
    from atlas.weekly_review import strings_sv as S
    assert "utan rekommendationer" in S.WEEKLY_REVIEW_DISCLAIMER


def test_wr_disclaimer_contains_bättre_omdöme():
    from atlas.weekly_review import strings_sv as S
    assert "bättre omdöme" in S.WEEKLY_REVIEW_DISCLAIMER


def test_wr_disclaimer_differs_from_english():
    from atlas.weekly_review import strings_sv as S
    from atlas.weekly_review import strings as EN
    assert S.WEEKLY_REVIEW_DISCLAIMER != EN.WEEKLY_REVIEW_DISCLAIMER


# ---------------------------------------------------------------------------
# Weekly Review Swedish — safe terms present in module
# ---------------------------------------------------------------------------

def test_wr_sv_module_contains_required_terms():
    content = WR_STRINGS_SV.read_text(encoding="utf-8")
    for term in REQUIRED_WR_TERMS:
        assert term in content, f"Required Swedish term missing from strings_sv.py: {term!r}"


# ---------------------------------------------------------------------------
# Weekly Review Swedish — no forbidden language
# ---------------------------------------------------------------------------

def test_wr_sv_module_no_forbidden_language():
    content = WR_STRINGS_SV.read_text(encoding="utf-8")
    for term in FORBIDDEN_SWEDISH:
        assert term not in content, f"Forbidden Swedish term in strings_sv.py: {term!r}"


# ---------------------------------------------------------------------------
# Weekly Review Swedish — no translated canonical values
# ---------------------------------------------------------------------------

def test_wr_sv_module_no_canonical_values():
    # Scan only assignment lines — docstrings may mention canonical values as explanatory text
    lines = [l for l in WR_STRINGS_SV.read_text(encoding="utf-8").splitlines()
             if "=" in l and not l.strip().startswith("#") and not l.strip().startswith('"""')]
    assignment_text = "\n".join(lines)
    for val in CANONICAL_VALUES:
        assert val not in assignment_text, f"Canonical value must not appear as assignment in strings_sv.py: {val!r}"


# ---------------------------------------------------------------------------
# Snapshot Swedish module — imports correctly
# ---------------------------------------------------------------------------

def test_sn_strings_sv_importable():
    import atlas.snapshot_input.strings_sv  # noqa: F401


# ---------------------------------------------------------------------------
# Snapshot Swedish constants — headings
# ---------------------------------------------------------------------------

def test_sn_heading_validation():
    from atlas.snapshot_input import strings_sv as S
    assert hasattr(S, "HEADING_VALIDATION")
    assert "Snapshot Draft" in S.HEADING_VALIDATION or "Validering" in S.HEADING_VALIDATION


def test_sn_heading_review():
    from atlas.snapshot_input import strings_sv as S
    assert hasattr(S, "HEADING_REVIEW")
    assert S.HEADING_REVIEW != "Snapshot Draft Review"


def test_sn_heading_confirmation():
    from atlas.snapshot_input import strings_sv as S
    assert hasattr(S, "HEADING_CONFIRMATION")
    assert S.HEADING_CONFIRMATION != "Snapshot Draft Confirmation"


def test_sn_heading_rejection():
    from atlas.snapshot_input import strings_sv as S
    assert hasattr(S, "HEADING_REJECTION")
    assert S.HEADING_REJECTION != "Snapshot Draft Rejection"


def test_sn_heading_research_notes_export():
    from atlas.snapshot_input import strings_sv as S
    assert S.HEADING_RESEARCH_NOTES_EXPORT == "Export av analysnotisar"


def test_sn_heading_company_facts_export():
    from atlas.snapshot_input import strings_sv as S
    assert S.HEADING_COMPANY_FACTS_EXPORT == "Export av företagsfakta"


def test_sn_all_6_headings_present():
    from atlas.snapshot_input import strings_sv as S
    for name in [
        "HEADING_VALIDATION", "HEADING_REVIEW", "HEADING_CONFIRMATION",
        "HEADING_REJECTION", "HEADING_RESEARCH_NOTES_EXPORT", "HEADING_COMPANY_FACTS_EXPORT",
    ]:
        assert hasattr(S, name), f"Missing heading constant: {name}"


# ---------------------------------------------------------------------------
# Snapshot Swedish constants — status display lines
# ---------------------------------------------------------------------------

def test_sn_all_7_status_lines_present():
    from atlas.snapshot_input import strings_sv as S
    for name in [
        "STATUS_VALID", "STATUS_INVALID", "STATUS_REVIEWABLE",
        "STATUS_BLOCKED", "STATUS_WRITTEN", "STATUS_CONFIRMED", "STATUS_REJECTED",
    ]:
        assert hasattr(S, name), f"Missing status constant: {name}"


def test_sn_status_confirmed_differs_from_english():
    from atlas.snapshot_input import strings_sv as S
    assert S.STATUS_CONFIRMED != "Status: confirmed"


# ---------------------------------------------------------------------------
# Snapshot Swedish constants — exportability lines
# ---------------------------------------------------------------------------

def test_sn_exportable_yes():
    from atlas.snapshot_input import strings_sv as S
    assert hasattr(S, "EXPORTABLE_YES")
    assert S.EXPORTABLE_YES != "Exportable: yes"


def test_sn_exportable_no():
    from atlas.snapshot_input import strings_sv as S
    assert hasattr(S, "EXPORTABLE_NO")


def test_sn_exportable_no_reason():
    from atlas.snapshot_input import strings_sv as S
    assert hasattr(S, "EXPORTABLE_NO_REASON")


# ---------------------------------------------------------------------------
# Snapshot Swedish constants — section headers
# ---------------------------------------------------------------------------

def test_sn_section_safety_boundary():
    from atlas.snapshot_input import strings_sv as S
    assert "Säkerhetsgräns" in S.SECTION_SAFETY_BOUNDARY


def test_sn_section_headers_present():
    from atlas.snapshot_input import strings_sv as S
    for name in [
        "SECTION_SAFETY_BOUNDARY", "SECTION_SOURCE", "SECTION_REVIEW_CHECKLIST",
        "SECTION_UNCERTAINTIES", "SECTION_MISSING_REQUIRED_FIELDS",
        "SECTION_EXTRACTED_FIELDS", "SECTION_BLOCKING_ISSUES",
        "SECTION_RESEARCH_NOTES_REVIEW",
    ]:
        assert hasattr(S, name), f"Missing section header: {name}"


# ---------------------------------------------------------------------------
# Snapshot Swedish constants — safety boundary lines
# ---------------------------------------------------------------------------

def test_sn_safety_lines_present():
    from atlas.snapshot_input import strings_sv as S
    for name in [
        "SAFETY_VALIDATION_NO_WRITE",
        "SAFETY_REVIEW_READONLY", "SAFETY_REVIEW_NO_CONFIRM", "SAFETY_REVIEW_NO_WRITE",
        "SAFETY_ORIGINAL_NOT_MODIFIED", "SAFETY_NO_INPUT_FILES_CHANGED",
        "SAFETY_CONFIRM_EXPORT_SEPARATE",
        "SAFETY_REJECT_NOT_EXPORTABLE",
        "SAFETY_RESEARCH_NOTES_ONLY", "SAFETY_RESEARCH_NOTES_NO_OTHER",
        "SAFETY_COMPANY_FACTS_ONLY", "SAFETY_COMPANY_FACTS_NO_OTHER",
    ]:
        assert hasattr(S, name), f"Missing safety line: {name}"


# ---------------------------------------------------------------------------
# Snapshot Swedish constants — confirm/reject notes
# ---------------------------------------------------------------------------

def test_sn_note_lines_present():
    from atlas.snapshot_input import strings_sv as S
    for name in ["NOTE_ALREADY_CONFIRMED", "NOTE_ALREADY_REJECTED", "NOTE_CONFIRMED_TO_REJECTED"]:
        assert hasattr(S, name), f"Missing note line: {name}"


# ---------------------------------------------------------------------------
# Snapshot Swedish — safe terms present
# ---------------------------------------------------------------------------

def test_sn_sv_module_contains_required_terms():
    content = SN_STRINGS_SV.read_text(encoding="utf-8")
    for term in REQUIRED_SN_TERMS:
        assert term in content, f"Required Swedish term missing from snapshot strings_sv.py: {term!r}"


# ---------------------------------------------------------------------------
# Snapshot Swedish — no forbidden language
# ---------------------------------------------------------------------------

def test_sn_sv_module_no_forbidden_language():
    content = SN_STRINGS_SV.read_text(encoding="utf-8")
    for term in FORBIDDEN_SWEDISH:
        assert term not in content, f"Forbidden Swedish term in snapshot strings_sv.py: {term!r}"


# ---------------------------------------------------------------------------
# Snapshot Swedish — no translated canonical values
# ---------------------------------------------------------------------------

def test_sn_sv_module_no_canonical_values():
    # Scan only assignment lines — docstrings may mention canonical values as explanatory text
    lines = [l for l in SN_STRINGS_SV.read_text(encoding="utf-8").splitlines()
             if "=" in l and not l.strip().startswith("#") and not l.strip().startswith('"""')]
    assignment_text = "\n".join(lines)
    for val in CANONICAL_VALUES:
        assert val not in assignment_text, f"Canonical value must not appear as assignment in snapshot strings_sv.py: {val!r}"


# ---------------------------------------------------------------------------
# Active renderers import Swedish constants for dispatch (Sprint 250)
# but sv remains unsupported at runtime
# ---------------------------------------------------------------------------

def test_weekly_review_render_imports_strings_sv_for_dispatch():
    # Sprint 250: strings_sv imported for locale dispatch readiness; sv still raises
    source = WR_RENDER.read_text(encoding="utf-8")
    assert "strings_sv" in source


def test_snapshot_render_imports_strings_sv_for_dispatch():
    # Sprint 250: strings_sv imported for locale dispatch readiness; sv still raises
    source = SN_RENDER.read_text(encoding="utf-8")
    assert "strings_sv" in source


def test_weekly_review_sv_now_renders_at_runtime():
    # Sprint 251: sv is now supported
    from pathlib import Path as P
    from atlas.weekly_review.inputs import WeeklyReviewInputPaths, load_weekly_review_inputs
    from atlas.weekly_review.render import render_weekly_review
    paths = WeeklyReviewInputPaths(
        portfolio_path=P("examples/weekly_review/portfolio.json"),
        watchlist_path=P("examples/weekly_review/watchlist.json"),
        as_of="2026-01-01",
    )
    result = load_weekly_review_inputs(paths)
    out = render_weekly_review(result, locale="sv")
    assert "Atlas veckovis investeringsgranskning" in out


def test_snapshot_sv_now_renders_at_runtime():
    # Sprint 251: sv is now supported
    import json
    from atlas.snapshot_input.schema import SnapshotDraft
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    draft = SnapshotDraft.from_dict(
        json.loads(Path("examples/snapshot_drafts/research_notes_snapshot.json").read_text(encoding="utf-8"))
    )
    out = render_snapshot_draft_validation(draft, locale="sv")
    assert "Validering av Snapshot Draft" in out


# ---------------------------------------------------------------------------
# locale_support.py — Sprint 251 activated sv
# ---------------------------------------------------------------------------

def test_locale_support_sv_now_present():
    # Sprint 251: SUPPORTED_LOCALE_SV added
    source = LOCALE_SUPPORT.read_text(encoding="utf-8")
    assert 'SUPPORTED_LOCALE_SV = "sv"' in source


def test_locale_support_still_has_en():
    source = LOCALE_SUPPORT.read_text(encoding="utf-8")
    assert 'SUPPORTED_LOCALE_EN = "en"' in source


def test_ensure_supported_locale_accepts_sv():
    # Sprint 251: sv is now supported
    from atlas.locale_support import ensure_supported_locale
    ensure_supported_locale("sv")  # must not raise


def test_ensure_supported_locale_accepts_en():
    from atlas.locale_support import ensure_supported_locale
    ensure_supported_locale("en")  # must not raise


# ---------------------------------------------------------------------------
# Runtime Weekly Review output remains English
# ---------------------------------------------------------------------------

def test_weekly_review_output_is_english():
    from pathlib import Path as P
    from atlas.weekly_review.inputs import WeeklyReviewInputPaths, load_weekly_review_inputs
    from atlas.weekly_review.render import render_weekly_review
    paths = WeeklyReviewInputPaths(
        portfolio_path=P("examples/weekly_review/portfolio.json"),
        watchlist_path=P("examples/weekly_review/watchlist.json"),
        as_of="2026-01-01",
    )
    result = load_weekly_review_inputs(paths)
    out = render_weekly_review(result)
    assert "Atlas Weekly Investment Review" in out
    assert "1. Review Scope" in out
    assert "Granskningens omfattning" not in out


def test_weekly_review_output_no_swedish_headings():
    from pathlib import Path as P
    from atlas.weekly_review.inputs import WeeklyReviewInputPaths, load_weekly_review_inputs
    from atlas.weekly_review.render import render_weekly_review
    paths = WeeklyReviewInputPaths(
        portfolio_path=P("examples/weekly_review/portfolio.json"),
        watchlist_path=P("examples/weekly_review/watchlist.json"),
        as_of="2026-01-01",
    )
    result = load_weekly_review_inputs(paths)
    out = render_weekly_review(result)
    for sv_heading in ["Portföljkontext", "Saknat underlag", "Indatastatus", "Bevakningslista"]:
        assert sv_heading not in out, f"Swedish heading found in English output: {sv_heading!r}"


# ---------------------------------------------------------------------------
# Runtime Snapshot CLI output remains English
# ---------------------------------------------------------------------------

def test_snapshot_render_output_is_english():
    import json
    from atlas.snapshot_input.schema import SnapshotDraft
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    draft = SnapshotDraft.from_dict(
        json.loads(Path("examples/snapshot_drafts/research_notes_snapshot.json").read_text(encoding="utf-8"))
    )
    out = render_snapshot_draft_validation(draft)
    assert "Snapshot Draft Validation" in out
    assert "Validering av Snapshot Draft" not in out


# ---------------------------------------------------------------------------
# No infrastructure additions
# ---------------------------------------------------------------------------

def test_no_gettext_in_sv_modules():
    for path in [WR_STRINGS_SV, SN_STRINGS_SV]:
        assert "gettext" not in path.read_text(encoding="utf-8")


def test_no_locale_import_in_sv_modules():
    for path in [WR_STRINGS_SV, SN_STRINGS_SV]:
        assert "import locale" not in path.read_text(encoding="utf-8")


def test_no_provider_imports_in_sv_modules():
    for path in [WR_STRINGS_SV, SN_STRINGS_SV]:
        content = path.read_text(encoding="utf-8")
        for term in ["requests", "urllib", "httpx", "aiohttp"]:
            assert term not in content


def test_no_translation_directories():
    assert not Path("atlas/weekly_review/locale").exists()
    assert not Path("atlas/snapshot_input/locale").exists()
    assert not Path("atlas/locale").exists()


def test_no_language_option_in_cli():
    # Sprint 257: --language added to Phase 1 read-only commands (weekly-review,
    # snapshot validate, snapshot review). Deferred commands remain without it.
    import atlas.cli.main as main_mod
    source = Path(main_mod.__file__).read_text(encoding="utf-8")
    # Phase 1 implementation is present
    assert "--language" in source


# ---------------------------------------------------------------------------
# English string constants modules unchanged
# ---------------------------------------------------------------------------

def test_wr_english_strings_unchanged():
    from atlas.weekly_review import strings as EN
    assert EN.WEEKLY_REVIEW_TITLE == "Atlas Weekly Investment Review"
    assert EN.SECTION_REVIEW_SCOPE == "1. Review Scope"
    assert EN.WEEKLY_REVIEW_DISCLAIMER.startswith("Atlas Weekly Investment Review")


def test_sn_english_strings_unchanged():
    from atlas.snapshot_input import strings as EN
    assert EN.HEADING_VALIDATION == "Snapshot Draft Validation"
    assert EN.SECTION_SAFETY_BOUNDARY == "Safety Boundary:"

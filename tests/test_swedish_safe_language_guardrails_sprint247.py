"""Sprint 247 — Swedish safe-language guardrail document tests.

Verifies that docs/SwedishSafeLanguageGuardrails.md exists, contains all required
sections, documents all 7 prohibited categories, includes all safe Swedish
alternatives, and explicitly states that sv is not enabled.

No Swedish output is implemented. No locale changes. Documentation-only sprint.
"""

from __future__ import annotations

from pathlib import Path

DOC_PATH = Path("docs/SwedishSafeLanguageGuardrails.md")
LOCALE_SUPPORT = Path("atlas/locale_support.py")
WEEKLY_REVIEW_RENDER = Path("atlas/weekly_review/render.py")
SNAPSHOT_RENDER = Path("atlas/snapshot_input/render.py")


# ---------------------------------------------------------------------------
# Document existence and basic shape
# ---------------------------------------------------------------------------

def test_document_exists():
    assert DOC_PATH.exists(), "docs/SwedishSafeLanguageGuardrails.md must exist"


def test_document_is_not_empty():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert len(content) > 500


def test_document_title():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Swedish Safe-Language Guardrails" in content


def test_document_sprint_number():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "247" in content


def test_document_status_line_sv_not_enabled():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "sv` is not enabled" in content or "not enabled" in content


# ---------------------------------------------------------------------------
# Required sections present
# ---------------------------------------------------------------------------

def test_section_purpose():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "## Purpose" in content


def test_section_scope():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "## Scope" in content


def test_section_non_goals():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "## Non-Goals" in content


def test_section_core_principle():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Core Swedish Output Principle" in content


def test_section_prohibited_categories():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Prohibited Swedish Language Categories" in content


def test_section_safe_alternatives():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Safe Swedish Alternatives" in content


def test_section_concept_mapping():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Atlas Concept Mapping" in content


def test_section_weekly_review_style_rules():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Swedish Weekly Review Style Rules" in content


def test_section_snapshot_cli_style_rules():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Swedish Snapshot CLI Style Rules" in content


def test_section_user_provided_content():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "User-Provided Swedish Content" in content


def test_section_guardrail_sensitive_phrases():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Guardrail-Sensitive Swedish Phrases" in content


def test_section_testing_requirements():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Testing Requirements Before sv Can Be Enabled" in content


def test_section_remaining_gaps():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Remaining Gaps" in content


def test_section_recommended_next_step():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Recommended Next Step" in content


# ---------------------------------------------------------------------------
# All 7 prohibited categories documented
# ---------------------------------------------------------------------------

def test_category_1_recommendation():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Category 1" in content
    assert "Recommendation" in content


def test_category_2_transaction():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Category 2" in content
    assert "Transaction" in content


def test_category_3_price_target():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Category 3" in content
    assert "Price" in content


def test_category_4_urgency():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Category 4" in content
    assert "Urgency" in content


def test_category_5_certainty():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Category 5" in content
    assert "Certainty" in content


def test_category_6_outperformance():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Category 6" in content
    assert "Outperformance" in content


def test_category_7_personalized_advice():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Category 7" in content
    assert "Personalized" in content or "Personalised" in content


# ---------------------------------------------------------------------------
# Safe Swedish alternatives present
# ---------------------------------------------------------------------------

def test_safe_alternative_kräver_mer_underlag():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Kräver mer underlag" in content


def test_safe_alternative_bevakningslista():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Bevakningslista" in content


def test_safe_alternative_beslut_uppskjutet():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Beslut uppskjutet" in content


def test_safe_alternative_ingen_åtgärd_motiverad():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Ingen åtgärd motiverad" in content


def test_safe_alternative_skäl_att_avvakta():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Skäl att avvakta" in content


def test_safe_alternative_underlagslucka():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Underlagslucka" in content


def test_safe_alternative_risk_att_följa():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Risk att följa" in content


def test_safe_alternative_säkerhetsgräns():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Säkerhetsgräns" in content


def test_safe_alternative_fortsätt_undersöka():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Fortsätt undersöka" in content


# ---------------------------------------------------------------------------
# Concept mapping covers Weekly Review sections
# ---------------------------------------------------------------------------

def test_concept_mapping_section_titles_present():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Granskningsomfattning" in content
    assert "Portföljkontext" in content
    assert "Bevakningslistegranskning" in content


def test_concept_mapping_disclaimer_present():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "deterministisk" in content
    assert "utan rekommendationer" in content


def test_concept_mapping_snapshot_headings_present():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Utkastkontroll" in content
    assert "Utkastgranskning" in content
    assert "Utkastbekräftelse" in content


# ---------------------------------------------------------------------------
# Non-goals: sv not enabled, no translations, no gettext, no --language
# ---------------------------------------------------------------------------

def test_non_goals_no_sv_enabled():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Add `sv` to `atlas/locale_support.py`" in content or "Add sv to" in content or "not enable" in content


def test_non_goals_no_translations():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Translate any runtime string" in content or "no translations" in content.lower()


def test_non_goals_no_gettext():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "gettext" in content


def test_testing_requirements_count():
    content = DOC_PATH.read_text(encoding="utf-8")
    # Document should specify at least 10 testing requirements before sv can be enabled
    assert content.count("**Swedish") >= 5 or "10." in content


def test_testing_requirements_sprint_247_does_not_enable():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Sprint 247 does not enable" in content


# ---------------------------------------------------------------------------
# User-provided content rules
# ---------------------------------------------------------------------------

def test_user_content_research_notes_not_translated():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Research notes are not rewritten or translated" in content


def test_user_content_ticker_symbols_preserved():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Ticker symbols" in content or "ticker symbols" in content


# ---------------------------------------------------------------------------
# locale_support.py unchanged — sv not added
# ---------------------------------------------------------------------------

def test_locale_support_still_only_en():
    source = LOCALE_SUPPORT.read_text(encoding="utf-8")
    assert '"sv"' not in source
    assert '"fr"' not in source
    assert 'SUPPORTED_LOCALE_EN = "en"' in source


def test_locale_support_ensure_function_unchanged():
    source = LOCALE_SUPPORT.read_text(encoding="utf-8")
    assert "def ensure_supported_locale" in source


# ---------------------------------------------------------------------------
# Renderer modules unchanged
# ---------------------------------------------------------------------------

def test_weekly_review_render_sv_still_raises():
    # Sprint 250 added a dispatch branch for "sv" in the renderer, but sv
    # remains unsupported until locale_support.py is updated (B5).
    import pytest
    from pathlib import Path as P
    from atlas.weekly_review.inputs import WeeklyReviewInputPaths, load_weekly_review_inputs
    from atlas.weekly_review.render import render_weekly_review
    paths = WeeklyReviewInputPaths(
        portfolio_path=P("examples/weekly_review/portfolio.json"),
        watchlist_path=P("examples/weekly_review/watchlist.json"),
        as_of="2026-01-01",
    )
    result = load_weekly_review_inputs(paths)
    with pytest.raises(ValueError, match="sv"):
        render_weekly_review(result, locale="sv")


def test_snapshot_render_no_sv_in_locale_support():
    # sv must not be in locale_support.py until B5 is intentionally completed
    source = LOCALE_SUPPORT.read_text(encoding="utf-8")
    assert '"sv"' not in source


def test_weekly_review_render_locale_default_still_en():
    source = WEEKLY_REVIEW_RENDER.read_text(encoding="utf-8")
    assert 'locale: str = "en"' in source


def test_snapshot_render_locale_default_still_en():
    source = SNAPSHOT_RENDER.read_text(encoding="utf-8")
    assert 'locale: str = "en"' in source


# ---------------------------------------------------------------------------
# No Swedish strings injected into renderers or strings modules
# ---------------------------------------------------------------------------

def test_weekly_review_strings_no_swedish():
    source = Path("atlas/weekly_review/strings.py").read_text(encoding="utf-8")
    for swedish_term in ["Bevakningslista", "Underlagslucka", "Portfölj", "Granskningsomfattning"]:
        assert swedish_term not in source, f"Swedish term found in weekly_review/strings.py: {swedish_term!r}"


def test_snapshot_strings_no_swedish():
    source = Path("atlas/snapshot_input/strings.py").read_text(encoding="utf-8")
    for swedish_term in ["Utkastkontroll", "Säkerhetsgräns", "Bekräftade", "Portfölj"]:
        assert swedish_term not in source, f"Swedish term found in snapshot_input/strings.py: {swedish_term!r}"


# ---------------------------------------------------------------------------
# Recommended next step documented
# ---------------------------------------------------------------------------

def test_recommended_next_step_mentions_sprint_248():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "248" in content


def test_recommended_next_step_mentions_french():
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "French" in content

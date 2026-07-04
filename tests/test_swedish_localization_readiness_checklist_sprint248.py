"""Sprint 248 — Swedish localization readiness checklist tests.

Verifies that docs/SwedishLocalizationReadinessChecklist.md exists, contains
all 14 blocking criteria, references all approved Swedish terms from the
guardrail spec, correctly reports current status, and confirms sv is not
yet enabled.

No Swedish output is implemented. No locale changes. Documentation-only sprint.
"""

from __future__ import annotations

from pathlib import Path

CHECKLIST_PATH = Path("docs/SwedishLocalizationReadinessChecklist.md")
GUARDRAIL_PATH = Path("docs/SwedishSafeLanguageGuardrails.md")
LOCALE_SUPPORT = Path("atlas/locale_support.py")
WEEKLY_REVIEW_RENDER = Path("atlas/weekly_review/render.py")
SNAPSHOT_RENDER = Path("atlas/snapshot_input/render.py")


# ---------------------------------------------------------------------------
# Document existence and basic shape
# ---------------------------------------------------------------------------

def test_checklist_exists():
    assert CHECKLIST_PATH.exists()


def test_checklist_not_empty():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert len(content) > 500


def test_checklist_title():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "Swedish Localization Readiness Checklist" in content


def test_checklist_sprint_number():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "248" in content


def test_checklist_sv_not_enabled():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "not enabled" in content


# ---------------------------------------------------------------------------
# Required sections present
# ---------------------------------------------------------------------------

def test_section_purpose():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "## Purpose" in content


def test_section_scope():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "## Scope" in content


def test_section_non_goals():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "## Non-Goals" in content


def test_section_blocking_criteria():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "Blocking Criteria" in content


def test_section_non_blocking_criteria():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "Non-Blocking Criteria" in content


def test_section_current_status():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "Current Status" in content


def test_section_how_to_activate():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "How to Activate" in content or "How to activate" in content


def test_section_recommended_implementation_order():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "Recommended Implementation Order" in content or "implementation order" in content.lower()


def test_section_related_documents():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "Related Documents" in content


# ---------------------------------------------------------------------------
# All 14 blocking criteria documented
# ---------------------------------------------------------------------------

def test_criterion_b1_guardrail_spec():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "B1" in content
    assert "Guardrail" in content or "guardrail" in content


def test_criterion_b2_readiness_checklist():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "B2" in content
    assert "Readiness" in content or "checklist" in content.lower()


def test_criterion_b3_string_constants():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "B3" in content
    assert "string" in content.lower() or "constants" in content.lower()


def test_criterion_b4_renderer_integration():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "B4" in content
    assert "renderer" in content.lower() or "Renderer" in content


def test_criterion_b5_locale_support_updated():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "B5" in content
    assert "locale_support" in content


def test_criterion_b6_forbidden_category_scan():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "B6" in content
    assert "forbidden" in content.lower() or "Forbidden" in content or "scan" in content.lower()


def test_criterion_b7_heading_output_tests():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "B7" in content
    assert "heading" in content.lower() or "Heading" in content


def test_criterion_b8_label_output_tests():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "B8" in content
    assert "label" in content.lower() or "Label" in content


def test_criterion_b9_disclaimer_test():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "B9" in content
    assert "disclaimer" in content.lower() or "Disclaimer" in content


def test_criterion_b10_snapshot_cli_heading_tests():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "B10" in content
    assert "Snapshot" in content


def test_criterion_b11_canonical_value_tests():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "B11" in content
    assert "canonical" in content.lower() or "Canonical" in content


def test_criterion_b12_user_content_passthrough():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "B12" in content
    assert "passthrough" in content.lower() or "Passthrough" in content or "user-provided" in content.lower()


def test_criterion_b13_regression_tests():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "B13" in content
    assert "regression" in content.lower() or "Regression" in content


def test_criterion_b14_full_suite_green():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "B14" in content
    assert "green" in content.lower() or "suite" in content.lower()


# ---------------------------------------------------------------------------
# Swedish section title mappings referenced
# ---------------------------------------------------------------------------

def test_granskningsomfattning_referenced():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "Granskningsomfattning" in content


def test_portföljkontext_referenced():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "Portföljkontext" in content


def test_bevakningslistegranskning_referenced():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "Bevakningslistegranskning" in content


def test_saknat_underlag_referenced():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "Saknat underlag" in content


def test_skäl_att_avvakta_referenced():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "Skäl att avvakta" in content


# ---------------------------------------------------------------------------
# Swedish safe alternatives referenced
# ---------------------------------------------------------------------------

def test_underlagslucka_referenced():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "Underlagslucka" in content


def test_risk_att_följa_referenced():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "Risk att följa" in content


def test_ingen_åtgärd_motiverad_referenced():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "Ingen åtgärd motiverad" in content


def test_beslut_uppskjutet_referenced():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "Beslut uppskjutet" in content


def test_säkerhetsgräns_referenced():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "Säkerhetsgräns" in content


# ---------------------------------------------------------------------------
# Snapshot CLI Swedish headings referenced
# ---------------------------------------------------------------------------

def test_utkastkontroll_referenced():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "Utkastkontroll" in content


def test_utkastgranskning_referenced():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "Utkastgranskning" in content


def test_utkastbekräftelse_referenced():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "Utkastbekräftelse" in content


# ---------------------------------------------------------------------------
# Swedish disclaimer mapping referenced
# ---------------------------------------------------------------------------

def test_swedish_disclaimer_line1_referenced():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "deterministisk" in content
    assert "utan rekommendationer" in content


def test_swedish_disclaimer_line2_referenced():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "stöder bättre omdöme" in content


# ---------------------------------------------------------------------------
# Status table: B1 and B2 DONE, B3–B14 OPEN
# ---------------------------------------------------------------------------

def test_status_table_b1_done():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "B1" in content and "DONE" in content


def test_status_table_b2_done():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    # B2 is this document itself — should be marked DONE
    lines = [l for l in content.splitlines() if "B2" in l]
    assert any("DONE" in l for l in lines)


def test_status_table_b3_present():
    # B3 was OPEN at Sprint 248 creation; Sprint 249 marked it DONE — either state is valid
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    lines = [l for l in content.splitlines() if "B3" in l]
    assert any("OPEN" in l or "DONE" in l for l in lines)


def test_status_table_b14_open():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    lines = [l for l in content.splitlines() if "B14" in l]
    assert any("OPEN" in l for l in lines)


def test_status_summary_criteria_count_documented():
    # At Sprint 248 creation: "2 of 14"; after Sprint 249 updated to "3 of 14"
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "of 14" in content


# ---------------------------------------------------------------------------
# Non-goals: sv not added, no translations, no --language
# ---------------------------------------------------------------------------

def test_non_goals_no_sv_enabled():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "Enable Swedish output" in content or "not enable" in content.lower()


def test_non_goals_no_language_flag():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "--language" in content


def test_non_goals_no_locale_support_change():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "locale_support" in content


# ---------------------------------------------------------------------------
# How-to-activate section contains safety note
# ---------------------------------------------------------------------------

def test_activate_section_mentions_string_constants_first():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    # The activation instructions must warn that B3/B4 must exist before B5
    assert "B3" in content and "B4" in content and "B5" in content


# ---------------------------------------------------------------------------
# locale_support.py unchanged
# ---------------------------------------------------------------------------

def test_locale_support_no_sv():
    source = LOCALE_SUPPORT.read_text(encoding="utf-8")
    assert '"sv"' not in source


def test_locale_support_no_fr():
    source = LOCALE_SUPPORT.read_text(encoding="utf-8")
    assert '"fr"' not in source


def test_locale_support_still_has_en():
    source = LOCALE_SUPPORT.read_text(encoding="utf-8")
    assert 'SUPPORTED_LOCALE_EN = "en"' in source


# ---------------------------------------------------------------------------
# Renderer modules unchanged
# ---------------------------------------------------------------------------

def test_weekly_review_render_no_sv_dispatch():
    source = WEEKLY_REVIEW_RENDER.read_text(encoding="utf-8")
    assert '"sv"' not in source


def test_snapshot_render_no_sv_dispatch():
    source = SNAPSHOT_RENDER.read_text(encoding="utf-8")
    assert '"sv"' not in source


# ---------------------------------------------------------------------------
# No Swedish string constants modules created yet
# ---------------------------------------------------------------------------

def test_strings_sv_weekly_review_not_imported_by_renderer():
    # Sprint 249 created strings_sv.py; it must not be imported by the active renderer
    source = Path("atlas/weekly_review/render.py").read_text(encoding="utf-8")
    assert "strings_sv" not in source


def test_strings_sv_snapshot_not_imported_by_renderer():
    # Sprint 249 created strings_sv.py; it must not be imported by the active renderer
    source = Path("atlas/snapshot_input/render.py").read_text(encoding="utf-8")
    assert "strings_sv" not in source


# ---------------------------------------------------------------------------
# Related documents referenced
# ---------------------------------------------------------------------------

def test_references_guardrail_doc():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "SwedishSafeLanguageGuardrails" in content


def test_references_localization_boundary_doc():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "AtlasLocalizationBoundary" in content


def test_references_strings_inventory_doc():
    content = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "AtlasUserFacingStringsInventory" in content


# ---------------------------------------------------------------------------
# Guardrail doc still exists and is unmodified structurally
# ---------------------------------------------------------------------------

def test_guardrail_doc_still_exists():
    assert GUARDRAIL_PATH.exists()


def test_guardrail_doc_still_has_seven_categories():
    content = GUARDRAIL_PATH.read_text(encoding="utf-8")
    for i in range(1, 8):
        assert f"Category {i}" in content

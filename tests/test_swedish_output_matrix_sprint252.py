"""Sprint 252 — Swedish output test matrix.

Renders full Swedish output through direct renderer calls and asserts all
Atlas-generated Swedish strings, canonical English value preservation,
user-provided content passthrough, and forbidden-category safety.

B6 — forbidden-category scan on rendered output
B7 — Weekly Review section-title output matrix
B8 — Weekly Review label/status output matrix
B9 — Swedish disclaimer output test
B10 — Snapshot CLI heading/safety output matrix

sv is supported only in direct renderer calls.
CLI output remains English.
No --language option exists.
B11–B14 remain OPEN.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_PORTFOLIO = Path("examples/weekly_review/portfolio.json")
_WATCHLIST = Path("examples/weekly_review/watchlist.json")
_PROFILE = Path("examples/weekly_review/investor_profile.json")
_JOURNAL = Path("examples/weekly_review/decision_journal.json")
_RESEARCH_NOTES_DIR = Path("examples/weekly_review/research_notes")
_COMPANY_FACTS_DIR = Path("examples/weekly_review/company_facts")
_EXAMPLE_DRAFT = Path("examples/snapshot_drafts/research_notes_snapshot.json")
_COMPANY_FACTS_DRAFT = Path("examples/snapshot_drafts/company_facts_snapshot_confirmed.json")


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _load_wr_result_rich():
    """Load weekly review result with full optional inputs for rich output."""
    from atlas.weekly_review.inputs import WeeklyReviewInputPaths, load_weekly_review_inputs
    paths = WeeklyReviewInputPaths(
        portfolio_path=_PORTFOLIO,
        watchlist_path=_WATCHLIST,
        as_of="2026-01-01",
        profile_path=_PROFILE,
        journal_path=_JOURNAL,
        research_notes_dir=_RESEARCH_NOTES_DIR,
        company_facts_dir=_COMPANY_FACTS_DIR,
        scope_notes="Q1 granskning — fokus på tekniksektorn.",
    )
    return load_weekly_review_inputs(paths)


def _wr_sv():
    from atlas.weekly_review.render import render_weekly_review
    return render_weekly_review(_load_wr_result_rich(), locale="sv")


def _wr_en():
    from atlas.weekly_review.render import render_weekly_review
    return render_weekly_review(_load_wr_result_rich(), locale="en")


def _load_draft():
    from atlas.snapshot_input.schema import SnapshotDraft
    return SnapshotDraft.from_dict(json.loads(_EXAMPLE_DRAFT.read_text(encoding="utf-8")))


# ---------------------------------------------------------------------------
# B7 — Weekly Review section-title output matrix
# ---------------------------------------------------------------------------

def test_b7_wr_sv_title():
    assert "Atlas veckovis investeringsgranskning" in _wr_sv()


def test_b7_wr_sv_section1():
    assert "1. Granskningens omfattning" in _wr_sv()


def test_b7_wr_sv_section2():
    assert "2. Portföljkontext" in _wr_sv()


def test_b7_wr_sv_section3():
    assert "3. Bevakningslista" in _wr_sv()


def test_b7_wr_sv_section4():
    assert "4. Bolagsgranskningar som behöver uppmärksamhet" in _wr_sv()


def test_b7_wr_sv_section5():
    assert "5. Portföljpassning och lämplighetsnoteringar" in _wr_sv()


def test_b7_wr_sv_section6():
    assert "6. Risk- och principgränser" in _wr_sv()


def test_b7_wr_sv_section7():
    assert "7. Öppna beslut" in _wr_sv()


def test_b7_wr_sv_section8():
    assert "8. Saknat underlag" in _wr_sv()


def test_b7_wr_sv_section9():
    assert "9. Uppföljningsfrågor" in _wr_sv()


def test_b7_wr_sv_section10():
    assert "10. Icke-åtgärder / skäl att avvakta" in _wr_sv()


def test_b7_wr_sv_all_ten_sections_present():
    from atlas.weekly_review.strings_sv import WEEKLY_REVIEW_SECTION_TITLES
    out = _wr_sv()
    for title in WEEKLY_REVIEW_SECTION_TITLES:
        assert title in out, f"Section title missing from Swedish output: {title!r}"


def test_b7_wr_en_title_not_in_sv():
    assert "Atlas Weekly Investment Review" not in _wr_sv()


def test_b7_wr_en_title_in_en():
    assert "Atlas Weekly Investment Review" in _wr_en()


# ---------------------------------------------------------------------------
# B8 — Weekly Review label/status output matrix
# ---------------------------------------------------------------------------

def test_b8_label_underlagslucka():
    assert "Underlagslucka" in _wr_sv()


def test_b8_label_risk_att_folja():
    assert "Risk att följa" in _wr_sv()


def test_b8_label_skal_att_avvakta():
    assert "Skäl att avvakta" in _wr_sv()


def test_b8_label_beslut_uppskjutet():
    assert "Beslut uppskjutet" in _wr_sv()


def test_b8_label_ingen_atgard_motiverad():
    assert "Ingen åtgärd motiverad" in _wr_sv()


def test_b8_label_indatastatus():
    assert "Indatastatus" in _wr_sv()


def test_b8_label_indatavarningar():
    # Fixture has at least one warning (missing financials)
    assert "Indatavarningar" in _wr_sv()


def test_b8_input_status_portfolio_loaded():
    # "Portfölj: 3 innehav inlästa."
    assert "Portfölj:" in _wr_sv()
    assert "innehav inlästa" in _wr_sv()


def test_b8_input_status_watchlist_loaded():
    # "Bevakningslista: 2 post(er) inlästa från 'Core Research Watchlist'."
    assert "Bevakningslista:" in _wr_sv()
    assert "post(er) inlästa från" in _wr_sv()


def test_b8_input_status_profile_available():
    assert "Investerarprofil: Tillgänglig" in _wr_sv()


def test_b8_input_status_journal_loaded():
    assert "Beslutsjournal:" in _wr_sv()
    assert "post(er) inlästa" in _wr_sv()


def test_b8_input_status_company_facts_available():
    assert "Företagsfakta: Tillgänglig" in _wr_sv()


def test_b8_input_status_financials_not_provided():
    # Financials dir not loaded in rich fixture → not-provided template
    assert "Finansiell historik: Inte angiven" in _wr_sv()


def test_b8_input_status_research_notes_loaded():
    assert "Analysnotisar:" in _wr_sv()
    assert "ticker(s) med lokala notisar" in _wr_sv()


def test_b8_input_status_review_date():
    assert "Granskningsdatum: 2026-01-01" in _wr_sv()


def test_b8_input_status_warnings_count():
    # At least one warning exists in fixture
    assert "Varningar: 1" in _wr_sv()


def test_b8_warning_scope_summary_format():
    # Warning scope summary line includes Swedish phrase
    assert "indatavarning(ar) noterade" in _wr_sv()


def test_b8_label_saknat_valfritt_indata():
    # Missing optional financials triggers LABEL_MISSING_OPTIONAL_INPUT
    assert "Saknat valfritt indata" in _wr_sv()


# ---------------------------------------------------------------------------
# B9 — Swedish disclaimer output test
# ---------------------------------------------------------------------------

def test_b9_disclaimer_line1():
    assert "Atlas veckovis investeringsgranskning — deterministisk, lokal, utan rekommendationer." in _wr_sv()


def test_b9_disclaimer_line2():
    assert "Atlas stöder bättre omdöme. Det ersätter det inte." in _wr_sv()


def test_b9_disclaimer_both_lines():
    from atlas.weekly_review.strings_sv import WEEKLY_REVIEW_DISCLAIMER
    out = _wr_sv()
    for line in WEEKLY_REVIEW_DISCLAIMER.splitlines():
        assert line in out, f"Disclaimer line missing: {line!r}"


def test_b9_english_disclaimer_not_in_sv():
    out = _wr_sv()
    assert "deterministic, local-only, no recommendations" not in out
    assert "supports better judgment" not in out


# ---------------------------------------------------------------------------
# B10 — Snapshot CLI heading/safety output matrix
# ---------------------------------------------------------------------------

def test_b10_validation_heading():
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    out = render_snapshot_draft_validation(_load_draft(), locale="sv")
    assert "Validering av Snapshot Draft" in out


def test_b10_review_heading():
    from atlas.snapshot_input.render import render_snapshot_draft_review
    out = render_snapshot_draft_review(_load_draft(), locale="sv")
    assert "Granskning av Snapshot Draft" in out


def test_b10_confirm_heading():
    from atlas.snapshot_input.render import render_snapshot_confirm_success
    out = render_snapshot_confirm_success("in.json", "out.json", "research_notes_snapshot", False, locale="sv")
    assert "Bekräftelse av Snapshot Draft" in out


def test_b10_reject_heading():
    from atlas.snapshot_input.render import render_snapshot_reject_success
    out = render_snapshot_reject_success("in.json", "out.json", "research_notes_snapshot", False, False, locale="sv")
    assert "Avvisning av Snapshot Draft" in out


def test_b10_research_notes_export_heading():
    from atlas.snapshot_input.render import render_research_notes_export_success
    out = render_research_notes_export_success("research_notes_snapshot", "/tmp/out.json", locale="sv")
    assert "Export av analysnotisar" in out


def test_b10_company_facts_export_heading():
    from atlas.snapshot_input.render import render_company_facts_export_success
    out = render_company_facts_export_success("MSFT", "/tmp/out.json", locale="sv")
    assert "Export av företagsfakta" in out


def test_b10_validation_safety_boundary_label():
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    out = render_snapshot_draft_validation(_load_draft(), locale="sv")
    assert "Säkerhetsgräns:" in out


def test_b10_validation_safety_no_write_line():
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    out = render_snapshot_draft_validation(_load_draft(), locale="sv")
    assert "Validering av utkast skriver inte till lokala Atlas-indatafiler." in out


def test_b10_review_safety_boundary_label():
    from atlas.snapshot_input.render import render_snapshot_draft_review
    out = render_snapshot_draft_review(_load_draft(), locale="sv")
    assert "Säkerhetsgräns:" in out


def test_b10_review_readonly_line():
    from atlas.snapshot_input.render import render_snapshot_draft_review
    out = render_snapshot_draft_review(_load_draft(), locale="sv")
    assert "Granskning är skrivskyddad." in out


def test_b10_confirm_safety_boundary_label():
    from atlas.snapshot_input.render import render_snapshot_confirm_success
    out = render_snapshot_confirm_success("in.json", "out.json", "research_notes_snapshot", False, locale="sv")
    assert "Säkerhetsgräns:" in out


def test_b10_confirm_original_not_modified_line():
    from atlas.snapshot_input.render import render_snapshot_confirm_success
    out = render_snapshot_confirm_success("in.json", "out.json", "research_notes_snapshot", False, locale="sv")
    assert "Originalutkastet ändrades inte." in out


def test_b10_reject_not_exportable_line():
    from atlas.snapshot_input.render import render_snapshot_reject_success
    out = render_snapshot_reject_success("in.json", "out.json", "research_notes_snapshot", False, False, locale="sv")
    assert "Avvisade utkast kan inte exporteras." in out


def test_b10_validation_status_valid():
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    out = render_snapshot_draft_validation(_load_draft(), locale="sv")
    assert "Status: giltig" in out


def test_b10_confirm_status_confirmed():
    from atlas.snapshot_input.render import render_snapshot_confirm_success
    out = render_snapshot_confirm_success("in.json", "out.json", "research_notes_snapshot", False, locale="sv")
    assert "Status: bekräftad" in out


def test_b10_reject_status_rejected():
    from atlas.snapshot_input.render import render_snapshot_reject_success
    out = render_snapshot_reject_success("in.json", "out.json", "research_notes_snapshot", False, False, locale="sv")
    assert "Status: avvisad" in out


def test_b10_english_headings_absent_from_sv_validation():
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    out = render_snapshot_draft_validation(_load_draft(), locale="sv")
    assert "Snapshot Draft Validation" not in out
    assert "Safety Boundary:" not in out


# ---------------------------------------------------------------------------
# B6 — Forbidden-category scan on rendered Swedish output
# ---------------------------------------------------------------------------

# Category 1: Direct recommendation language
_CAT1_TERMS = [
    "köp nu", "sälj omedelbart", "starkt rekommenderat köp",
    "vi rekommenderar att du köper", "köp aktien", "sälj aktien",
    "rekommenderar att sälja", "rekommenderar att köpa",
]

# Category 2: Transaction / execution language
_CAT2_TERMS = [
    "öppna en position", "öka din exponering", "minska innehavet",
    "ta en position", "öka positionen",
]

# Category 3: Price-target framing
_CAT3_TERMS = [
    "kursmål", "förväntas stiga till", "uppsida till",
    "riktkurs", "prisnivå",
]

# Category 4: Urgency language
_CAT4_TERMS = [
    "agera nu", "missar du tillfället", "innan det är för sent",
    "bråttom", "snarast möjligt",
]

# Category 5: Certainty and promise language
_CAT5_TERMS = [
    "garanterat", "kommer att stiga", "riskfritt",
    "säker avkastning", "ingen risk",
]

# Category 6: Outperformance prediction
_CAT6_TERMS = [
    "kommer att slå index", "bättre än marknaden", "överträffar sektorn",
    "överträffar index", "slår marknaden",
]

# Category 7: Personalized advice framing
_CAT7_TERMS = [
    "baserat på din situation rekommenderar vi",
    "det bästa valet för dig", "finansiell rådgivning",
    "personlig rådgivning", "råd anpassat för dig",
]


def _sv_outputs_all():
    """All rendered Swedish output strings for the scan."""
    from atlas.snapshot_input.render import (
        render_snapshot_draft_validation, render_snapshot_draft_review,
        render_snapshot_confirm_success, render_snapshot_reject_success,
        render_research_notes_export_success, render_company_facts_export_success,
    )
    draft = _load_draft()
    return [
        _wr_sv(),
        render_snapshot_draft_validation(draft, locale="sv"),
        render_snapshot_draft_review(draft, locale="sv"),
        render_snapshot_confirm_success("in.json", "out.json", "research_notes_snapshot", False, locale="sv"),
        render_snapshot_reject_success("in.json", "out.json", "research_notes_snapshot", False, False, locale="sv"),
        render_research_notes_export_success("research_notes_snapshot", "/tmp/f.json", locale="sv"),
        render_company_facts_export_success("MSFT", "/tmp/f.json", locale="sv"),
    ]


def _scan_outputs(terms: list[str]) -> list[str]:
    combined = "\n".join(_sv_outputs_all()).lower()
    return [t for t in terms if t.lower() in combined]


def test_b6_no_cat1_recommendation_language():
    hits = _scan_outputs(_CAT1_TERMS)
    assert not hits, f"Category 1 (recommendation) terms found in Swedish output: {hits}"


def test_b6_no_cat2_transaction_language():
    hits = _scan_outputs(_CAT2_TERMS)
    assert not hits, f"Category 2 (transaction) terms found in Swedish output: {hits}"


def test_b6_no_cat3_price_target_language():
    hits = _scan_outputs(_CAT3_TERMS)
    assert not hits, f"Category 3 (price-target) terms found in Swedish output: {hits}"


def test_b6_no_cat4_urgency_language():
    hits = _scan_outputs(_CAT4_TERMS)
    assert not hits, f"Category 4 (urgency) terms found in Swedish output: {hits}"


def test_b6_no_cat5_certainty_language():
    hits = _scan_outputs(_CAT5_TERMS)
    assert not hits, f"Category 5 (certainty) terms found in Swedish output: {hits}"


def test_b6_no_cat6_outperformance_language():
    hits = _scan_outputs(_CAT6_TERMS)
    assert not hits, f"Category 6 (outperformance) terms found in Swedish output: {hits}"


def test_b6_no_cat7_personalized_advice_language():
    hits = _scan_outputs(_CAT7_TERMS)
    assert not hits, f"Category 7 (personalized advice) terms found in Swedish output: {hits}"


def test_b6_disclaimer_safe_no_recommendation_promise():
    out = _wr_sv()
    assert "garanterat" not in out.lower()
    assert "rekommenderar att köpa" not in out.lower()
    assert "sälj" not in out.lower()


# ---------------------------------------------------------------------------
# Canonical value preservation in Swedish output
# ---------------------------------------------------------------------------

def test_canonical_snapshot_type_research_notes():
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    out = render_snapshot_draft_validation(_load_draft(), locale="sv")
    assert "research_notes_snapshot" in out


def test_canonical_confirmation_status_draft():
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    out = render_snapshot_draft_validation(_load_draft(), locale="sv")
    assert "draft" in out


def test_canonical_confirmation_status_confirmed():
    from atlas.snapshot_input.render import render_snapshot_confirm_success
    out = render_snapshot_confirm_success("in.json", "out.json", "research_notes_snapshot", False, locale="sv")
    assert "confirmed" in out


def test_canonical_confirmation_status_rejected():
    from atlas.snapshot_input.render import render_snapshot_reject_success
    out = render_snapshot_reject_success("in.json", "out.json", "research_notes_snapshot", False, False, locale="sv")
    assert "rejected" in out


def test_canonical_ticker_asml_in_wr_sv():
    assert "ASML" in _wr_sv()


def test_canonical_ticker_msft_in_wr_sv():
    assert "MSFT" in _wr_sv()


def test_canonical_warning_code_preserved():
    # Warning code must appear as-is (not translated)
    assert "missing_optional_financials" in _wr_sv()


def test_canonical_warning_row_format():
    # Warning row uses [code] message format with canonical English code
    assert "[missing_optional_financials]" in _wr_sv()


def test_canonical_file_path_not_translated():
    # target_local_file from snapshot draft must appear unchanged
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    out = render_snapshot_draft_validation(_load_draft(), locale="sv")
    assert "my_review/research_notes/ASML/notes.md" in out


def test_canonical_snapshot_type_research_notes_in_confirm():
    from atlas.snapshot_input.render import render_snapshot_confirm_success
    out = render_snapshot_confirm_success("in.json", "out.json", "research_notes_snapshot", False, locale="sv")
    assert "research_notes_snapshot" in out


# ---------------------------------------------------------------------------
# User-provided content passthrough
# ---------------------------------------------------------------------------

def test_user_content_scope_note_passthrough():
    # Scope note is user-provided and must appear unchanged
    assert "Q1 granskning — fokus på tekniksektorn." in _wr_sv()


def test_user_content_watchlist_reason_passthrough():
    # Watchlist reason from fixture is user-supplied
    assert "Water infrastructure theme" in _wr_sv()


def test_user_content_research_note_evidence_gap_passthrough():
    # Research note evidence gap text is user-supplied
    assert "Margin durability through a downcycle has not been reviewed recently." in _wr_sv()


def test_user_content_decision_journal_note_passthrough():
    # Decision journal view note is user-supplied
    assert "Water infrastructure theme has long-term demand logic." in _wr_sv()


def test_user_content_snapshot_notes_passthrough():
    # Snapshot notes field is user-supplied
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    out = render_snapshot_draft_validation(_load_draft(), locale="sv")
    assert "Draft created from user-written research notes." in out


def test_user_content_snapshot_source_reference_passthrough():
    # Source reference is user-supplied
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    out = render_snapshot_draft_validation(_load_draft(), locale="sv")
    assert "my_notes/asml_notes_2026.md" in out


def test_user_content_watchlist_observation_passthrough():
    # Watchlist observation is user-supplied
    assert "Exposed to water infrastructure spending cycles." in _wr_sv()


# ---------------------------------------------------------------------------
# English output unchanged
# ---------------------------------------------------------------------------

def test_wr_en_title_unchanged():
    assert "Atlas Weekly Investment Review" in _wr_en()


def test_wr_en_section1_unchanged():
    assert "1. Review Scope" in _wr_en()


def test_wr_en_section8_unchanged():
    assert "8. Missing Evidence" in _wr_en()


def test_wr_en_disclaimer_unchanged():
    assert "deterministic, local-only, no recommendations" in _wr_en()


def test_wr_en_equals_default():
    from atlas.weekly_review.render import render_weekly_review
    result = _load_wr_result_rich()
    assert render_weekly_review(result) == render_weekly_review(result, locale="en")


def test_snapshot_en_heading_unchanged():
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    out = render_snapshot_draft_validation(_load_draft(), locale="en")
    assert "Snapshot Draft Validation" in out
    assert "Safety Boundary:" in out


# ---------------------------------------------------------------------------
# CLI preservation
# ---------------------------------------------------------------------------

def _atlas_cli(*args: str) -> subprocess.CompletedProcess:
    atlas_bin = str(Path(".venv/bin/atlas").resolve())
    return subprocess.run([atlas_bin, *args], capture_output=True, text=True)


def test_cli_wr_output_english():
    result = _atlas_cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-01",
    )
    assert result.returncode == 0, result.stderr
    assert "Atlas Weekly Investment Review" in result.stdout
    assert "Atlas veckovis investeringsgranskning" not in result.stdout


def test_cli_snapshot_validate_english():
    result = _atlas_cli("snapshot", "validate", str(_EXAMPLE_DRAFT))
    assert result.returncode == 0, result.stderr
    assert "Snapshot Draft Validation" in result.stdout
    assert "Validering av Snapshot Draft" not in result.stdout


def test_cli_help_no_language():
    result = _atlas_cli("--help")
    assert "--language" not in result.stdout + result.stderr


def test_cli_wr_no_swedish_sections():
    result = _atlas_cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-01",
    )
    for sv_term in ["Granskningens omfattning", "Portföljkontext", "Bevakningslista",
                    "Indatastatus", "Underlagslucka"]:
        assert sv_term not in result.stdout, f"Swedish term in CLI output: {sv_term!r}"


# ---------------------------------------------------------------------------
# No infrastructure additions
# ---------------------------------------------------------------------------

def test_no_gettext_imports():
    for path in [
        Path("atlas/locale_support.py"),
        Path("atlas/weekly_review/render.py"),
        Path("atlas/snapshot_input/render.py"),
    ]:
        assert "import gettext" not in path.read_text(encoding="utf-8"), f"gettext import in {path}"


def test_no_provider_imports():
    for path in [
        Path("atlas/locale_support.py"),
        Path("atlas/weekly_review/render.py"),
        Path("atlas/snapshot_input/render.py"),
    ]:
        source = path.read_text(encoding="utf-8")
        for term in ["requests", "httpx", "aiohttp", "urllib.request"]:
            assert term not in source, f"{term!r} found in {path}"


def test_no_translation_catalogs():
    import atlas
    assert not any(Path(atlas.__file__).parent.glob("**/*.po"))
    assert not any(Path(atlas.__file__).parent.glob("**/*.mo"))

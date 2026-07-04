"""Sprint 262 — Weekly Review body message constants tests.

Verifies that the 27 newly extracted Weekly Review section body message
templates are defined in strings.py and strings_sv.py with exact expected
wording, that render.py no longer contains the hardcoded English literals,
that English CLI output is unchanged, and that Swedish CLI output uses the
new Swedish constants.

No new locales, no gettext, no string catalogs, no runtime detection.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

STRINGS_EN = Path("atlas/weekly_review/strings.py")
STRINGS_SV = Path("atlas/weekly_review/strings_sv.py")
RENDER = Path("atlas/weekly_review/render.py")

_PORTFOLIO = Path("examples/weekly_review/portfolio.json")
_WATCHLIST = Path("examples/weekly_review/watchlist.json")

_AS_OF = "2026-01-05"


def _cli(*args: str) -> subprocess.CompletedProcess:
    atlas = str(Path(".venv/bin/atlas").resolve())
    return subprocess.run([atlas, *args], capture_output=True, text=True)


def _review(*extra: str) -> subprocess.CompletedProcess:
    return _cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", _AS_OF,
        *extra,
    )


# ---------------------------------------------------------------------------
# Section 1 — Review Scope body message constants (English)
# ---------------------------------------------------------------------------

def test_scope_review_date_not_specified_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.SCOPE_REVIEW_DATE_NOT_SPECIFIED == "Review date: Not specified"


def test_scope_input_mode_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.SCOPE_INPUT_MODE == "Input mode: Local files only. No external data, no live pricing."


def test_scope_portfolio_summary_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.SCOPE_PORTFOLIO_SUMMARY == "Portfolio: {count} holding(s) across {accounts} account(s)"
    assert S.SCOPE_PORTFOLIO_SUMMARY.format(count=3, accounts=1) == "Portfolio: 3 holding(s) across 1 account(s)"


def test_scope_watchlist_summary_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.SCOPE_WATCHLIST_SUMMARY == "Watchlist: {count} item(s) in '{name}'"
    assert S.SCOPE_WATCHLIST_SUMMARY.format(count=2, name="My List") == "Watchlist: 2 item(s) in 'My List'"


def test_scope_optional_inputs_loaded_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.SCOPE_OPTIONAL_INPUTS_LOADED == "Optional inputs loaded: {items}"
    assert S.SCOPE_OPTIONAL_INPUTS_LOADED.format(items="investor profile, company facts") == \
        "Optional inputs loaded: investor profile, company facts"


def test_scope_optional_inputs_none_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.SCOPE_OPTIONAL_INPUTS_NONE == (
        "Optional inputs: none provided — review uses portfolio and watchlist only"
    )


# ---------------------------------------------------------------------------
# Section 1 — Review Scope body message constants (Swedish)
# ---------------------------------------------------------------------------

def test_scope_review_date_not_specified_sv_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert S.SCOPE_REVIEW_DATE_NOT_SPECIFIED == "Granskningsdatum: Inte angivet"


def test_scope_input_mode_sv_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert "Lokala filer enbart" in S.SCOPE_INPUT_MODE
    assert "live-prissättning" in S.SCOPE_INPUT_MODE


def test_scope_portfolio_summary_sv_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert "{count}" in S.SCOPE_PORTFOLIO_SUMMARY
    assert "{accounts}" in S.SCOPE_PORTFOLIO_SUMMARY


def test_scope_optional_inputs_none_sv_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert "portfölj" in S.SCOPE_OPTIONAL_INPUTS_NONE.lower()


# ---------------------------------------------------------------------------
# Section 2 — Portfolio Context body message constants (English)
# ---------------------------------------------------------------------------

def test_portfolio_holdings_header_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.PORTFOLIO_HOLDINGS_HEADER == "Holdings by weight (user-supplied values, highest first):"


def test_portfolio_sector_header_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.PORTFOLIO_SECTOR_HEADER == "Sector exposure:"


def test_portfolio_note_local_only_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.PORTFOLIO_NOTE_LOCAL_ONLY == (
        "Note: All values are user-supplied. No live pricing or external data used."
    )


# ---------------------------------------------------------------------------
# Section 2 — Portfolio Context body message constants (Swedish)
# ---------------------------------------------------------------------------

def test_portfolio_holdings_header_sv_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert "vikt" in S.PORTFOLIO_HOLDINGS_HEADER.lower()


def test_portfolio_sector_header_sv_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert "Sektorexponering" in S.PORTFOLIO_SECTOR_HEADER


def test_portfolio_note_local_only_sv_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert "användarsupplerade" in S.PORTFOLIO_NOTE_LOCAL_ONLY.lower()


# ---------------------------------------------------------------------------
# Section 3 — Watchlist Review body message constants
# ---------------------------------------------------------------------------

def test_watchlist_no_items_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.WATCHLIST_NO_ITEMS == "No watchlist items loaded."


def test_watchlist_no_items_sv_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert "bevakningsposter" in S.WATCHLIST_NO_ITEMS.lower()


# ---------------------------------------------------------------------------
# Section 4 — Company Reviews Needing Attention body message constants
# ---------------------------------------------------------------------------

def test_attention_no_items_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.ATTENTION_NO_ITEMS == (
        "No items flagged for immediate attention from available local inputs."
    )


def test_attention_note_local_only_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.ATTENTION_NOTE_LOCAL_ONLY == (
        "Note: All observations are derived from user-supplied local inputs only. "
        "No external data, no engine analysis, no recommendations."
    )


def test_attention_note_local_only_sv_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert "rekommendationer" in S.ATTENTION_NOTE_LOCAL_ONLY.lower()


# ---------------------------------------------------------------------------
# Section 5 — Portfolio Fit and Suitability Notes body message constants
# ---------------------------------------------------------------------------

def test_suitability_profile_provided_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.SUITABILITY_PROFILE_PROVIDED == "Investor profile: Provided."


def test_suitability_profile_not_provided_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.SUITABILITY_PROFILE_NOT_PROVIDED == (
        "Investor profile: Not provided. "
        "Suitability observations below are structural only and not personalized."
    )


def test_suitability_invested_positions_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.SUITABILITY_INVESTED_POSITIONS == "Invested positions: {count} (excluding cash holdings)."
    assert S.SUITABILITY_INVESTED_POSITIONS.format(count=5) == "Invested positions: 5 (excluding cash holdings)."


def test_suitability_engine_deferred_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.SUITABILITY_ENGINE_DEFERRED == (
        "Full suitability evaluation is deferred until engine wiring. "
        "Portfolio fit notes are limited to loaded local structure."
    )


def test_suitability_note_no_merit_judgment_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.SUITABILITY_NOTE_NO_MERIT_JUDGMENT == (
        "Note: Atlas does not judge investment merit or provide personalized guidance. "
        "Suitability assessment requires manual review."
    )


def test_suitability_profile_not_provided_sv_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert "personaliserade" in S.SUITABILITY_PROFILE_NOT_PROVIDED.lower()


def test_suitability_note_no_merit_judgment_sv_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert "investeringsmerit" in S.SUITABILITY_NOTE_NO_MERIT_JUDGMENT.lower()


# ---------------------------------------------------------------------------
# Section 6 — Risk and Principle Guardrails body message constants
# ---------------------------------------------------------------------------

def test_guardrails_engine_deferred_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.GUARDRAILS_ENGINE_DEFERRED == (
        "Risk and principle guardrail engine wiring is deferred to a later sprint."
    )


def test_guardrails_principle_guardrail_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.GUARDRAILS_PRINCIPLE_GUARDRAIL == (
        "Principle Guardrail: No action is warranted when evidence is incomplete."
    )


def test_guardrails_note_local_only_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.GUARDRAILS_NOTE_LOCAL_ONLY == (
        "Note: Guardrail checks are based on user-supplied data only. "
        "No live market data or external analysis used."
    )


def test_guardrails_no_flags_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.GUARDRAILS_NO_FLAGS == "No guardrail flags raised from available local inputs."


def test_guardrails_engine_deferred_sv_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert "Motorkoppling" in S.GUARDRAILS_ENGINE_DEFERRED


def test_guardrails_principle_guardrail_sv_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert "Principgräns" in S.GUARDRAILS_PRINCIPLE_GUARDRAIL


def test_guardrails_no_flags_sv_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert "gränskontrollflaggor" in S.GUARDRAILS_NO_FLAGS.lower()


# ---------------------------------------------------------------------------
# Section 7 — Open Decisions body message constants
# ---------------------------------------------------------------------------

def test_decisions_no_journal_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.DECISIONS_NO_JOURNAL == "No decision journal provided. Open decisions not reviewed."


def test_decisions_journal_reviewed_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.DECISIONS_JOURNAL_REVIEWED == "Decision journal: {count} entry/entries reviewed."
    assert S.DECISIONS_JOURNAL_REVIEWED.format(count=3) == "Decision journal: 3 entry/entries reviewed."


def test_decisions_date_missing_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.DECISIONS_DATE_MISSING == (
        "[Date Missing] No decision date recorded; aging cannot be assessed."
    )


def test_aging_note_suffix_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.AGING_NOTE_SUFFIX == (
        "Review date is older than 90 days ({days} days). "
        "Thesis assumptions may need to be rechecked."
    )
    assert S.AGING_NOTE_SUFFIX.format(days=95) == (
        "Review date is older than 90 days (95 days). Thesis assumptions may need to be rechecked."
    )


def test_decisions_no_journal_sv_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert "beslutsjournal" in S.DECISIONS_NO_JOURNAL.lower()


def test_aging_note_suffix_sv_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert "{days}" in S.AGING_NOTE_SUFFIX
    assert "90 dagar" in S.AGING_NOTE_SUFFIX


# ---------------------------------------------------------------------------
# Section 8 — Missing Evidence body message constants
# ---------------------------------------------------------------------------

def test_evidence_no_gaps_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.EVIDENCE_NO_GAPS == "No evidence gaps identified from available local inputs."


def test_evidence_no_gaps_sv_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert "underlagsluckor" in S.EVIDENCE_NO_GAPS.lower()


# ---------------------------------------------------------------------------
# Section 9 — Follow-Up Questions body message constants
# ---------------------------------------------------------------------------

def test_questions_no_company_facts_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.QUESTIONS_NO_COMPANY_FACTS == (
        "What company facts are needed before changing the status of any watchlist item?"
    )


def test_questions_no_financials_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.QUESTIONS_NO_FINANCIALS == (
        "Which financial trends should be reviewed before any watchlist decision changes?"
    )


def test_questions_open_watchlist_gaps_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.QUESTIONS_OPEN_WATCHLIST_GAPS == (
        "What evidence would confirm or weaken the current assumptions for each open watchlist item?"
    )


def test_questions_none_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.QUESTIONS_NONE == (
        "No follow-up questions identified. "
        "Add open_questions to watchlist items to surface them here."
    )


def test_questions_no_company_facts_sv_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert "företagsfakta" in S.QUESTIONS_NO_COMPANY_FACTS.lower()


def test_questions_none_sv_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert "uppföljningsfrågor" in S.QUESTIONS_NONE.lower()


# ---------------------------------------------------------------------------
# render.py no longer contains the extracted hardcoded English literals
# ---------------------------------------------------------------------------

def test_render_no_hardcoded_scope_input_mode() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert '"Input mode: Local files only.' not in src
    assert "'Input mode: Local files only." not in src


def test_render_no_hardcoded_holdings_header() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert '"Holdings by weight (user-supplied values, highest first):"' not in src


def test_render_no_hardcoded_sector_header() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert '"Sector exposure:"' not in src


def test_render_no_hardcoded_watchlist_no_items() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert '"No watchlist items loaded."' not in src


def test_render_no_hardcoded_attention_no_items() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert '"No items flagged for immediate attention' not in src


def test_render_no_hardcoded_suitability_profile_provided() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert '"Investor profile: Provided."' not in src


def test_render_no_hardcoded_decisions_no_journal() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert '"No decision journal provided. Open decisions not reviewed."' not in src


def test_render_no_hardcoded_evidence_no_gaps() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert '"No evidence gaps identified from available local inputs."' not in src


def test_render_no_hardcoded_questions_none() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert '"No follow-up questions identified.' not in src


# ---------------------------------------------------------------------------
# English CLI output is unchanged (key body message spot-checks)
# ---------------------------------------------------------------------------

def test_english_output_scope_input_mode() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    assert "Input mode: Local files only. No external data, no live pricing." in r.stdout


def test_english_output_scope_optional_inputs_none() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    assert "Optional inputs: none provided — review uses portfolio and watchlist only" in r.stdout


def test_english_output_portfolio_holdings_header() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    assert "Holdings by weight (user-supplied values, highest first):" in r.stdout


def test_english_output_portfolio_sector_header() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    assert "Sector exposure:" in r.stdout


def test_english_output_portfolio_note_local_only() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    assert "Note: All values are user-supplied. No live pricing or external data used." in r.stdout


def test_english_output_suitability_profile_not_provided() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    # Long line — rich wraps at terminal width; check two stable substrings
    assert "Investor profile: Not provided. Suitability observations" in r.stdout
    assert "not personalized." in r.stdout


def test_english_output_guardrails_engine_deferred() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    assert "Risk and principle guardrail engine wiring is deferred to a later sprint." in r.stdout


def test_english_output_guardrails_principle_guardrail() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    assert "Principle Guardrail: No action is warranted when evidence is incomplete." in r.stdout


def test_english_output_decisions_no_journal() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    assert "No decision journal provided. Open decisions not reviewed." in r.stdout


def test_english_output_questions_no_company_facts() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    # Long line may wrap; check stable prefix
    assert "What company facts are needed before changing the status of any watchlist" in r.stdout


def test_english_output_questions_no_financials() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    assert "Which financial trends should be reviewed before any watchlist decision" in r.stdout


def test_english_output_questions_open_watchlist_gaps() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    assert "What evidence would confirm or weaken the current assumptions for each open" in r.stdout


def test_english_output_suitability_engine_deferred() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    assert "Full suitability evaluation is deferred until engine wiring." in r.stdout


def test_english_output_suitability_note_no_merit_judgment() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    assert "Note: Atlas does not judge investment merit or provide personalized guidance." in r.stdout


# ---------------------------------------------------------------------------
# Swedish CLI output uses new Swedish constants
# ---------------------------------------------------------------------------

def test_swedish_output_scope_input_mode() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Indataläge: Lokala filer enbart." in r.stdout


def test_swedish_output_scope_optional_inputs_none() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Valfria indata: inga angivna" in r.stdout


def test_swedish_output_portfolio_holdings_header() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Innehav efter vikt" in r.stdout


def test_swedish_output_portfolio_sector_header() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Sektorexponering:" in r.stdout


def test_swedish_output_suitability_profile_not_provided() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Investerarprofil: Inte angiven." in r.stdout
    assert "personaliserade" in r.stdout


def test_swedish_output_guardrails_engine_deferred() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Motorkoppling för risk- och principgränser är uppskjuten" in r.stdout


def test_swedish_output_guardrails_principle_guardrail() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Principgräns: Ingen åtgärd är motiverad" in r.stdout


def test_swedish_output_decisions_no_journal() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Ingen beslutsjournal angiven." in r.stdout


def test_swedish_output_questions_no_company_facts() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "företagsfakta" in r.stdout.lower()


def test_swedish_output_no_english_body_leaks() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    # Key extracted English strings must not appear in Swedish output
    assert "Input mode: Local files only." not in r.stdout
    assert "Holdings by weight (user-supplied values, highest first):" not in r.stdout
    assert "Sector exposure:" not in r.stdout
    assert "No decision journal provided. Open decisions not reviewed." not in r.stdout
    assert "Risk and principle guardrail engine wiring is deferred" not in r.stdout
    assert "Principle Guardrail: No action is warranted" not in r.stdout


# ---------------------------------------------------------------------------
# User-provided content passes through unchanged
# ---------------------------------------------------------------------------

def test_user_watchlist_reason_unchanged_english() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    assert "Water infrastructure" in r.stdout


def test_user_watchlist_reason_unchanged_swedish() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Water infrastructure" in r.stdout


# ---------------------------------------------------------------------------
# Canonical values remain English regardless of language
# ---------------------------------------------------------------------------

def test_canonical_ticker_unchanged_swedish() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "XYL" in r.stdout


def test_canonical_ticker_msft_unchanged_swedish() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "MSFT" in r.stdout


# ---------------------------------------------------------------------------
# Infrastructure safety
# ---------------------------------------------------------------------------

def test_no_gettext_in_strings_en() -> None:
    assert "gettext" not in STRINGS_EN.read_text(encoding="utf-8")


def test_no_gettext_in_strings_sv() -> None:
    assert "gettext" not in STRINGS_SV.read_text(encoding="utf-8")


def test_supported_locales_still_en_sv() -> None:
    from atlas.locale_support import _SUPPORTED_LOCALES
    assert _SUPPORTED_LOCALES == frozenset({"en", "sv"})


def test_no_translation_catalogs() -> None:
    import atlas
    pkg = Path(atlas.__file__).parent
    assert not any(pkg.glob("*.po"))
    assert not any(pkg.glob("*.mo"))

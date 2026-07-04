"""Sprint 263 — Weekly Review Section 10 tail message constants tests.

Verifies that the 12 newly extracted Section 10 (Non-Actions / Reasons to Wait)
tail message templates are defined in strings.py and strings_sv.py with exact
expected wording, that render.py no longer contains the hardcoded English
literals, that English CLI output is unchanged, and that Swedish CLI output
uses the new Swedish constants.

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
# English constant values — exact string equality
# ---------------------------------------------------------------------------

def test_nonactions_wait_evidence_gaps_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.NONACTIONS_WAIT_EVIDENCE_GAPS == (
        "{count} evidence gap(s) identified across watchlist items. "
        "Gathering evidence is the appropriate next step."
    )
    assert S.NONACTIONS_WAIT_EVIDENCE_GAPS.format(count=3) == (
        "3 evidence gap(s) identified across watchlist items. "
        "Gathering evidence is the appropriate next step."
    )


def test_nonactions_wait_no_profile_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.NONACTIONS_WAIT_NO_PROFILE == (
        "Investor profile not provided. "
        "Structural suitability assessment is deferred."
    )


def test_nonactions_wait_no_journal_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.NONACTIONS_WAIT_NO_JOURNAL == (
        "Decision journal not provided. "
        "Open decisions and prior context are not available for this review."
    )


def test_nonactions_wait_missing_facts_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.NONACTIONS_WAIT_MISSING_FACTS == (
        "Local company facts missing for {count} ticker(s) ({tickers}): "
        "thesis context is incomplete for these positions."
    )
    assert S.NONACTIONS_WAIT_MISSING_FACTS.format(count=2, tickers="AAPL, MSFT") == (
        "Local company facts missing for 2 ticker(s) (AAPL, MSFT): "
        "thesis context is incomplete for these positions."
    )


def test_nonactions_wait_missing_fins_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.NONACTIONS_WAIT_MISSING_FINS == (
        "Local financial history missing for {count} ticker(s) ({tickers}): "
        "financial context is incomplete for these positions."
    )
    assert S.NONACTIONS_WAIT_MISSING_FINS.format(count=1, tickers="ASML") == (
        "Local financial history missing for 1 ticker(s) (ASML): "
        "financial context is incomplete for these positions."
    )


def test_nonactions_wait_no_company_facts_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.NONACTIONS_WAIT_NO_COMPANY_FACTS == (
        "Company facts not loaded. "
        "Decision-relevant evidence is incomplete."
    )


def test_nonactions_wait_no_financials_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.NONACTIONS_WAIT_NO_FINANCIALS == (
        "Financial history not loaded. "
        "Financial trend analysis is not available."
    )


def test_nonactions_wait_aging_journal_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.NONACTIONS_WAIT_AGING_JOURNAL == (
        "decision journal notes are older than 90 days ({days} days). "
        "Assumptions should be refreshed before changing decision status."
    )
    assert S.NONACTIONS_WAIT_AGING_JOURNAL.format(days=120) == (
        "decision journal notes are older than 90 days (120 days). "
        "Assumptions should be refreshed before changing decision status."
    )


def test_nonactions_wait_research_gaps_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.NONACTIONS_WAIT_RESEARCH_GAPS == (
        "{ticker} research notes contain {count} unresolved evidence gap(s). "
        "Gathering evidence is the appropriate next step."
    )
    assert S.NONACTIONS_WAIT_RESEARCH_GAPS.format(ticker="ASML", count=2) == (
        "ASML research notes contain 2 unresolved evidence gap(s). "
        "Gathering evidence is the appropriate next step."
    )


def test_nonactions_wait_principles_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.NONACTIONS_WAIT_PRINCIPLES == (
        "Stated principles support a measured approach to evidence and decision discipline:"
    )


def test_nonactions_no_action_constraints_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.NONACTIONS_NO_ACTION_CONSTRAINTS == (
        "Stated constraints apply to current portfolio and watchlist decisions:"
    )


def test_nonactions_no_action_informational_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.NONACTIONS_NO_ACTION_INFORMATIONAL == (
        "This review is informational only. "
        "All observations are based on user-supplied local inputs."
    )


# ---------------------------------------------------------------------------
# Swedish constant values — exact string equality
# ---------------------------------------------------------------------------

def test_sv_nonactions_wait_evidence_gaps_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert S.NONACTIONS_WAIT_EVIDENCE_GAPS == (
        "{count} underlagslucka(or) identifierade bland bevakningsposter. "
        "Att samla in underlag är det lämpliga nästa steget."
    )


def test_sv_nonactions_wait_no_profile_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert S.NONACTIONS_WAIT_NO_PROFILE == (
        "Investerarprofil ej angiven. "
        "Strukturell lämplighetsbedömning är uppskjuten."
    )


def test_sv_nonactions_wait_no_journal_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert S.NONACTIONS_WAIT_NO_JOURNAL == (
        "Beslutsjournal ej angiven. "
        "Öppna beslut och tidigare kontext är inte tillgängliga för denna granskning."
    )


def test_sv_nonactions_wait_missing_facts_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert "{count}" in S.NONACTIONS_WAIT_MISSING_FACTS
    assert "{tickers}" in S.NONACTIONS_WAIT_MISSING_FACTS
    formatted = S.NONACTIONS_WAIT_MISSING_FACTS.format(count=2, tickers="AAPL, MSFT")
    assert "2" in formatted
    assert "AAPL, MSFT" in formatted


def test_sv_nonactions_wait_missing_fins_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert "{count}" in S.NONACTIONS_WAIT_MISSING_FINS
    assert "{tickers}" in S.NONACTIONS_WAIT_MISSING_FINS


def test_sv_nonactions_wait_no_company_facts_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert S.NONACTIONS_WAIT_NO_COMPANY_FACTS == (
        "Företagsfakta inte inlästa. "
        "Beslutsrelevant underlag är ofullständigt."
    )


def test_sv_nonactions_wait_no_financials_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert S.NONACTIONS_WAIT_NO_FINANCIALS == (
        "Finansiell historik inte inläst. "
        "Analys av finansiella trender är inte tillgänglig."
    )


def test_sv_nonactions_wait_aging_journal_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert "{days}" in S.NONACTIONS_WAIT_AGING_JOURNAL
    formatted = S.NONACTIONS_WAIT_AGING_JOURNAL.format(days=120)
    assert "120" in formatted


def test_sv_nonactions_wait_research_gaps_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert "{ticker}" in S.NONACTIONS_WAIT_RESEARCH_GAPS
    assert "{count}" in S.NONACTIONS_WAIT_RESEARCH_GAPS
    formatted = S.NONACTIONS_WAIT_RESEARCH_GAPS.format(ticker="ASML", count=2)
    assert "ASML" in formatted
    assert "2" in formatted


def test_sv_nonactions_wait_principles_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert S.NONACTIONS_WAIT_PRINCIPLES == (
        "Angivna principer stödjer ett genomtänkt förhållningssätt till underlag och beslutsdisciplin:"
    )


def test_sv_nonactions_no_action_constraints_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert S.NONACTIONS_NO_ACTION_CONSTRAINTS == (
        "Angivna begränsningar gäller för nuvarande portfölj- och bevakningsbeslut:"
    )


def test_sv_nonactions_no_action_informational_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert S.NONACTIONS_NO_ACTION_INFORMATIONAL == (
        "Denna granskning är informationell enbart. "
        "Alla observationer baseras på användarsupplerade lokala indata."
    )


# ---------------------------------------------------------------------------
# render.py no longer contains hardcoded English Section 10 tails
# ---------------------------------------------------------------------------

def test_render_no_hardcoded_evidence_gaps_tail() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert "evidence gap(s) identified across watchlist items" not in src


def test_render_no_hardcoded_no_profile_tail() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert '"Investor profile not provided.' not in src


def test_render_no_hardcoded_no_journal_tail() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert '"Decision journal not provided.' not in src


def test_render_no_hardcoded_missing_facts_tail() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert "thesis context is incomplete for these positions" not in src


def test_render_no_hardcoded_missing_fins_tail() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert "financial context is incomplete for these positions" not in src


def test_render_no_hardcoded_company_facts_not_loaded_tail() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert '"Company facts not loaded.' not in src


def test_render_no_hardcoded_financials_not_loaded_tail() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert '"Financial history not loaded.' not in src


def test_render_no_hardcoded_aging_journal_tail() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert "Assumptions should be refreshed before changing decision status" not in src


def test_render_no_hardcoded_research_gaps_tail() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert "unresolved evidence gap(s). \\\nGathering evidence" not in src


def test_render_no_hardcoded_principles_tail() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert '"Stated principles support a measured approach' not in src


def test_render_no_hardcoded_constraints_tail() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert '"Stated constraints apply to current portfolio' not in src


def test_render_no_hardcoded_informational_tail() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert '"This review is informational only.' not in src


# ---------------------------------------------------------------------------
# English CLI output unchanged — Section 10 body message spot-checks
# ---------------------------------------------------------------------------

def test_english_output_no_profile_tail() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    assert "Investor profile not provided." in r.stdout


def test_english_output_no_journal_tail() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    assert "Decision journal not provided." in r.stdout


def test_english_output_no_company_facts_tail() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    assert "Company facts not loaded." in r.stdout


def test_english_output_no_financials_tail() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    assert "Financial history not loaded." in r.stdout


def test_english_output_informational_tail() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    assert "This review is informational only." in r.stdout


# ---------------------------------------------------------------------------
# Swedish CLI output uses Swedish Section 10 constants
# ---------------------------------------------------------------------------

def test_swedish_output_no_profile_tail() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Investerarprofil ej angiven." in r.stdout


def test_swedish_output_no_journal_tail() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Beslutsjournal ej angiven." in r.stdout


def test_swedish_output_no_company_facts_tail() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Företagsfakta inte inlästa." in r.stdout


def test_swedish_output_no_financials_tail() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Finansiell historik inte inläst." in r.stdout


def test_swedish_output_informational_tail() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Denna granskning är informationell enbart." in r.stdout


# ---------------------------------------------------------------------------
# Swedish output does NOT contain residual hardcoded English Section 10 tails
# ---------------------------------------------------------------------------

def test_swedish_output_no_residual_english_informational() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "This review is informational only." not in r.stdout


# ---------------------------------------------------------------------------
# Canonical values not translated — label prefixes are locale-aware
# ---------------------------------------------------------------------------

def test_sv_labels_are_swedish_not_english() -> None:
    from atlas.weekly_review import strings_sv as S
    assert "Reason to Wait" not in S.LABEL_REASON_TO_WAIT
    assert "No Action Warranted" not in S.LABEL_NO_ACTION_WARRANTED


# ---------------------------------------------------------------------------
# No gettext, no locale detection
# ---------------------------------------------------------------------------

def test_no_gettext_in_strings_en() -> None:
    src = STRINGS_EN.read_text(encoding="utf-8")
    assert "gettext" not in src
    assert "import locale" not in src


def test_no_gettext_in_strings_sv() -> None:
    src = STRINGS_SV.read_text(encoding="utf-8")
    assert "gettext" not in src
    assert "import locale" not in src


def test_no_gettext_in_render() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert "gettext" not in src

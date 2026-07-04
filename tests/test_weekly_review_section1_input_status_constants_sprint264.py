"""Sprint 264 — Weekly Review Section 6/8 input-status tail constants tests.

Verifies that the 6 newly extracted hardcoded English tail strings visible in
Swedish output are defined as constants in strings.py and strings_sv.py:
  - Section 6 guardrails: 2 × LABEL_EVIDENCE_GAP tails (company facts / financials)
  - Section 8 missing evidence: 4 × LABEL_MISSING_OPTIONAL_INPUT tails

All constants were previously hardcoded English strings leaked into --language sv
output. English output remains unchanged.

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
# English constant values — Section 6 guardrails evidence tails
# ---------------------------------------------------------------------------

def test_guardrails_evidence_no_company_facts_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.GUARDRAILS_EVIDENCE_NO_COMPANY_FACTS == (
        "Company facts not loaded. "
        "Evidence quality cannot be assessed from available inputs."
    )


def test_guardrails_evidence_no_financials_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.GUARDRAILS_EVIDENCE_NO_FINANCIALS == (
        "Financial history not loaded. "
        "Financial trend analysis not available."
    )


# ---------------------------------------------------------------------------
# English constant values — Section 8 missing-input tails
# ---------------------------------------------------------------------------

def test_evidence_missing_profile_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.EVIDENCE_MISSING_PROFILE == "Investor profile not provided."


def test_evidence_missing_journal_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.EVIDENCE_MISSING_JOURNAL == "Decision journal not provided."


def test_evidence_missing_company_facts_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.EVIDENCE_MISSING_COMPANY_FACTS == "Company facts directory not provided."


def test_evidence_missing_financials_constant() -> None:
    from atlas.weekly_review import strings as S
    assert S.EVIDENCE_MISSING_FINANCIALS == "Financial history directory not provided."


# ---------------------------------------------------------------------------
# Swedish constant values — Section 6 guardrails evidence tails
# ---------------------------------------------------------------------------

def test_sv_guardrails_evidence_no_company_facts_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert S.GUARDRAILS_EVIDENCE_NO_COMPANY_FACTS == (
        "Företagsfakta inte inlästa. "
        "Underlagskvalitet kan inte bedömas från tillgängliga indata."
    )


def test_sv_guardrails_evidence_no_financials_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert S.GUARDRAILS_EVIDENCE_NO_FINANCIALS == (
        "Finansiell historik inte inläst. "
        "Analys av finansiella trender är inte tillgänglig."
    )


# ---------------------------------------------------------------------------
# Swedish constant values — Section 8 missing-input tails
# ---------------------------------------------------------------------------

def test_sv_evidence_missing_profile_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert S.EVIDENCE_MISSING_PROFILE == "Investerarprofil saknas."


def test_sv_evidence_missing_journal_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert S.EVIDENCE_MISSING_JOURNAL == "Beslutsjournal saknas."


def test_sv_evidence_missing_company_facts_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert S.EVIDENCE_MISSING_COMPANY_FACTS == "Företagsfakta-katalog saknas."


def test_sv_evidence_missing_financials_constant() -> None:
    from atlas.weekly_review import strings_sv as S
    assert S.EVIDENCE_MISSING_FINANCIALS == "Finansiell historik-katalog saknas."


# ---------------------------------------------------------------------------
# render.py no longer contains extracted hardcoded English tails
# ---------------------------------------------------------------------------

def test_render_no_hardcoded_guardrails_no_company_facts() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert '"Company facts not loaded. \\\nEvidence quality' not in src
    assert '"Company facts not loaded. Evidence quality' not in src
    assert "Evidence quality cannot be assessed from available inputs" not in src


def test_render_no_hardcoded_guardrails_no_financials() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert "Financial trend analysis not available" not in src


def test_render_no_hardcoded_missing_profile() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert '"Investor profile not provided."' not in src


def test_render_no_hardcoded_missing_journal() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert '"Decision journal not provided."' not in src


def test_render_no_hardcoded_missing_company_facts_dir() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert '"Company facts directory not provided."' not in src


def test_render_no_hardcoded_missing_financials_dir() -> None:
    src = RENDER.read_text(encoding="utf-8")
    assert '"Financial history directory not provided."' not in src


# ---------------------------------------------------------------------------
# English CLI output unchanged
# ---------------------------------------------------------------------------

def test_english_output_missing_profile() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    assert "Investor profile not provided." in r.stdout


def test_english_output_missing_journal() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    assert "Decision journal not provided." in r.stdout


def test_english_output_missing_company_facts_dir() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    assert "Company facts directory not provided." in r.stdout


def test_english_output_missing_financials_dir() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    assert "Financial history directory not provided." in r.stdout


def test_english_output_guardrails_no_company_facts() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    assert "Company facts not loaded." in r.stdout


def test_english_output_guardrails_no_financials() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    assert "Financial history not loaded." in r.stdout


# ---------------------------------------------------------------------------
# Swedish CLI output uses Swedish constants (no residual English)
# ---------------------------------------------------------------------------

def test_swedish_output_missing_profile_is_swedish() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Investerarprofil saknas." in r.stdout


def test_swedish_output_missing_journal_is_swedish() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Beslutsjournal saknas." in r.stdout


def test_swedish_output_missing_company_facts_is_swedish() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Företagsfakta-katalog saknas." in r.stdout


def test_swedish_output_missing_financials_is_swedish() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Finansiell historik-katalog saknas." in r.stdout


def test_swedish_output_guardrails_no_company_facts_is_swedish() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Företagsfakta inte inlästa." in r.stdout


def test_swedish_output_guardrails_no_financials_is_swedish() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Finansiell historik inte inläst." in r.stdout


def test_swedish_output_no_residual_english_company_facts_dir() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Company facts directory not provided." not in r.stdout


def test_swedish_output_no_residual_english_financials_dir() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Financial history directory not provided." not in r.stdout


def test_swedish_output_no_residual_english_guardrails_facts() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Evidence quality cannot be assessed from available inputs." not in r.stdout


def test_swedish_output_no_residual_english_guardrails_fins() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Financial trend analysis not available." not in r.stdout


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
# Canonical values remain English
# ---------------------------------------------------------------------------

def test_canonical_section_labels_remain_english_in_english() -> None:
    r = _review()
    assert r.returncode == 0, r.stderr
    assert "Missing Optional Input" in r.stdout
    assert "Evidence Gap" in r.stdout


def test_canonical_section_labels_are_swedish_in_swedish() -> None:
    r = _review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "Missing Optional Input" not in r.stdout
    assert "Evidence Gap" not in r.stdout


# ---------------------------------------------------------------------------
# No gettext, no string catalogs, no runtime locale detection
# ---------------------------------------------------------------------------

def test_no_gettext_in_strings_en() -> None:
    assert "gettext" not in STRINGS_EN.read_text(encoding="utf-8")
    assert "import locale" not in STRINGS_EN.read_text(encoding="utf-8")


def test_no_gettext_in_strings_sv() -> None:
    assert "gettext" not in STRINGS_SV.read_text(encoding="utf-8")
    assert "import locale" not in STRINGS_SV.read_text(encoding="utf-8")


def test_no_gettext_in_render() -> None:
    assert "gettext" not in RENDER.read_text(encoding="utf-8")

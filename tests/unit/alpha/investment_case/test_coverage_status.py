"""Coverage truth: why a Case is silent, and what the investor is told.

The failure this guards against is specific and was live. A Swedish
portfolio's ABB, Volvo, Sandvik, Atlas Copco and Novo Nordisk holdings --
correct tickers, real listed equities -- were each shown a message telling
the investor to check the ticker, or suggesting the holding might be a
cryptocurrency. Atlas never knew either of those things. It only knew that
no connected source had answered, which is a fact about Atlas's reach.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from atlas.alpha.investment_case.coverage_status import CoverageStatus, describe_coverage

REPO = Path(__file__).resolve().parents[4]
TRANSLATIONS = REPO / "frontend/src/i18n/translations"


def _describe(**overrides) -> CoverageStatus:
    base = dict(
        ticker="ABB",
        resolution_was_no_match=False,
        has_company_profile=True,
        has_market_snapshot=True,
        financial_statement_count=12,
        analysis_is_withheld=False,
    )
    base.update(overrides)
    return describe_coverage(**base)


# --- Classification ----------------------------------------------------


def test_a_fully_evidenced_case_needs_no_explanation() -> None:
    assert _describe() is CoverageStatus.SUFFICIENT_EVIDENCE


def test_no_source_returned_an_identity_is_identity_unresolved() -> None:
    assert _describe(
        resolution_was_no_match=True, has_company_profile=False,
        has_market_snapshot=False, financial_statement_count=0,
    ) is CoverageStatus.IDENTITY_UNRESOLVED


def test_an_identified_security_with_no_statements_is_pending_not_unknown() -> None:
    """The Novo Nordisk case: Atlas had identified it as Novo Nordisk A/S
    and still had no financial history. That is waiting, not a mystery."""
    assert _describe(
        resolution_was_no_match=False, financial_statement_count=0,
    ) is CoverageStatus.EVIDENCE_PENDING


def test_evidence_that_exists_but_cannot_conclude_is_partial() -> None:
    assert _describe(
        financial_statement_count=4, analysis_is_withheld=True,
    ) is CoverageStatus.PARTIAL_EVIDENCE


def test_identity_is_decided_before_anything_else() -> None:
    """Counting statements is meaningless while Atlas does not know which
    company it is looking at."""
    assert _describe(
        resolution_was_no_match=True, has_company_profile=False,
        has_market_snapshot=False, financial_statement_count=99,
    ) is CoverageStatus.IDENTITY_UNRESOLVED


def test_a_profile_overrides_a_stale_no_match() -> None:
    """A recorded NO_MATCH is not permanent: if a source has since returned
    a profile, the security is identified."""
    assert _describe(
        resolution_was_no_match=True, has_company_profile=True,
        financial_statement_count=0,
    ) is CoverageStatus.EVIDENCE_PENDING


def test_a_case_with_no_ticker_is_unresolved() -> None:
    assert _describe(ticker=None) is CoverageStatus.IDENTITY_UNRESOLVED


def test_coverage_never_claims_a_venue_or_an_instrument_type() -> None:
    """Distinguishing 'listed somewhere Atlas does not cover' from 'not a
    company' would mean guessing which venue a symbol belongs to -- and a
    guess is what produced the message this module exists to remove."""
    values = {status.value for status in CoverageStatus}
    for forbidden in ("source_not_covered", "unsupported_instrument", "crypto", "commodity"):
        assert forbidden not in values


# --- The copy ----------------------------------------------------------


@pytest.mark.parametrize("language", ["en", "sv"])
def test_a_silent_case_is_never_blamed_on_the_investors_ticker(language: str) -> None:
    text = (TRANSLATIONS / f"{language}.ts").read_text()
    match = re.search(r'"investmentCase\.hero\.noProviderData":\s*\n?\s*"([^"]*)"', text)
    assert match, f"{language}: noProviderData copy not found"
    copy = match.group(1).lower()

    blaming = {
        "en": ["check that the ticker", "ticker is correct", "cryptocurrency", "commodity"],
        "sv": ["kontrollera att tickern", "kryptovaluta", "råvara"],
    }[language]
    for phrase in blaming:
        assert phrase not in copy, (
            f"{language}: coverage copy still says {phrase!r}. Atlas does not know that the "
            "ticker is wrong or that the holding is a cryptocurrency -- it only knows that no "
            "connected source answered."
        )


@pytest.mark.parametrize("language", ["en", "sv"])
def test_the_copy_says_what_atlas_actually_knows(language: str) -> None:
    text = (TRANSLATIONS / f"{language}.ts").read_text()
    match = re.search(r'"investmentCase\.hero\.noProviderData":\s*\n?\s*"([^"]*)"', text)
    copy = match.group(1)
    expected = {"en": ["connected data sources", "SEC"], "sv": ["datakällor", "SEC"]}[language]
    for phrase in expected:
        assert phrase in copy, f"{language}: copy should name Atlas's own sources ({phrase!r})"


@pytest.mark.parametrize("language", ["en", "sv"])
def test_every_coverage_state_has_copy_in_both_languages(language: str) -> None:
    text = (TRANSLATIONS / f"{language}.ts").read_text()
    for key in ("investmentCase.coverage.identityUnresolved",
                "investmentCase.coverage.evidencePending",
                "investmentCase.coverage.partialEvidence",
                "coverage.badge.identityUnresolved",
                "coverage.badge.evidencePending",
                "coverage.badge.partialEvidence",
                "coverage.notAnalysed.hint"):
        assert f'"{key}"' in text, f"{language}: missing {key}"


def test_the_not_analysed_hint_separates_coverage_from_opinion() -> None:
    """A holding Atlas cannot analyse must never read as a holding Atlas
    dislikes."""
    text = (TRANSLATIONS / "en.ts").read_text()
    match = re.search(r'"coverage\.notAnalysed\.hint":\s*"([^"]*)"', text)
    assert match
    assert "not a negative" in match.group(1).lower()

"""Knowing which security it is, and having nothing to say about it.

This state could not honestly exist before. Telling "Atlas has no source
for this venue" apart from "Atlas has no idea what this is" required
knowing the venue, and the only way to know it was to guess from a ticker
-- the guess that produced the "check your ticker may be wrong" message
these states were written to remove.

A holding that arrives with an ISIN now resolves to a specific security
with a proven venue, so the distinction is demonstrable, and the promise
implied by "evidence pending" stops being made to holdings whose evidence
is never coming.
"""
from __future__ import annotations

import pytest

from atlas.alpha.investment_case.coverage_status import CoverageStatus, describe_coverage


def coverage(**overrides) -> CoverageStatus:
    args = dict(
        ticker="VOLV-B", resolution_was_no_match=False, has_company_profile=True,
        has_market_snapshot=True, financial_statement_count=0, analysis_is_withheld=True,
        listing_mics=frozenset({"XSTO"}),
    )
    args.update(overrides)
    return describe_coverage(**args)


def test_a_resolved_stockholm_security_with_no_statements_is_uncovered() -> None:
    assert coverage() is CoverageStatus.SOURCE_NOT_COVERED


@pytest.mark.parametrize("mic", ["XSTO", "XPAR", "XCSE", "XTAI"])
def test_every_venue_behind_the_unresolved_holdings_is_uncovered(mic) -> None:
    assert coverage(listing_mics=frozenset({mic})) is CoverageStatus.SOURCE_NOT_COVERED


@pytest.mark.parametrize("mic", ["XNAS", "XNYS"])
def test_a_us_listing_with_no_statements_is_still_merely_pending(mic) -> None:
    """Waiting is a reasonable expectation there, because a source that
    reaches that venue is connected."""
    assert coverage(listing_mics=frozenset({mic})) is CoverageStatus.EVIDENCE_PENDING


def test_a_cross_listed_security_is_covered_if_any_venue_is() -> None:
    """AstraZeneca trades in London and New York. One reachable venue is
    enough, and claiming otherwise would hide statements Atlas can get."""
    assert coverage(listing_mics=frozenset({"XLON", "XNYS"})) is CoverageStatus.EVIDENCE_PENDING


def test_an_unknown_venue_is_not_evidence_of_an_uncovered_one() -> None:
    """No security master entry means Atlas does not know where this
    trades -- which is not the same as knowing it trades somewhere
    unreachable. The weaker, older answer is kept."""
    assert coverage(listing_mics=None) is CoverageStatus.EVIDENCE_PENDING
    assert coverage(listing_mics=frozenset()) is CoverageStatus.EVIDENCE_PENDING


def test_identity_is_still_asked_about_first() -> None:
    """A holding Atlas cannot name stays unresolved however uncovered its
    venue might be -- naming the venue of a security you cannot identify
    is the guess this module exists to refuse.

    Both cases below are ones where identity is genuinely absent: no
    ticker at all, or a failed resolution with nothing since to replace
    it. A failed resolution that *has* been replaced -- by a profile or by
    a security master entry -- is a different case, covered below.
    """
    assert coverage(ticker=None) is CoverageStatus.IDENTITY_UNRESOLVED
    assert coverage(resolution_was_no_match=True, has_company_profile=False,
                    has_market_snapshot=False,
                    listing_mics=None) is CoverageStatus.IDENTITY_UNRESOLVED


def test_real_statements_outrank_the_venue_table() -> None:
    """If evidence actually exists, where it trades is beside the point."""
    assert coverage(financial_statement_count=7) is CoverageStatus.PARTIAL_EVIDENCE
    assert coverage(financial_statement_count=7,
                    analysis_is_withheld=False) is CoverageStatus.SUFFICIENT_EVIDENCE


def test_the_existing_states_are_unchanged_without_the_new_input() -> None:
    """Every existing caller that passes no venue gets exactly what it got
    before -- which is why the current Cases cannot move."""
    before = describe_coverage(
        ticker="MSFT", resolution_was_no_match=False, has_company_profile=True,
        has_market_snapshot=True, financial_statement_count=0, analysis_is_withheld=True)
    assert before is CoverageStatus.EVIDENCE_PENDING


# --- A stale NO_MATCH must not outlive the evidence that beat it -------


def test_a_security_master_entry_overrides_a_stale_no_match() -> None:
    """Those NO_MATCH records were written by ticker-based attempts that
    failed for want of an identifier the import did not keep. Once a
    holding has been resolved to a security with a known venue, "no source
    recognised this symbol" is the answer to an older, weaker question --
    and leaving it in charge would mean a correctly identified Volvo B
    still reported as unidentified.
    """
    assert coverage(resolution_was_no_match=True, has_company_profile=False,
                    has_market_snapshot=False) is CoverageStatus.SOURCE_NOT_COVERED


def test_a_stale_no_match_still_wins_when_nothing_has_replaced_it() -> None:
    """The holdings nobody has re-imported. No venue is known for them, so
    the honest answer is still that Atlas does not know what they are."""
    for mics in (None, frozenset()):
        assert coverage(resolution_was_no_match=True, has_company_profile=False,
                        has_market_snapshot=False,
                        listing_mics=mics) is CoverageStatus.IDENTITY_UNRESOLVED

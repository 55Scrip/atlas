"""Why a Case has no analysis -- stated as a fact about Atlas, not about
the holding.

A Case can be silent for several unrelated reasons, and until now they all
arrived at the screen as one boolean. The message that boolean produced told
the investor to check that their ticker was correct, or suggested the holding
might be a cryptocurrency. For a Swedish portfolio that message appeared on
ABB, Volvo, Sandvik, Atlas Copco and Novo Nordisk -- correct tickers, real
listed equities, every one of them.

The underlying fact was never about the ticker. `NO_MATCH` is recorded when
no connected provider returns an identity-bearing candidate, which happens
when Atlas's sources do not cover the venue a holding trades on -- and,
as a live rehearsal showed, also when a provider simply fails. Neither is
evidence that the investor typed something wrong.

So these states say only what Atlas can actually prove:

* `IDENTITY_UNRESOLVED` -- a resolution attempt ran and no connected source
  recognised the symbol. Atlas cannot tell, from this alone, whether the
  holding trades somewhere it does not cover or is not a company at all, so
  it claims neither.
* `EVIDENCE_PENDING` -- the security is identified; the financial evidence
  simply has not been gathered yet. Waiting is the right expectation.
* `PARTIAL_EVIDENCE` -- some evidence exists but not enough to conclude.
  Which dimensions are missing is already reported elsewhere.
* `SOURCE_NOT_COVERED` -- Atlas knows exactly which security this is, and
  none of its connected sources carries financial statements for the venue
  it trades on. A fact about Atlas's reach, stated as one.
* `SUFFICIENT_EVIDENCE` -- nothing to explain.

`SOURCE_NOT_COVERED` was deliberately absent when these states were first
written, and the reason it could be added is worth recording: telling it
apart from "not a company" used to require guessing which venue a symbol
belonged to, and a guess is what produced the message this module exists to
remove. It is no longer a guess. A holding that arrives with an ISIN now
resolves to a specific security with a proven venue, so "Volvo B trades on
Nasdaq Stockholm and Atlas has no fundamentals source for Stockholm" is
something Atlas can demonstrate rather than infer.

The state is therefore reachable only through proven identity. A holding
Atlas cannot name stays `IDENTITY_UNRESOLVED`, because for that one the
honest answer is still that Atlas does not know what it is looking at.
"""
from __future__ import annotations

from enum import Enum

__all__ = ["CoverageStatus", "describe_coverage"]


class CoverageStatus(str, Enum):
    IDENTITY_UNRESOLVED = "identity_unresolved"
    SOURCE_NOT_COVERED = "source_not_covered"
    EVIDENCE_PENDING = "evidence_pending"
    PARTIAL_EVIDENCE = "partial_evidence"
    SUFFICIENT_EVIDENCE = "sufficient_evidence"


#: The venues Atlas's connected fundamentals sources actually reach. SEC
#: EDGAR carries SEC registrants and Alpha Vantage's fundamentals coverage
#: is US-listed equities; neither has ever returned a statement for a
#: Stockholm, Paris, Copenhagen or Taipei listing.
#:
#: A closed list of what is covered, rather than a list of what is not:
#: being absent from it means "no connected source has been shown to reach
#: this venue", which is the claim that can be defended. Connecting a
#: European provider is what would extend it, and that is a deliberate
#: change rather than a silent one.
_VENUES_WITH_A_FUNDAMENTALS_SOURCE: frozenset[str] = frozenset(
    {"XNAS", "XNYS", "XASE", "ARCX", "BATS", "OTCM"}
)


def describe_coverage(
    *,
    ticker: str | None,
    resolution_was_no_match: bool,
    has_company_profile: bool,
    has_market_snapshot: bool,
    financial_statement_count: int,
    analysis_is_withheld: bool,
    listing_mics: frozenset[str] | None = None,
) -> CoverageStatus:
    """Classify why this Case is (or is not) able to conclude.

    Order matters: identity is asked about first, because everything below it
    is meaningless when Atlas does not know which company it is looking at.

    `resolution_was_no_match` is the only identity input, and it is read as
    what it is -- "no connected source returned a candidate" -- never as a
    judgement about the symbol the investor supplied.
    """
    if ticker is None:
        return CoverageStatus.IDENTITY_UNRESOLVED
    # A security master entry overrides a stale `NO_MATCH`, for the same
    # reason a company profile already does, only more strongly: those
    # records were written by ticker-based attempts that failed for want of
    # an identifier the import did not keep. Once a holding has been
    # resolved to a security with a known venue, "no source recognised this
    # symbol" is a fact about an older, weaker question.
    identified_in_the_security_master = bool(listing_mics)
    if (
        resolution_was_no_match
        and not has_company_profile
        and not has_market_snapshot
        and not identified_in_the_security_master
    ):
        return CoverageStatus.IDENTITY_UNRESOLVED
    if financial_statement_count == 0:
        # Identity is established -- something recognised this security. The
        # question left is whether waiting would ever help.
        if listing_mics and not (listing_mics & _VENUES_WITH_A_FUNDAMENTALS_SOURCE):
            # Every venue this security is listed on is one no connected
            # source reaches. Evidence is not pending; it is not coming, and
            # saying "pending" would promise a wait that never ends.
            return CoverageStatus.SOURCE_NOT_COVERED
        # Either Atlas knows a covered venue for it, or it knows no venue at
        # all -- and an unknown venue is not evidence of an uncovered one.
        return CoverageStatus.EVIDENCE_PENDING
    if analysis_is_withheld:
        return CoverageStatus.PARTIAL_EVIDENCE
    return CoverageStatus.SUFFICIENT_EVIDENCE

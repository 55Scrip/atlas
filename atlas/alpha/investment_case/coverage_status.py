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
* `SUFFICIENT_EVIDENCE` -- nothing to explain.

Deliberately absent is a "source not covered" state. Distinguishing that
from "not a company" would mean guessing which venue a symbol belongs to,
and a guess is what produced the message this module exists to remove. The
copy for `IDENTITY_UNRESOLVED` instead says plainly which sources Atlas has,
and lets the investor draw the conclusion Atlas has not earned.
"""
from __future__ import annotations

from enum import Enum

__all__ = ["CoverageStatus", "describe_coverage"]


class CoverageStatus(str, Enum):
    IDENTITY_UNRESOLVED = "identity_unresolved"
    EVIDENCE_PENDING = "evidence_pending"
    PARTIAL_EVIDENCE = "partial_evidence"
    SUFFICIENT_EVIDENCE = "sufficient_evidence"


def describe_coverage(
    *,
    ticker: str | None,
    resolution_was_no_match: bool,
    has_company_profile: bool,
    has_market_snapshot: bool,
    financial_statement_count: int,
    analysis_is_withheld: bool,
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
    if resolution_was_no_match and not has_company_profile and not has_market_snapshot:
        return CoverageStatus.IDENTITY_UNRESOLVED
    if financial_statement_count == 0:
        # Identity is established -- something recognised this security -- so
        # the honest expectation is that evidence is still being gathered,
        # not that the holding is unknowable.
        return CoverageStatus.EVIDENCE_PENDING
    if analysis_is_withheld:
        return CoverageStatus.PARTIAL_EVIDENCE
    return CoverageStatus.SUFFICIENT_EVIDENCE

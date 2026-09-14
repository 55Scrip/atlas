"""The current share-count read model (Current Share-Count Evidence v1).

Descriptive and diagnostic only: nothing that values, recommends or
narrates reads it. It answers "what is this security's latest dated
share count, as the SEC filings Atlas holds state it, as of a given day"
and compares that with the market-data provider's `SharesOutstanding`.

**Temporal.** A count is visible on `evaluated_on` only when both its own
as-of date and its filing date are on or before that day. The latest
as-of date wins (then the latest filing). If the filings Atlas holds give
that date more than one value, or a withheld one, the reading is a
conflict: nothing is chosen, least of all the value nearest the provider.

**The provider is a comparator, never truth.** Its scope is undocumented,
and Atlas records neither the value's as-of date nor whether a price-only
refresh carried it forward unasked (`PROVIDER_FRESHNESS_UNDETERMINED`).
The cross-check reports both sides and their ratio; it never alters the
SEC evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

from atlas.alpha.security_share_evidence.models import (
    CURRENT_COVER_SHARE_COUNT,
    CurrentShareCountEvidence,
    ShareClassLinkKind,
)

__all__ = [
    "PROVIDER_FRESHNESS_UNDETERMINED",
    "CurrentShareStatus",
    "CurrentShareReading",
    "ProviderShareCrossCheck",
    "read_current_shares",
    "cross_check",
]

#: Atlas stores the provider's value and when the snapshot was written --
#: not whether the provider was asked for it then, or when it was true.
PROVIDER_FRESHNESS_UNDETERMINED = "undetermined"


class CurrentShareStatus(str, Enum):
    #: The latest eligible count is proven to be this security's, and single-valued.
    LINKED = "linked"
    #: The latest eligible count disagrees with itself: withheld.
    CONFLICT = "conflict"
    #: The filer's cover counts exist but none is proven to be this security's.
    AMBIGUOUS = "ambiguous"
    #: No current cover count for this security's filer.
    MISSING = "missing"


@dataclass(frozen=True)
class CurrentShareReading:
    ticker: str
    status: CurrentShareStatus
    evidence: CurrentShareCountEvidence | None
    evaluated_on: date
    as_of_age_days: int | None
    filing_age_days: int | None


def _visible(e: CurrentShareCountEvidence, on: date) -> bool:
    # A period-end count is another evidence type: never a current count.
    return e.evidence_type == CURRENT_COVER_SHARE_COUNT and e.filing_date <= on and e.as_of <= on


def read_current_shares(
    ticker: str,
    joined: tuple[CurrentShareCountEvidence, ...],
    issuer_evidence: tuple[CurrentShareCountEvidence, ...],
    *,
    evaluated_on: date,
) -> CurrentShareReading:
    """`joined`: the counts this ticker's identity joins (proven links);
    `issuer_evidence`: every count its filer has (to tell AMBIGUOUS from MISSING)."""
    visible = [e for e in joined if _visible(e, evaluated_on)]
    if visible:
        latest_as_of = max(e.as_of for e in visible)
        same_day = [e for e in visible if e.as_of == latest_as_of]
        values = {e.shares for e in same_day}
        chosen = max(same_day, key=lambda e: (e.filing_date, e.accession, e.context_id))
        if any(not e.usable for e in same_day) or len(values) != 1:
            return CurrentShareReading(ticker, CurrentShareStatus.CONFLICT, None, evaluated_on, None, None)
        return CurrentShareReading(ticker, CurrentShareStatus.LINKED, chosen, evaluated_on,
                                   (evaluated_on - chosen.as_of).days, (evaluated_on - chosen.filing_date).days)
    unproven = [e for e in issuer_evidence if _visible(e, evaluated_on)
                and e.link_kind is not ShareClassLinkKind.PROVEN_BY_SHARED_DIMENSION]
    status = CurrentShareStatus.AMBIGUOUS if unproven else CurrentShareStatus.MISSING
    return CurrentShareReading(ticker, status, None, evaluated_on, None, None)


@dataclass(frozen=True)
class ProviderShareCrossCheck:
    ticker: str
    provider_shares: float | None
    provider_written_at: datetime | None
    provider_freshness: str
    sec_status: CurrentShareStatus
    sec_shares: float | None
    sec_as_of: date | None
    sec_filing_date: date | None
    ratio: float | None
    difference: float | None


def cross_check(reading: CurrentShareReading, provider_shares: float | None,
                provider_written_at: datetime | None) -> ProviderShareCrossCheck:
    """Provider ÷ SEC, reported as found; the SEC reading is returned untouched."""
    sec = reading.evidence.shares if reading.evidence is not None else None
    ratio = provider_shares / sec if provider_shares and sec else None
    return ProviderShareCrossCheck(
        ticker=reading.ticker, provider_shares=provider_shares, provider_written_at=provider_written_at,
        provider_freshness=PROVIDER_FRESHNESS_UNDETERMINED, sec_status=reading.status, sec_shares=sec,
        sec_as_of=reading.evidence.as_of if reading.evidence else None,
        sec_filing_date=reading.evidence.filing_date if reading.evidence else None,
        ratio=ratio, difference=(provider_shares - sec) if provider_shares and sec else None,
    )

"""The persisted shape of security-level share-class evidence.

Filing-level and issuer-scoped: an observation names the SEC filer (CIK),
the filing (accession), the class member and -- only when that filing
proves it -- the trading symbol and exchange its own cover page ties to the
member. It carries no Atlas identity: which Atlas security an observation
belongs to is decided when it is read (CIK + symbol + MIC, see
`repository.py`), so a later change to the security master never leaves a
stale link behind, and two Atlas issuers that share one SEC filer are
never merged -- the CIK travels with the evidence instead.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import ClassVar

__all__ = [
    "ShareClassLinkKind",
    "SecurityShareFiling",
    "SecurityShareCountObservation",
    "HISTORICAL_PERIOD_END_SHARE_COUNT",
    "CURRENT_COVER_SHARE_COUNT",
    "CurrentShareScope",
    "CurrentShareFiling",
    "CurrentShareCountEvidence",
]

#: The two share-count evidence types. Neither ever satisfies a query for
#: the other: they live in separate tables behind separate readers.
HISTORICAL_PERIOD_END_SHARE_COUNT = "historical_period_end_share_count"
CURRENT_COVER_SHARE_COUNT = "current_cover_share_count"


class ShareClassLinkKind(str, Enum):
    """What one filing proves about one class member (the values of
    `business_data_providers.sec_edgar_share_classes.LinkKind`, pinned
    equal by a test). No continuity kind exists: a link is proven inside
    a filing or not at all."""

    PROVEN_BY_SHARED_DIMENSION = "proven_by_shared_dimension"
    AMBIGUOUS = "ambiguous"
    NO_LINK = "no_link"


@dataclass(frozen=True)
class SecurityShareFiling:
    """One annual filing, processed completely. Its presence (at the
    current parser version) is what makes a re-run skip the filing."""

    issuer_cik: str
    accession: str
    form: str
    filing_date: date
    fiscal_period: str | None
    document_period_end: date | None
    instance_url: str
    cover_rows: int
    dimensioned_cover_rows: int
    observations: int
    proven: int
    ambiguous: int
    no_link: int
    conflicts: int
    parser_version: str
    processed_at: datetime


@dataclass(frozen=True)
class SecurityShareCountObservation:
    """One class member's outstanding shares at one annual period end, as
    one filing reports it. `shares` is `None` when the filing reports
    disagreeing values for the member and date (`conflict`): withheld,
    never resolved. The cover fields are set only for a
    `PROVEN_BY_SHARED_DIMENSION` link."""

    issuer_cik: str
    accession: str
    form: str
    filing_date: date
    fiscal_period: str | None
    document_period_end: date | None
    period_end: date
    class_axis: str
    class_member: str
    shares: float | None
    conflict: bool
    source_concept: str
    context_id: str
    link_kind: ShareClassLinkKind
    cover_title: str | None
    cover_symbol: str | None
    cover_exchange: str | None
    cover_mic: str | None
    parser_version: str
    recorded_at: datetime

    evidence_type: ClassVar[str] = HISTORICAL_PERIOD_END_SHARE_COUNT

    @property
    def usable(self) -> bool:
        return (self.link_kind is ShareClassLinkKind.PROVEN_BY_SHARED_DIMENSION
                and not self.conflict and self.shares is not None and self.shares > 0
                and self.filing_date > self.period_end)


class CurrentShareScope(str, Enum):
    #: One class of the filer's stock (one class-axis member).
    CLASS = "class"
    #: The filer's common stock as one count, in a filing reporting no classes.
    ISSUER = "issuer"


@dataclass(frozen=True)
class CurrentShareFiling:
    """One 10-K/10-Q whose cover page was read, completely."""

    issuer_cik: str
    accession: str
    form: str
    filing_date: date
    document_period_end: date | None
    fiscal_period: str | None
    instance_url: str
    cover_rows: int
    share_classes_reported: bool
    counts: int
    proven: int
    ambiguous: int
    no_link: int
    conflicts: int
    parser_version: str
    retrieved_at: datetime
    recorded_at: datetime


@dataclass(frozen=True)
class CurrentShareCountEvidence:
    """A current share count as one filing's cover page states it.

    Three dates, never substituted for one another: `as_of` is the count's
    own instant (the cover's "as of" date), `filing_date` is when SEC
    received the filing, `retrieved_at` is when Atlas fetched it. Scope and
    class are the filing's own; which Atlas security the count belongs to
    is decided on read (CIK + symbol + MIC), exactly as for historical
    counts. Issuer, class and scope are kept so that a later economic
    market-cap analysis can use them -- nothing here aggregates classes."""

    issuer_cik: str
    accession: str
    form: str
    filing_date: date
    document_period_end: date | None
    as_of: date
    scope: CurrentShareScope
    class_axis: str | None
    class_member: str | None
    shares: float | None
    unit: str
    #: Reported precision (`decimals`): `"INF"` exact, `"-6"` rounded to millions.
    decimals: str | None
    conflict: bool
    concept: str
    context_id: str
    link_kind: ShareClassLinkKind
    cover_title: str | None
    cover_symbol: str | None
    cover_exchange: str | None
    cover_mic: str | None
    parser_version: str
    retrieved_at: datetime
    recorded_at: datetime

    evidence_type: ClassVar[str] = CURRENT_COVER_SHARE_COUNT

    @property
    def usable(self) -> bool:
        return (self.link_kind is ShareClassLinkKind.PROVEN_BY_SHARED_DIMENSION and not self.conflict
                and self.unit == "shares" and self.shares is not None and math.isfinite(self.shares)
                and self.shares > 0 and self.as_of <= self.filing_date)

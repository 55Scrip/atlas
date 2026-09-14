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

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

__all__ = ["ShareClassLinkKind", "SecurityShareFiling", "SecurityShareCountObservation"]


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

    @property
    def usable(self) -> bool:
        return (self.link_kind is ShareClassLinkKind.PROVEN_BY_SHARED_DIMENSION
                and not self.conflict and self.shares is not None and self.shares > 0
                and self.filing_date > self.period_end)

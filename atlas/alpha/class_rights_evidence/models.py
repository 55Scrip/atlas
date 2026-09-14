"""Domain model for class economic-rights evidence.

Every observation keeps the strength of its source (`CONTRACTUAL` for a
filed statement under the governing instrument, `FILING_STATEMENT` for any
other filed statement, `STRUCTURED_FILING` for an XBRL fact,
`ACCOUNTING_CORROBORATION` for per-class EPS -- never promoted), and the
span it holds for: `effective_from`..`effective_to`, an instant or the
periods its filing presents. A reader applies it inside that span, or
forward from it -- never backward.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import ClassVar

__all__ = ["CLASS_ECONOMIC_RIGHTS", "RightKind", "EvidenceStrength", "ClassRightsFiling", "ClassRightsObservation"]

CLASS_ECONOMIC_RIGHTS = "class_economic_rights"


class RightKind(str, Enum):
    EARNINGS_PER_SHARE = "earnings_per_share"
    CONVERSION_RATE = "conversion_rate"
    CONVERSION_RATIO_RANGE = "conversion_ratio_range"
    AS_CONVERTED_SHARES = "as_converted_shares"
    PREFERRED_SHARES_OUTSTANDING = "preferred_shares_outstanding"
    PREFERRED_SHARES_ISSUED = "preferred_shares_issued"
    LIQUIDATION_PREFERENCE = "liquidation_preference"
    PREFERRED_DIVIDEND_RATE = "preferred_dividend_rate"
    CLASS_INVENTORY = "class_inventory"
    ECONOMIC_PARITY = "economic_parity"
    CONVERTIBLE_INTO = "convertible_into"
    VOTES_PER_SHARE = "votes_per_share"
    NON_VOTING = "non_voting"
    SENIOR_TO_COMMON = "senior_to_common"
    NOT_CONVERTIBLE = "not_convertible"


class EvidenceStrength(str, Enum):
    CONTRACTUAL = "contractual"
    FILING_STATEMENT = "filing_statement"
    STRUCTURED_FILING = "structured_filing"
    ACCOUNTING_CORROBORATION = "accounting_corroboration"


@dataclass(frozen=True)
class ClassRightsFiling:
    """One 10-K/10-Q whose rights evidence was read, completely."""

    issuer_cik: str
    accession: str
    form: str
    filing_date: date
    document_period_end: date | None
    presented_from: date | None
    instance_url: str
    observations: int
    parser_version: str
    retrieved_at: datetime
    recorded_at: datetime


@dataclass(frozen=True)
class ClassRightsObservation:
    issuer_cik: str
    accession: str
    form: str
    filing_date: date
    observation_key: str
    kind: RightKind
    strength: EvidenceStrength
    subject_member: str | None
    subject_label: str | None
    target_member: str | None
    target_label: str | None
    related_members: tuple[str, ...]
    related_labels: tuple[str, ...]
    value: float | None
    value_low: float | None
    value_high: float | None
    unit: str | None
    decimals: str | None
    equity_kind: str | None
    effective_from: date
    effective_to: date
    concept: str
    context_id: str
    excerpt: str | None
    parser_version: str
    retrieved_at: datetime
    recorded_at: datetime

    evidence_type: ClassVar[str] = CLASS_ECONOMIC_RIGHTS

    def holds_on(self, on: date) -> bool:
        return self.effective_from <= on <= self.effective_to

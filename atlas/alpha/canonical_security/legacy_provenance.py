"""Repairing identity provenance on records that predate the Identity
Gate (Legacy Identity Provenance Backfill).

**The problem.** 570 of 2506 stored `BusinessRecord`s -- 22.7% -- carry
an authoritative SEC CIK and no `canonical_security_id` at all. They were
ingested before the gate stamped identity onto records. Atlas therefore
holds real, authoritative evidence about who those filings belong to and
cannot connect it to the issuer model.

**The rule, and the one thing it must never become.** A record may be
attached to an issuer when its own CIK matches a CIK that some
*already-linked* record has independently established for that issuer.
The bridge is the identifier, never the ticker. Matching
`business_record.company == canonical_security.native_ticker` would look
identical in the GOOG case and would be exactly the shortcut that turns
`SU.PA` into Suncor Energy, so it is refused by construction: nothing in
this module reads a ticker or a company name.

**Issuer provenance is not security provenance.** A CIK proves which
filer produced a filing. It does not prove which *listing* generated the
record -- Alphabet files one 10-K, and both `GOOG` and `GOOGL` are
covered by it. So the repair sets `canonical_issuer_id` and deliberately
leaves `canonical_security_id` null. Claiming a security here would
invent a fact, and for a price or market snapshot it would be actively
dangerous: the issuer does not identify which listing's price it is.

**Security-specific documents are excluded entirely.** Only issuer-level
document kinds are eligible; a market snapshot never receives issuer
provenance, because there is no sense in which a price belongs to a
company rather than to a listing.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from atlas.alpha.canonical_security.issuer_cik import normalize_cik

__all__ = [
    "ISSUER_LEVEL_DOCUMENT_TYPES",
    "LegacyRepairOutcome",
    "LegacyRecordRepair",
    "build_cik_to_issuer_index",
    "plan_legacy_repair",
]

#: Document kinds whose content genuinely belongs to the *company*, so
#: attaching them to an issuer without naming a security is honest.
#:
#: `market_data_snapshot` is deliberately absent, and so is anything
#: else priced or venue-specific: a price belongs to a listing, and
#: issuer-level provenance would let it cross a security boundary --
#: precisely the failure the issuer/security split exists to prevent.
ISSUER_LEVEL_DOCUMENT_TYPES: frozenset[str] = frozenset(
    {"financial_statement", "company_filing", "annual_report", "transcript"}
)


class LegacyRepairOutcome(str, Enum):
    """Why one record can or cannot be repaired without a provider call."""

    #: Its CIK resolves to exactly one issuer via already-linked records.
    ISSUER_PROVEN = "issuer_proven"
    #: Already has security provenance; nothing to repair.
    ALREADY_LINKED = "already_linked"
    #: Issuer-level evidence exists, but the record is security-specific
    #: (a price), so issuer provenance would be the wrong claim.
    SECURITY_SPECIFIC_EXCLUDED = "security_specific_excluded"
    #: Has a CIK, but no linked record anywhere establishes that CIK for
    #: an issuer. Repairable only after an identity-gate run.
    NO_ISSUER_FOR_CIK = "no_issuer_for_cik"
    #: The CIK maps to more than one issuer -- Atlas does not guess.
    CONTRADICTORY = "contradictory"
    #: No authoritative identifier at all.
    NO_EVIDENCE = "no_evidence"


@dataclass(frozen=True)
class LegacyRecordRepair:
    record_id: str
    outcome: LegacyRepairOutcome
    canonical_issuer_id: str | None = None
    cik: str | None = None

    @property
    def is_repairable(self) -> bool:
        return self.outcome is LegacyRepairOutcome.ISSUER_PROVEN


def build_cik_to_issuer_index(
    linked_records: tuple[tuple[str, str | None, dict], ...],
    issuer_by_security: dict[str, str | None],
) -> dict[str, set[str]]:
    """CIK -> the issuers it is known to belong to, derived **only** from
    records that already carry a `canonical_security_id`.

    That restriction is what makes this safe. The index is built from
    identity Atlas already proved through the gate; unlinked records are
    consumers of the index, never contributors to it. Otherwise a legacy
    record could vouch for its own issuer, and the evidence would be
    circular.

    `linked_records` is `(record_id, canonical_security_id, metadata)`.
    """
    index: dict[str, set[str]] = {}
    for _record_id, security_id, metadata in linked_records:
        if not security_id:
            continue
        issuer_id = issuer_by_security.get(security_id)
        if not issuer_id:
            continue
        cik = normalize_cik(metadata.get("sec_cik"))
        if cik is None:
            continue
        index.setdefault(cik, set()).add(issuer_id)
    return index


def plan_legacy_repair(
    records: tuple[tuple[str, str | None, str, dict], ...],
    cik_to_issuer: dict[str, set[str]],
) -> tuple[LegacyRecordRepair, ...]:
    """Pure and deterministic. `records` is
    `(record_id, canonical_security_id, document_type, metadata)`.

    Reads no ticker and no company name -- the parameters do not even
    carry them, so a future edit cannot quietly start matching on one.
    """
    repairs: list[LegacyRecordRepair] = []
    for record_id, security_id, document_type, metadata in records:
        cik = normalize_cik(metadata.get("sec_cik"))
        if security_id:
            outcome = LegacyRepairOutcome.ALREADY_LINKED
            issuer = None
        elif cik is None:
            outcome = LegacyRepairOutcome.NO_EVIDENCE
            issuer = None
        elif document_type not in ISSUER_LEVEL_DOCUMENT_TYPES:
            outcome = LegacyRepairOutcome.SECURITY_SPECIFIC_EXCLUDED
            issuer = None
        else:
            issuers = cik_to_issuer.get(cik, set())
            if len(issuers) == 1:
                outcome = LegacyRepairOutcome.ISSUER_PROVEN
                issuer = next(iter(issuers))
            elif len(issuers) > 1:
                outcome = LegacyRepairOutcome.CONTRADICTORY
                issuer = None
            else:
                outcome = LegacyRepairOutcome.NO_ISSUER_FOR_CIK
                issuer = None
        repairs.append(
            LegacyRecordRepair(
                record_id=record_id, outcome=outcome, canonical_issuer_id=issuer, cik=cik
            )
        )
    return tuple(repairs)

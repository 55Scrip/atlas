"""Security-level provenance repair for historical BusinessRecords.

The issuer backfill (`legacy_provenance`) gave 144 pre-existing records
a `canonical_issuer_id` from stored CIK evidence, but left
`canonical_security_id` NULL: at the time, no security existed to point
at. Securities exist now, so the question this module answers is
narrow -- for a record that already has a *proven* issuer, can exactly
one security now be proven too?

**The governing case is GOOG.** Alphabet files under one CIK
(0001652044) for two listed share classes. Alphabet's already-linked
records all point at the GOOGL security, purely because the GOOG
security was created later and nothing has been linked to it yet. A
CIK->security index built from those records therefore converges,
confidently and wrongly, on GOOGL. Convergence in that index is not
evidence of uniqueness -- it can equally be an artifact of incomplete
linking, and telling those apart from inside the index is impossible.

So uniqueness is established by an independent signal that can only
ever *refuse*: how many distinct company strings Atlas has ever seen
carrying that CIK. One means the CIK names a single listing as far as
every record Atlas holds is concerned; more than one means the CIK
spans share classes and no filing under it belongs to one security
rather than another.

That count is the only thing this module learns about tickers, and it
arrives pre-computed as an integer. Following `legacy_provenance`, the
planner is never handed a ticker or a company name -- the parameters do
not carry them, so a future edit cannot quietly begin matching on one.
A financial statement is issuer-level in exactly the sense
`ISSUER_LEVEL_DOCUMENT_TYPES` means: leaving one attached to an issuer
and to no security stays a correct, honest state, and is what this
planner returns for every case it cannot prove.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from atlas.alpha.canonical_security.issuer_cik import normalize_cik

__all__ = [
    "SecurityProvenanceOutcome",
    "SecurityRecordRepair",
    "CikSecurityEvidence",
    "plan_security_provenance_repair",
]


class SecurityProvenanceOutcome(str, Enum):
    """Why one record can or cannot receive security provenance."""

    #: Every independent signal agrees on exactly one security, and the
    #: CIK is not shared across share classes. The only repairable case.
    PROVABLE_SECURITY = "provable_security"
    #: The CIK spans more than one listing (share classes), so no filing
    #: under it belongs to one security rather than another.
    MULTIPLE_POSSIBLE_SECURITIES = "multiple_possible_securities"
    #: The issuer is proven but owns no security at all yet.
    NO_SECURITY_EXISTS = "no_security_exists"
    #: No usable CIK, or no already-linked record carries it, so there
    #: is nothing to reason from.
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    #: Signals contradict each other -- never repaired, always reported.
    UNKNOWN = "unknown"
    #: Already has security provenance; nothing to do.
    ALREADY_LINKED = "already_linked"


@dataclass(frozen=True)
class CikSecurityEvidence:
    """Everything the planner may know about one CIK, all of it derived
    from records Atlas already stores.

    `distinct_company_count` is a COUNT, never the strings themselves:
    it can veto a repair but can never select a target.
    """

    #: Securities that already-linked records bearing this CIK point at.
    linked_security_ids: frozenset[str]
    #: How many distinct company strings Atlas has seen for this CIK.
    distinct_company_count: int


@dataclass(frozen=True)
class SecurityRecordRepair:
    record_id: str
    outcome: SecurityProvenanceOutcome
    #: Set only for PROVABLE_SECURITY.
    security_id: str | None = None
    reason: str = ""


def plan_security_provenance_repair(
    records: tuple[tuple[str, str | None, str | None, dict], ...],
    *,
    cik_evidence: dict[str, CikSecurityEvidence],
    securities_by_issuer: dict[str, frozenset[str]],
    security_issuer: dict[str, str],
) -> tuple[SecurityRecordRepair, ...]:
    """Pure and total: every record in, exactly one classification out.

    `records` are `(record_id, canonical_security_id, canonical_issuer_id,
    metadata)`. No ticker, no company name, no document type -- a record
    is repairable on evidence alone or not at all.

    A repair requires all four to hold, and any one of them failing
    leaves the record attached to its issuer and to no security:

      1. the CIK is carried by at least one already-linked record;
      2. those records converge on exactly one security;
      3. that CIK has been seen under exactly one company string, so it
         does not span share classes;
      4. the converged security belongs to this record's own proven
         issuer, and is the only security that issuer owns.
    """
    plans: list[SecurityRecordRepair] = []
    for record_id, security_id, issuer_id, metadata in records:
        if security_id:
            plans.append(SecurityRecordRepair(record_id, SecurityProvenanceOutcome.ALREADY_LINKED))
            continue
        if not issuer_id:
            plans.append(SecurityRecordRepair(
                record_id, SecurityProvenanceOutcome.INSUFFICIENT_EVIDENCE, reason="no proven issuer"))
            continue

        owned = securities_by_issuer.get(issuer_id, frozenset())
        if not owned:
            plans.append(SecurityRecordRepair(
                record_id, SecurityProvenanceOutcome.NO_SECURITY_EXISTS,
                reason="issuer owns no security"))
            continue

        cik = normalize_cik(metadata.get("sec_cik"))
        evidence = cik_evidence.get(cik) if cik else None
        if evidence is None or not evidence.linked_security_ids:
            plans.append(SecurityRecordRepair(
                record_id, SecurityProvenanceOutcome.INSUFFICIENT_EVIDENCE,
                reason="no already-linked record carries this CIK"))
            continue

        # The share-class veto, checked before the index is trusted:
        # convergence in the index cannot distinguish "one listing" from
        # "the other listing has simply not been linked yet".
        if evidence.distinct_company_count != 1:
            plans.append(SecurityRecordRepair(
                record_id, SecurityProvenanceOutcome.MULTIPLE_POSSIBLE_SECURITIES,
                reason=f"CIK spans {evidence.distinct_company_count} listings"))
            continue

        if len(evidence.linked_security_ids) != 1:
            plans.append(SecurityRecordRepair(
                record_id, SecurityProvenanceOutcome.MULTIPLE_POSSIBLE_SECURITIES,
                reason=f"CIK resolves to {len(evidence.linked_security_ids)} securities"))
            continue

        candidate = next(iter(evidence.linked_security_ids))
        if security_issuer.get(candidate) != issuer_id or owned != frozenset({candidate}):
            plans.append(SecurityRecordRepair(
                record_id, SecurityProvenanceOutcome.UNKNOWN,
                reason="CIK-proven security disagrees with the record's proven issuer"))
            continue

        plans.append(SecurityRecordRepair(
            record_id, SecurityProvenanceOutcome.PROVABLE_SECURITY, security_id=candidate,
            reason="CIK unique to one listing, one linked security, issuer agrees"))
    return tuple(plans)

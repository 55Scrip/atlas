"""CIK-backed issuer reconciliation: turning the one proven equivalence
signal into a safe, repeatable operation.

**What a CIK proves, and what it does not.** The SEC assigns a CIK to a
*filer* -- a legal reporting entity -- so two securities reporting under
one CIK belong to one issuer. It says nothing whatever about whether
they are the same security. `GOOG` and `GOOGL` share CIK `0001652044`
and remain two instruments with different share classes and different
voting rights. If this module ever turns "same issuer" into "same
security", it is wrong.

**Evidence is collected through `canonical_security_id`, never through a
ticker string.** That restriction is the point: matching records by
ticker is how a `SU`/`SU.PA` style collision would sneak back in. It has
a real cost -- most stored CIK records predate the identity gate and
carry no security link, so they are invisible here -- and that cost is
accepted deliberately. A security whose own records cannot be identified
is not eligible for linking.

**A security whose records disagree is never linkable.** Two different
CIKs under one security means Atlas does not actually know which filer
it is looking at, and `CONTRADICTORY_CIKS` withholds the security from
reconciliation entirely rather than picking a majority.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

__all__ = [
    "CikEvidenceState",
    "SecurityCikEvidence",
    "IssuerReconciliationPlan",
    "normalize_cik",
    "extract_cik_evidence",
    "plan_issuer_reconciliation",
]


def normalize_cik(value: object) -> str | None:
    """One canonical representation: ten digits, zero padded.

    SEC returns the same filer as `0000320193` from one endpoint and
    `320193` from another, and a provider may hand back an integer.
    Comparing those as raw strings would manufacture a contradiction out
    of formatting, so every comparison in this module goes through here.

    Deterministic and lossless for any real CIK, and `None` -- never a
    guess -- for anything that is not a positive integer of at most ten
    digits. A malformed value is treated as *absent evidence* rather
    than as a distinct identity, so it can never make two securities
    look different from each other."""
    if value is None:
        return None
    text = str(value).strip()
    if not text or not text.isdigit():
        return None
    stripped = text.lstrip("0")
    if not stripped or len(stripped) > 10:
        return None
    return stripped.zfill(10)


class CikEvidenceState(str, Enum):
    """What one security's own records say about its filer identity."""

    #: No record carries a usable CIK. Not linkable -- and not a fault.
    NO_EVIDENCE = "no_evidence"
    #: Every record that carries a CIK carries the same one. The only
    #: state eligible for automatic linking.
    ONE_CONSISTENT_CIK = "one_consistent_cik"
    #: Records disagree. Atlas does not know which filer this is, so the
    #: security is withheld from reconciliation entirely.
    CONTRADICTORY_CIKS = "contradictory_ciks"


@dataclass(frozen=True)
class SecurityCikEvidence:
    canonical_security_id: str
    state: CikEvidenceState
    cik: str | None
    observed: tuple[str, ...]

    @property
    def is_linkable(self) -> bool:
        return self.state is CikEvidenceState.ONE_CONSISTENT_CIK and self.cik is not None


def extract_cik_evidence(
    canonical_security_id: str, record_metadata: tuple[dict, ...]
) -> SecurityCikEvidence:
    """Pure. `record_metadata` is the already-parsed `metadata` of every
    `BusinessRecord` whose `canonical_security_id` is this security --
    the caller does that query, so this module touches no database and
    can be exhaustively tested."""
    observed = sorted(
        {
            normalized
            for metadata in record_metadata
            if (normalized := normalize_cik(metadata.get("sec_cik"))) is not None
        }
    )
    if not observed:
        state, cik = CikEvidenceState.NO_EVIDENCE, None
    elif len(observed) == 1:
        state, cik = CikEvidenceState.ONE_CONSISTENT_CIK, observed[0]
    else:
        state, cik = CikEvidenceState.CONTRADICTORY_CIKS, None
    return SecurityCikEvidence(
        canonical_security_id=canonical_security_id,
        state=state,
        cik=cik,
        observed=tuple(observed),
    )


@dataclass(frozen=True)
class IssuerReconciliationPlan:
    """One CIK's worth of work: the issuer that survives, the issuers
    folded into it, and the securities that move. Computed entirely
    before anything is written, so it can be printed, reviewed and
    re-derived."""

    cik: str
    surviving_issuer_id: str
    merged_issuer_ids: tuple[str, ...]
    security_ids: tuple[str, ...]

    @property
    def is_noop(self) -> bool:
        return not self.merged_issuer_ids


def plan_issuer_reconciliation(
    evidence: tuple[SecurityCikEvidence, ...],
    issuer_id_by_security: dict[str, str | None],
    issuer_created_at: dict[str, datetime],
) -> tuple[IssuerReconciliationPlan, ...]:
    """Pure and deterministic. Groups linkable securities by normalized
    CIK and, for any CIK covering more than one issuer, names the
    survivor.

    **Survivor rule: the oldest issuer by `created_at`, tie-broken by
    lexically smallest id.** Age is preferred because the oldest row has
    had the most opportunity to accumulate identifiers and references,
    so keeping it minimises what has to move. The lexical tie-break
    exists because two issuers created in the same backfill share a
    timestamp -- without it the outcome would depend on database row
    order, which is not a decision, it is an accident.

    A CIK covering exactly one issuer yields a no-op plan rather than
    being dropped, so a caller can report "checked, nothing to do"
    distinctly from "never looked".
    """
    by_cik: dict[str, list[SecurityCikEvidence]] = {}
    for item in evidence:
        if item.is_linkable:
            by_cik.setdefault(item.cik, []).append(item)  # type: ignore[arg-type]

    plans: list[IssuerReconciliationPlan] = []
    for cik in sorted(by_cik):
        securities = sorted(by_cik[cik], key=lambda e: e.canonical_security_id)
        issuers = {
            issuer_id_by_security[e.canonical_security_id]
            for e in securities
            if issuer_id_by_security.get(e.canonical_security_id)
        }
        if not issuers:
            continue
        survivor = min(
            issuers,
            key=lambda issuer_id: (
                issuer_created_at.get(issuer_id, datetime.max),
                issuer_id,
            ),
        )
        plans.append(
            IssuerReconciliationPlan(
                cik=cik,
                surviving_issuer_id=survivor,
                merged_issuer_ids=tuple(sorted(issuers - {survivor})),
                security_ids=tuple(e.canonical_security_id for e in securities),
            )
        )
    return tuple(plans)

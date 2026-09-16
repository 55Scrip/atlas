"""Valuation Evidence Snapshot -- what Atlas knew and used, frozen.

A stored `AnalyticalSnapshot` records what Atlas *concluded* at a moment:
the valuation status, the risk states, the thesis. It has never recorded
what that conclusion was *made from*. Two audits were limited by exactly
that: the prior fiscal epochs behind a classification, the Valuation
Support beside it, and the descriptive evidence about both existed only in
the live composition and were gone by the time anyone asked.

This module freezes them, at the moment the snapshot is taken, from the
same composition that produced the decision.

**It is a recording, not a second engine.** Every value here is copied from
a result the production pipeline already produced -- the accepted prior
epochs are `FcfYieldEvidence.prior_epochs` verbatim, the metadata is the
`ValuationEvidenceMetadata` the Case itself carries. Nothing is recomputed,
re-classified or re-derived, here or on the way back out.

**A frozen snapshot is historically true, permanently.** A later filing, a
price refresh, better class-rights evidence or a new methodology never
edits one: they produce a *new* snapshot, and the old one keeps saying what
Atlas actually had. Reading one never consults the current database.

**It decides nothing.** No valuation, recommendation, risk, fit, stance or
Decision Layer result reads a stored snapshot; this is history and
evaluation only, and the import firewall in the tests enforces it.

`SCHEMA_VERSION` versions *this persistence contract* and is deliberately
separate from `VALUATION_METHODOLOGY`, which identifies how the valuation
itself was computed. A future `fiscal_epoch_v4` changes the latter; adding
a field here changes the former.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from atlas.alpha.investment_case.valuation_evidence_metadata import ValuationEvidenceMetadata
from atlas.analysis_engine.valuation.models import FcfYieldEpochObservation, ValuationFinding
from atlas.analysis_engine.valuation.support import ValuationSupport

__all__ = [
    "SCHEMA_VERSION",
    "FrozenEpoch",
    "ValuationEvidenceSnapshot",
    "freeze_valuation_evidence",
    "serialize_valuation_evidence",
    "deserialize_valuation_evidence",
]

#: Versions the persistence contract below -- never the valuation method.
SCHEMA_VERSION = "valuation_evidence_snapshot_v1"


@dataclass(frozen=True)
class FrozenEpoch:
    """One fiscal valuation epoch exactly as the valuation used it.

    `fcf_yield` is stored rather than left to be recomputed on read: it is
    the number the classification actually compared, and a stored figure
    cannot drift from the arithmetic of a future release.
    """

    fiscal_period: str
    free_cash_flow: float
    raw_free_cash_flow: float | None
    senior_claim_low: float
    senior_claim_high: float
    market_cap_low: float | None
    market_cap_high: float | None
    share_price: float
    shares_outstanding: float
    currency: str
    fcf_yield: float
    denominator_quality: str | None
    observed_on: str
    available_from: str

    @classmethod
    def of(cls, epoch: FcfYieldEpochObservation) -> "FrozenEpoch":
        return cls(
            fiscal_period=epoch.fiscal_period,
            free_cash_flow=epoch.free_cash_flow,
            raw_free_cash_flow=epoch.raw_free_cash_flow,
            senior_claim_low=epoch.senior_claim_low,
            senior_claim_high=epoch.senior_claim_high,
            market_cap_low=epoch.market_cap_low,
            market_cap_high=epoch.market_cap_high,
            share_price=epoch.share_price,
            shares_outstanding=epoch.shares_outstanding,
            currency=epoch.currency,
            fcf_yield=epoch.fcf_yield,
            denominator_quality=epoch.denominator_quality,
            observed_on=epoch.observed_on,
            available_from=epoch.available_from.isoformat(),
        )


@dataclass(frozen=True)
class ValuationEvidenceSnapshot:
    """The valuation evidence behind one stored snapshot.

    `prior_epochs` are the accepted priors and only those -- whatever the
    method excluded is not here, so the record can never describe a
    valuation Atlas did not make. They keep the engine's own chronological
    order.

    `fingerprint` identifies this evidence for persistence purposes. It
    deliberately excludes `current_yield` and the current epoch, mirroring
    the existing decision that `AnalyticalSnapshot.content_hash` excludes
    `current_yield`: a price tick is not new evidence, and must not create
    a snapshot. A restated prior, a newly available fiscal year, a changed
    denominator treatment or a changed Valuation Support is.
    """

    schema_version: str
    valuation_methodology: str | None
    numerator_method: str | None
    nci_treatment: str | None
    share_count_method: str
    eligibility: str
    minimum_prior_epochs: int
    withheld_reasons: tuple[str, ...]
    valuation_position: str | None
    valuation_status: str
    current_yield: float | None
    current_epoch: FrozenEpoch | None
    prior_epochs: tuple[FrozenEpoch, ...]
    valuation_support_status: str
    valuation_support_gap: str | None
    metadata: ValuationEvidenceMetadata | None
    fingerprint: str


def _epoch_payload(epoch: FrozenEpoch) -> dict[str, Any]:
    return {
        "fiscal_period": epoch.fiscal_period,
        "free_cash_flow": epoch.free_cash_flow,
        "raw_free_cash_flow": epoch.raw_free_cash_flow,
        "senior_claim_low": epoch.senior_claim_low,
        "senior_claim_high": epoch.senior_claim_high,
        "market_cap_low": epoch.market_cap_low,
        "market_cap_high": epoch.market_cap_high,
        "share_price": epoch.share_price,
        "shares_outstanding": epoch.shares_outstanding,
        "currency": epoch.currency,
        "fcf_yield": epoch.fcf_yield,
        "denominator_quality": epoch.denominator_quality,
        "observed_on": epoch.observed_on,
        "available_from": epoch.available_from,
    }


def _epoch_from_payload(payload: Mapping[str, Any]) -> FrozenEpoch:
    return FrozenEpoch(**{field: payload[field] for field in (
        "fiscal_period", "free_cash_flow", "raw_free_cash_flow", "senior_claim_low", "senior_claim_high",
        "market_cap_low", "market_cap_high", "share_price", "shares_outstanding", "currency",
        "fcf_yield", "denominator_quality", "observed_on", "available_from")})


def _fingerprint(prior_epochs: tuple[FrozenEpoch, ...], *, valuation_methodology: str,
                 numerator_method: str | None, share_count_method: str, eligibility: str,
                 support_status: str, minimum_prior_epochs: int) -> str:
    """Identity of the evidence, excluding anything that moves with price.

    What is in it: the accepted priors, the method that built them, the
    eligibility rule they were judged under, and the Valuation Support
    beside them. What is out: the current yield and the current epoch.
    """
    material = {
        "prior_epochs": [_epoch_payload(epoch) for epoch in prior_epochs],
        "valuation_methodology": valuation_methodology,
        "numerator_method": numerator_method,
        "share_count_method": share_count_method,
        "eligibility": eligibility,
        "minimum_prior_epochs": minimum_prior_epochs,
        "valuation_support_status": support_status,
        "schema_version": SCHEMA_VERSION,
    }
    return hashlib.sha256(json.dumps(material, sort_keys=True).encode("utf-8")).hexdigest()


def freeze_valuation_evidence(
    finding: ValuationFinding,
    valuation_support: ValuationSupport,
    metadata: ValuationEvidenceMetadata | None,
    *,
    valuation_methodology: str | None,
) -> ValuationEvidenceSnapshot | None:
    """Copy the valuation evidence of one composition into an immutable
    record. `None` when the finding formed no evidence at all -- an honest
    absence, never an empty evidence set standing in for one."""
    evidence = finding.fcf_yield_evidence
    if evidence is None:
        return None
    priors = tuple(FrozenEpoch.of(epoch) for epoch in evidence.prior_epochs)
    support_status = valuation_support.status.value
    return ValuationEvidenceSnapshot(
        schema_version=SCHEMA_VERSION,
        valuation_methodology=valuation_methodology,
        numerator_method=evidence.numerator_method,
        nci_treatment=evidence.nci_treatment,
        share_count_method=evidence.share_count_method.value,
        eligibility=evidence.eligibility.value,
        minimum_prior_epochs=evidence.minimum_prior_epochs,
        withheld_reasons=tuple(reason.value for reason in evidence.withheld_reasons),
        valuation_position=evidence.position.value if evidence.position is not None else None,
        valuation_status=finding.status.value,
        current_yield=finding.current_yield,
        current_epoch=FrozenEpoch.of(evidence.current) if evidence.current is not None else None,
        prior_epochs=priors,
        valuation_support_status=support_status,
        valuation_support_gap=valuation_support.gap.value if valuation_support.gap is not None else None,
        metadata=metadata,
        fingerprint=_fingerprint(
            priors, valuation_methodology=valuation_methodology,
            numerator_method=evidence.numerator_method,
            share_count_method=evidence.share_count_method.value,
            eligibility=evidence.eligibility.value, support_status=support_status,
            minimum_prior_epochs=evidence.minimum_prior_epochs),
    )


# -- serialization -----------------------------------------------------------
#
# Explicit field by field, never a blanket dump of whatever an object
# happens to hold: a persisted historical record should gain a field only
# when someone decided it should.


def _metadata_payload(metadata: ValuationEvidenceMetadata | None) -> dict[str, Any] | None:
    if metadata is None:
        return None
    from dataclasses import asdict

    def plain(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: plain(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [plain(v) for v in value]
        return value.value if hasattr(value, "value") and not isinstance(value, (str, int, float)) else value

    return plain(asdict(metadata))


def serialize_valuation_evidence(snapshot: ValuationEvidenceSnapshot) -> dict[str, Any]:
    return {
        "schema_version": snapshot.schema_version,
        "valuation_methodology": snapshot.valuation_methodology,
        "numerator_method": snapshot.numerator_method,
        "nci_treatment": snapshot.nci_treatment,
        "share_count_method": snapshot.share_count_method,
        "eligibility": snapshot.eligibility,
        "minimum_prior_epochs": snapshot.minimum_prior_epochs,
        "withheld_reasons": list(snapshot.withheld_reasons),
        "valuation_position": snapshot.valuation_position,
        "valuation_status": snapshot.valuation_status,
        "current_yield": snapshot.current_yield,
        "current_epoch": None if snapshot.current_epoch is None else _epoch_payload(snapshot.current_epoch),
        "prior_epochs": [_epoch_payload(epoch) for epoch in snapshot.prior_epochs],
        "valuation_support_status": snapshot.valuation_support_status,
        "valuation_support_gap": snapshot.valuation_support_gap,
        "metadata": _metadata_payload(snapshot.metadata),
        "fingerprint": snapshot.fingerprint,
    }


def deserialize_valuation_evidence(payload: Mapping[str, Any] | None) -> ValuationEvidenceSnapshot | None:
    """`None` for a snapshot persisted before this contract existed -- a
    legacy row genuinely has no evidence, which is not the same fact as a
    recorded evidence set that happens to be empty."""
    if payload is None:
        return None
    return ValuationEvidenceSnapshot(
        schema_version=payload["schema_version"],
        valuation_methodology=payload["valuation_methodology"],
        numerator_method=payload["numerator_method"],
        nci_treatment=payload["nci_treatment"],
        share_count_method=payload["share_count_method"],
        eligibility=payload["eligibility"],
        minimum_prior_epochs=payload["minimum_prior_epochs"],
        withheld_reasons=tuple(payload["withheld_reasons"]),
        valuation_position=payload["valuation_position"],
        valuation_status=payload["valuation_status"],
        current_yield=payload["current_yield"],
        current_epoch=(None if payload["current_epoch"] is None
                       else _epoch_from_payload(payload["current_epoch"])),
        prior_epochs=tuple(_epoch_from_payload(epoch) for epoch in payload["prior_epochs"]),
        valuation_support_status=payload["valuation_support_status"],
        valuation_support_gap=payload["valuation_support_gap"],
        #: Kept as the recorded mapping: rebuilding the live dataclass would
        #: silently re-impose today's shape on a historical record.
        metadata=payload["metadata"],
        fingerprint=payload["fingerprint"],
    )

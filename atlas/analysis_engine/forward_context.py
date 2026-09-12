"""Forward context for recommendation reasoning -- the one seam between
Atlas's forward evidence and its recommendation.

`atlas.analysis_engine.forward_claims` is otherwise inert: nothing in the
analysis or decision path may import it (`test_integration_safety`). This
module is the single, deliberate exception. It reads the company's
already-persisted transcript records, runs the established forward-evidence
pipeline -- guidance claims, revisions and interpretations; customer
commitments and their contracted-volume interpretation; the company forward
picture -- and restates the result as a `ForwardReasoningContext`.

**Context, never input.** The result is handed to
`evaluate_recommendation_gate`, which places it into the reasoning after
the direction is chosen. Nothing that selects a direction, drivers,
change triggers, key unknowns or conviction can read it, and only
`atlas.analysis_engine.pipeline` imports this module -- both pinned by
tests.

**Restatement only.** Every item comes from an interpretation the
forward-evidence layer already produced: the latest verified revision of
each guided measure and horizon, and every contracted-volume observation
as it stands -- not merged, not deduplicated, not summed, carrying the
economics it does not establish. No transcript is parsed here beyond
calling that pipeline, no provider is called, and no clock is read: the
extraction time is the caller's own evaluation time.
"""
from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.analysis_engine.forward_claims import (
    ClaimBound,
    ContractedVolumeInterpretation,
    GuidanceEconomicInterpretation,
    StateDimension,
    detect_revisions,
    extract_customer_commitments,
    extract_forward_claims,
    interpret_customer_commitments,
    interpret_revisions,
    period_ordinal,
    synthesize_company_forward_picture,
)
from atlas.analysis_engine.reasoning import (
    ContractedVolumeContext,
    ForwardGuidanceContext,
    ForwardGuidanceSubject,
    ForwardReasoningContext,
    GuidanceRevisionKind,
    UnestablishedEconomics,
)

__all__ = ["build_forward_reasoning_context"]

#: Canonical subjects broader than the source's own measure -- VST's
#: "adjusted free cash flow before growth" is guidance for *a*
#: free-cash-flow measure, never Atlas's own FCF figure.
_MANAGEMENT_DEFINED = frozenset({ForwardGuidanceSubject.ADJUSTED_EBITDA, ForwardGuidanceSubject.FREE_CASH_FLOW})
_BOUND_WORDS = {ClaimBound.UPPER_BOUND: "up to ", ClaimBound.LOWER_BOUND: "at least "}


def _guidance_items(picture, interpretations: dict[str, GuidanceEconomicInterpretation]):
    items = []
    for synthesis in picture.annual:
        for summary in synthesis.dimensions:
            if not summary.history:
                continue
            placed = [e for e in summary.history if period_ordinal(e.source_period) is not None]
            latest_ordinal = period_ordinal(placed[-1].source_period) if placed else None
            latest = [e for e in summary.history if period_ordinal(e.source_period) == latest_ordinal]
            for entry in latest:
                interpretation = interpretations[entry.signal_id]
                subject = ForwardGuidanceSubject(interpretation.subject.value)
                items.append(ForwardGuidanceContext(
                    signal_id=entry.signal_id,
                    subject=subject,
                    measure_defined_by_management=subject in _MANAGEMENT_DEFINED,
                    horizon_period=interpretation.horizon_period,
                    horizon_kind=interpretation.horizon_kind.value,
                    revision=GuidanceRevisionKind(interpretation.revision_type.value),
                    value_text=interpretation.new_value_text,
                    prior_value_text=interpretation.prior_value_text,
                    source_period=interpretation.new_source_period,
                    revision_count=len(summary.history),
                ))
    return tuple(items)


def _volume_items(picture, volumes: dict[str, ContractedVolumeInterpretation]):
    items = []
    for observation in picture.state(StateDimension.CONTRACTED_VOLUME).observations:
        volume = volumes[observation.signal_id]
        items.append(ContractedVolumeContext(
            signal_id=observation.signal_id,
            source_period=volume.source_period,
            counterparty_text=volume.claim.counterparty_text,
            agreement_text=volume.claim.agreement_text,
            quantity_texts=tuple(
                f"{_BOUND_WORDS.get(q.bound, '')}{q.value_text}{' ' + q.measure_text if q.measure_text else ''}"
                for q in volume.quantities
            ),
            term_years=volume.span.term_years,
            delivery_start_years=volume.span.start_years,
            delivery_end_years=volume.span.end_years,
            not_established=tuple(a for a in UnestablishedEconomics if a.value in {n.value for n in volume.not_established}),
        ))
    return tuple(items)


def build_forward_reasoning_context(
    business_records: Iterable[BusinessRecord], *, extracted_at: datetime
) -> ForwardReasoningContext | None:
    """Pure and deterministic over one company's latest-version records.
    `None` when the records hold no verified, interpretable forward
    evidence -- never an empty context, and never a reassurance."""
    transcripts = tuple(r for r in business_records if r.document_type is SourceKind.TRANSCRIPT)
    if not transcripts:
        return None
    claims = tuple(c for r in transcripts for c in extract_forward_claims(r, extracted_at=extracted_at)[0])
    revisions, _ = detect_revisions(claims)
    guidance = interpret_revisions(revisions, claims)
    commitments, _ = extract_customer_commitments(transcripts)
    volumes, _ = interpret_customer_commitments(commitments)
    pictures = synthesize_company_forward_picture(guidance + volumes)
    if not pictures:
        return None
    if len(pictures) > 1:
        raise ValueError("forward context is built for one company's records at a time")
    (picture,) = pictures
    guidance_items = _guidance_items(picture, {g.signal_id: g for g in guidance})
    volume_items = _volume_items(picture, {v.signal_id: v for v in volumes})
    if not guidance_items and not volume_items:
        return None
    return ForwardReasoningContext(guidance=guidance_items, contracted_volume=volume_items)

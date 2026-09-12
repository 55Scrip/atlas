"""What an executed customer commitment establishes economically --
contracted volume, and nothing more (Forward-Looking Evidence, Stage 5.4).

A `CustomerCommitmentClaim` is a fact about state: Meta has committed, in
20-year agreements, to 2,176 megawatts of operating capacity. It means
something the first time Atlas sees it, so it is interpreted without any
prior figure and never as a revision -- there is no "raised", no
"reaffirmed", no movement and no effect.

**Contracted is not profitable.** What the source establishes is a
customer, a committed quantity of the company's output, and how long or
from when it runs. What it does not establish is the price, and so
nothing that depends on price: revenue, earnings, cash flow, margin,
return. VST itself excludes the Meta agreements' "premium above market"
from its guidance, and no real commitment states a price. So the one
meaning given here is `StateDimension.CONTRACTED_VOLUME`, and every
interpretation carries, explicitly, that price and the revenue, earnings
and cash-flow contributions are *not established* -- absence travels
with the fact instead of being left for a reader to fill in.

**Not "visibility", not "demand".** Long duration is not earnings
visibility, and one customer's commitment is not market demand. The
narrower name is the accurate one.

**Eligible only when volume is actually established.** An
interpretation needs at least one stated quantity, a stated term or
delivery start/end, and for every quantity something saying what it
counts -- the claim's kind or the quantity's own measure ("of Instinct
GPUs"). A five-year agreement with no quantity (Micron's SCA) is a real
commitment but establishes no volume, so it is withheld, not stretched.

**Nothing is merged or deduplicated.** AWS in 2025Q3 and AWS in 2025Q4
are two observations: nothing here says they are the same agreement.

Inert: nothing in Atlas's analysis or decision path imports it.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

from atlas.analysis_engine.forward_claims.commitments import CommittedQuantity, CustomerCommitmentClaim
from atlas.analysis_engine.forward_claims.contracts import ClaimBound, HorizonKind
from atlas.analysis_engine.forward_claims.interpretation import ForwardEvidenceKind
from atlas.analysis_engine.forward_claims.synthesis import (
    ALL_ECONOMIC_ASPECTS,
    EconomicAspect,
    EvidenceSpan,
    StateDimension,
)

__all__ = [
    "VOLUME_INTERPRETATION_VERSION",
    "ContractedVolumeInterpretation",
    "VolumeWithholdReason",
    "WithheldVolume",
    "interpret_customer_commitment",
    "interpret_customer_commitments",
]

VOLUME_INTERPRETATION_VERSION = "contracted-volume-v1"


class VolumeWithholdReason(str, Enum):
    NO_ESTABLISHED_VOLUME = "no_established_volume"
    """The commitment states no quantity."""
    NO_TERM_OR_DELIVERY = "no_term_or_delivery"
    """A quantity, but no term and no delivery start or end."""
    MEASURE_NOT_STATED = "measure_not_stated"
    """A quantity whose meaning nothing states: no kind, no measure."""
    TERMS_DISAGREE = "terms_disagree"
    """The claim and its supports state different terms."""
    MIXED_YEAR_KINDS = "mixed_year_kinds"
    """Delivery years qualified differently (fiscal and calendar)."""


@dataclass(frozen=True)
class WithheldVolume:
    claim_id: str
    reason: VolumeWithholdReason


def _stated_quantities(claim: CustomerCommitmentClaim) -> tuple[CommittedQuantity, ...]:
    return claim.quantities + tuple(q for s in claim.supports for q in s.quantities)


def _stated_windows(claim: CustomerCommitmentClaim):
    return ((claim.window,) if claim.window else ()) + tuple(s.window for s in claim.supports if s.window)


def _stated_terms(claim: CustomerCommitmentClaim):
    return ((claim.term,) if claim.term else ()) + tuple(s.term for s in claim.supports if s.term)


_BOUND_WORD = {ClaimBound.UPPER_BOUND: "up to ", ClaimBound.LOWER_BOUND: "at least "}


def _explanation(claim: CustomerCommitmentClaim, quantities: tuple[CommittedQuantity, ...], span: EvidenceSpan) -> str:
    """What is established, then what is not -- facts only, in the
    source's own figures."""
    customer = claim.counterparty_text or "an unnamed customer"
    volumes = " and ".join(
        f"{_BOUND_WORD.get(q.bound, '')}{q.value_text}{' ' + q.measure_text if q.measure_text else ''}" for q in quantities
    )
    parts = [f"{claim.company}: {customer} is committed, under executed \"{claim.agreement_text}\", to {volumes}"]
    if span.term_years is not None:
        parts.append(f"term {span.term_years:g} years")
    if span.start_years:
        parts.append("stated delivery starts " + ", ".join(str(y) for y in span.start_years))
    if span.end_years:
        parts.append("stated delivery ends " + ", ".join(str(y) for y in span.end_years))
    return "; ".join(parts) + ". Price, revenue, earnings and cash-flow contribution are not established."


@dataclass(frozen=True)
class ContractedVolumeInterpretation:
    """The contracted volume one executed customer commitment establishes.
    Holds the claim itself, so every quantity and year leads back through
    its supports and links to a transcript sentence."""

    claim: CustomerCommitmentClaim
    quantities: tuple[CommittedQuantity, ...]
    """Every stated quantity -- the anchor's own, then its supports' -- as
    stated: never converted, summed or ranked."""
    span: EvidenceSpan
    not_established: frozenset[EconomicAspect]
    """Always every aspect: a customer commitment claim cannot carry a
    price, so it establishes no price-dependent economics."""
    explanation: str
    interpretation_version: str

    def __post_init__(self) -> None:
        if not self.quantities or self.quantities != _stated_quantities(self.claim):
            raise ValueError("quantities are exactly the claim's stated quantities")
        if self.not_established != ALL_ECONOMIC_ASPECTS:
            raise ValueError("a customer commitment establishes no price, revenue, earnings or cash-flow contribution")

    # -- `synthesis.ForwardStateSignal` ----------------------------------------

    @property
    def signal_id(self) -> str:
        return f"{self.claim.id}:contracted_volume"

    @property
    def evidence_kind(self) -> ForwardEvidenceKind:
        return ForwardEvidenceKind.CUSTOMER_COMMITMENT

    @property
    def company(self) -> str:
        return self.claim.company

    @property
    def state_dimension(self) -> StateDimension:
        return StateDimension.CONTRACTED_VOLUME

    @property
    def source_period(self) -> str | None:
        return self.claim.source_period


def interpret_customer_commitment(
    claim: CustomerCommitmentClaim,
) -> ContractedVolumeInterpretation | WithheldVolume:
    """Pure and deterministic; reads only the claim."""
    quantities = _stated_quantities(claim)
    if not quantities:
        return WithheldVolume(claim.id, VolumeWithholdReason.NO_ESTABLISHED_VOLUME)
    if claim.commitment_kind is None and any(q.measure_text is None for q in quantities):
        return WithheldVolume(claim.id, VolumeWithholdReason.MEASURE_NOT_STATED)
    terms = {t.years for t in _stated_terms(claim)}
    if len(terms) > 1:
        return WithheldVolume(claim.id, VolumeWithholdReason.TERMS_DISAGREE)
    windows = _stated_windows(claim)
    if len({w.horizon_kind for w in windows}) > 1:
        return WithheldVolume(claim.id, VolumeWithholdReason.MIXED_YEAR_KINDS)
    if not terms and not windows:
        return WithheldVolume(claim.id, VolumeWithholdReason.NO_TERM_OR_DELIVERY)
    span = EvidenceSpan(
        term_years=terms.pop() if terms else None,
        start_years=tuple(sorted({w.start_year for w in windows if w.start_year is not None})),
        end_years=tuple(sorted({w.end_year for w in windows if w.end_year is not None})),
        year_kind=windows[0].horizon_kind if windows else HorizonKind.UNSPECIFIED_YEAR,
    )
    return ContractedVolumeInterpretation(
        claim=claim,
        quantities=quantities,
        span=span,
        not_established=ALL_ECONOMIC_ASPECTS,
        explanation=_explanation(claim, quantities, span),
        interpretation_version=VOLUME_INTERPRETATION_VERSION,
    )


def interpret_customer_commitments(
    claims: Iterable[CustomerCommitmentClaim],
) -> tuple[tuple[ContractedVolumeInterpretation, ...], tuple[WithheldVolume, ...]]:
    """Every claim either interpreted or withheld with a reason, in the
    claims' own order."""
    interpreted, withheld = [], []
    for claim in claims:
        result = interpret_customer_commitment(claim)
        (interpreted if isinstance(result, ContractedVolumeInterpretation) else withheld).append(result)
    return tuple(interpreted), tuple(withheld)

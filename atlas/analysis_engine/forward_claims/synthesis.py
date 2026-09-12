"""The combined forward economic picture for one company and horizon
(Forward-Looking Evidence, Stage 4.2).

Stage 4.1 says what one revision means for one dimension of the
business. An investor reasons across several at once, so this module
lays the interpreted signals for a company and horizon side by side:
for each economic dimension, whether the forward evidence shows it
strengthening, weakening, unchanged or ambiguous -- or shows nothing at
all.

**Synthesis is not sentiment.** There is no net, score, polarity or
verdict, and no field that could hold one. Revenue strengthening while
cash generation weakens is a mixed economic picture, and it stays two
dimensions; it is not a contradiction and not "on balance" anything. A
*conflict* is narrower: two signals about the same dimension that
disagree and cannot be put in order.

**Missing is not unchanged.** A dimension no signal speaks to is
`UNSUPPORTED`. `UNCHANGED` means a signal exists and says the stated
figures did not move. Two reaffirmations therefore say that earnings
and cash guidance held -- not that the business, the thesis or the
investment case is stable, and not that uncertainty fell.

**No visibility or uncertainty dimension.** Nothing Atlas extracts
today measures either: a reaffirmed range is not evidence of better
visibility, and range width is not interpreted. Contracted volume
(below) is not visibility either: it says a customer committed to a
quantity, not that revenue or earnings are more predictable.

**Latest signal, full history.** Within a dimension, signals are placed
in fiscal-period order; the most recent one gives the current state,
and every earlier one stays in the history, so a raise followed by a
cut reads as both, in order. Only fiscal `source_period` is used --
never a date, so nothing here is "recent".

**Not only for guidance.** The annual synthesis reads anything that
satisfies `ForwardEconomicSignal` -- a company, a horizon, a dimension, a
movement, an effect, a period and a provenance id. Another kind that
revises a single-year figure fits without changing this module.

**State evidence is its own shape** (Stage 5.4). An executed customer
commitment means something the first time it is seen; it has no prior
figure, so no movement and no effect, and it reaches over years rather
than into one. It enters through `ForwardStateSignal` -- a state
dimension, an `EvidenceSpan` and the economics it does *not* establish --
and never through `ForwardEconomicSignal`: a signal that satisfied both
would be both a comparison and a first observation, and is refused.
`synthesize_company_forward_picture` keeps the two side by side for a
company: the annual syntheses exactly as before, and next to them every
state observation, in fiscal order, with no "current" state, no
conflict and no netting -- two commitments with different quantities
are two observations, not a disagreement, because nothing says they
are the same agreement. Neither path looks at what class produced a
signal.

**Separate from historical analysis, and inert.** It reads no business
fact, valuation, risk or Outlook, and nothing in Atlas's analysis or
decision path imports it.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from atlas.analysis_engine.forward_claims.contracts import HorizonKind
from atlas.analysis_engine.forward_claims.interpretation import (
    EconomicDimension,
    ExpectedMovement,
    ForwardEvidenceKind,
    OutlookEffect,
)
from atlas.analysis_engine.forward_claims.source_time import period_ordinal

__all__ = [
    "SYNTHESIS_VERSION",
    "PICTURE_VERSION",
    "ForwardEconomicSignal",
    "ForwardStateSignal",
    "StateDimension",
    "EconomicAspect",
    "ALL_ECONOMIC_ASPECTS",
    "EvidenceSpan",
    "StateObservation",
    "StateDimensionSummary",
    "CompanyForwardPicture",
    "synthesize_company_forward_picture",
    "describe_company_forward_picture",
    "DimensionState",
    "SignalEntry",
    "DimensionSummary",
    "ForwardEconomicSynthesis",
    "synthesize_forward_signals",
    "describe_synthesis",
]

SYNTHESIS_VERSION = "forward-synthesis-v1"
PICTURE_VERSION = "forward-picture-v1"


@runtime_checkable
class ForwardEconomicSignal(Protocol):
    """One economically interpreted piece of forward evidence -- the
    only shape the synthesis reads. `GuidanceEconomicInterpretation`
    satisfies it today."""

    @property
    def signal_id(self) -> str: ...
    @property
    def evidence_kind(self) -> ForwardEvidenceKind: ...
    @property
    def company(self) -> str: ...
    @property
    def horizon_period(self) -> str: ...
    @property
    def horizon_kind(self) -> HorizonKind: ...
    @property
    def dimension(self) -> EconomicDimension: ...
    @property
    def movement(self) -> ExpectedMovement: ...
    @property
    def outlook_effect(self) -> OutlookEffect: ...
    @property
    def source_period(self) -> str | None: ...


class StateDimension(str, Enum):
    """What a piece of state evidence establishes. Kept apart from
    `EconomicDimension`: those are flows a revision moves (revenue,
    earnings, cash, spending); these are facts that simply hold."""

    CONTRACTED_VOLUME = "contracted_volume"
    """A customer has committed, in a concluded agreement, to take a
    stated quantity of the company's output over a stated term or from a
    stated delivery start. Committed volume -- not revenue (no price),
    not demand (one customer's commitment, not a market), not visibility
    of earnings."""


class EconomicAspect(str, Enum):
    """Economics a piece of state evidence may or may not establish. Its
    absence is carried explicitly, so no consumer can read contracted
    volume as money."""

    PRICE = "price"
    REVENUE_CONTRIBUTION = "revenue_contribution"
    EARNINGS_CONTRIBUTION = "earnings_contribution"
    CASH_FLOW_CONTRIBUTION = "cash_flow_contribution"


ALL_ECONOMIC_ASPECTS = frozenset(EconomicAspect)


@dataclass(frozen=True)
class EvidenceSpan:
    """How far forward a piece of state evidence reaches, as the source
    states it -- never an annual horizon. A 20-year agreement whose
    deliveries start in 2026 is not 2026 evidence."""

    term_years: float | None
    start_years: tuple[int, ...]
    """Stated delivery starts, ascending (Perry 2026, Davis-Besse 2027)."""
    end_years: tuple[int, ...]
    year_kind: HorizonKind
    """How the stated years are qualified; all of them share one kind."""

    def __post_init__(self) -> None:
        if self.term_years is None and not self.start_years and not self.end_years:
            raise ValueError("a span states a term or at least one year")
        if self.term_years is not None and self.term_years <= 0:
            raise ValueError("a term is a positive number of years")
        for years in (self.start_years, self.end_years):
            if tuple(sorted(set(years))) != years:
                raise ValueError("span years are distinct and ascending")


@runtime_checkable
class ForwardStateSignal(Protocol):
    """One interpreted piece of forward *state* evidence -- no movement,
    no effect, no single-year horizon. `ContractedVolumeInterpretation`
    satisfies it today."""

    @property
    def signal_id(self) -> str: ...
    @property
    def evidence_kind(self) -> ForwardEvidenceKind: ...
    @property
    def company(self) -> str: ...
    @property
    def state_dimension(self) -> StateDimension: ...
    @property
    def span(self) -> EvidenceSpan: ...
    @property
    def not_established(self) -> frozenset[EconomicAspect]: ...
    @property
    def source_period(self) -> str | None: ...
    @property
    def explanation(self) -> str: ...


def _is_revision(signal: object) -> bool:
    return isinstance(signal, ForwardEconomicSignal) and not isinstance(signal, ForwardStateSignal)


def _is_state(signal: object) -> bool:
    return isinstance(signal, ForwardStateSignal) and not isinstance(signal, ForwardEconomicSignal)


class DimensionState(str, Enum):
    """Where the forward evidence leaves one dimension. The first four
    are the latest signal's own effect; the last two are what the
    evidence cannot say."""

    STRENGTHENING = "strengthening"
    WEAKENING = "weakening"
    UNCHANGED = "unchanged"
    AMBIGUOUS = "ambiguous"
    CONFLICTING = "conflicting"
    """The most recent signals disagree and nothing orders them -- same
    fiscal period, or no period at all. Neither is chosen."""
    UNSUPPORTED = "unsupported"
    """No forward signal speaks to this dimension. Not unchanged."""


@dataclass(frozen=True)
class SignalEntry:
    """One signal as it enters a dimension's history -- the provenance id
    leads back to the interpretation, its revision, its claims and their
    transcript passages."""

    signal_id: str
    evidence_kind: ForwardEvidenceKind
    source_period: str | None
    movement: ExpectedMovement
    outlook_effect: OutlookEffect


@dataclass(frozen=True)
class DimensionSummary:
    dimension: EconomicDimension
    state: DimensionState
    history: tuple[SignalEntry, ...]
    """Every signal for this dimension, in fiscal-period order; signals
    with no period come last, in id order."""
    unordered_signal_ids: tuple[str, ...]
    """Signals with no fiscal period, which therefore cannot be placed."""
    history_has_opposite_effects: bool
    """Both strengthening and weakening occur in the history -- guidance
    moved one way and later the other. Recorded, never netted."""


@dataclass(frozen=True)
class ForwardEconomicSynthesis:
    """The forward economic picture for one company and one horizon --
    one summary per dimension, supported or not, and nothing combining
    them."""

    company: str
    horizon_period: str
    horizon_kind: HorizonKind
    dimensions: tuple[DimensionSummary, ...]
    """Every `EconomicDimension`, in its declaration order."""
    evidence_kinds: tuple[ForwardEvidenceKind, ...]
    """Which kinds of forward evidence this picture rests on -- today
    never more than guidance revisions, which is itself part of the
    picture: nothing here speaks to contracts, capacity or hedging."""
    synthesis_version: str

    def summary(self, dimension: EconomicDimension) -> DimensionSummary:
        return next(d for d in self.dimensions if d.dimension is dimension)


def _order_key(entry: SignalEntry) -> tuple[bool, tuple[int, int], str]:
    ordinal = period_ordinal(entry.source_period)
    return (ordinal is None, ordinal or (0, 0), entry.signal_id)


def _summarize(dimension: EconomicDimension, entries: list[SignalEntry]) -> DimensionSummary:
    if not entries:
        return DimensionSummary(dimension, DimensionState.UNSUPPORTED, (), (), False)
    entries.sort(key=_order_key)
    ordered = [e for e in entries if period_ordinal(e.source_period) is not None]
    unordered = [e for e in entries if period_ordinal(e.source_period) is None]
    if ordered:
        latest_ordinal = period_ordinal(ordered[-1].source_period)
        latest = [e for e in ordered if period_ordinal(e.source_period) == latest_ordinal]
    else:
        latest = []
    # An unplaceable signal could be the latest one; if it disagrees with
    # the latest placed signals, the current state is not established.
    candidates = {e.outlook_effect for e in latest + unordered}
    state = DimensionState.CONFLICTING if len(candidates) > 1 else DimensionState(candidates.pop().value)
    effects = {e.outlook_effect for e in entries}
    return DimensionSummary(
        dimension=dimension,
        state=state,
        history=tuple(entries),
        unordered_signal_ids=tuple(e.signal_id for e in unordered),
        history_has_opposite_effects={OutlookEffect.STRENGTHENING, OutlookEffect.WEAKENING} <= effects,
    )


def synthesize_forward_signals(signals: Iterable[ForwardEconomicSignal]) -> tuple[ForwardEconomicSynthesis, ...]:
    """Pure and deterministic, independent of input order. One synthesis
    per (company, horizon kind, horizon year): a fiscal-2026 and a
    calendar-2026 signal are different horizons and never share one. One
    pass to group, one sort per dimension -- no pairwise comparison."""
    grouped: dict[tuple[str, HorizonKind, str], dict[EconomicDimension, list[SignalEntry]]] = {}
    kinds: dict[tuple[str, HorizonKind, str], set[ForwardEvidenceKind]] = {}
    for signal in signals:
        if not _is_revision(signal):
            raise ValueError(f"{signal!r} is not a revision signal; state evidence belongs in the company picture")
        key = (signal.company, signal.horizon_kind, signal.horizon_period)
        grouped.setdefault(key, {}).setdefault(signal.dimension, []).append(
            SignalEntry(
                signal_id=signal.signal_id,
                evidence_kind=signal.evidence_kind,
                source_period=signal.source_period,
                movement=signal.movement,
                outlook_effect=signal.outlook_effect,
            )
        )
        kinds.setdefault(key, set()).add(signal.evidence_kind)

    syntheses = []
    for key in sorted(grouped, key=lambda k: (k[0], k[1].value, k[2])):
        company, horizon_kind, horizon_period = key
        by_dimension = grouped[key]
        syntheses.append(
            ForwardEconomicSynthesis(
                company=company,
                horizon_period=horizon_period,
                horizon_kind=horizon_kind,
                dimensions=tuple(_summarize(d, by_dimension.get(d, [])) for d in EconomicDimension),
                evidence_kinds=tuple(sorted(kinds[key], key=lambda k: k.value)),
                synthesis_version=SYNTHESIS_VERSION,
            )
        )
    return tuple(syntheses)


_DIMENSION_LABEL = {
    EconomicDimension.REVENUE: "Revenue",
    EconomicDimension.EARNINGS: "Earnings",
    EconomicDimension.CASH_GENERATION: "Cash generation",
    EconomicDimension.INVESTMENT_SPENDING: "Investment spending",
}
_STATE_LABEL = {
    DimensionState.STRENGTHENING: "strengthening",
    DimensionState.WEAKENING: "weakening",
    DimensionState.UNCHANGED: "unchanged",
    DimensionState.AMBIGUOUS: "ambiguous in effect",
    DimensionState.CONFLICTING: "conflicting signals",
}


def describe_synthesis(synthesis: ForwardEconomicSynthesis) -> tuple[str, ...]:
    """One line per dimension, stating the evidence and nothing about
    the investment: "Investment spending: ambiguous in effect -- increased
    (2026Q1), increased (2026Q2)." / "Revenue: no forward signal." """
    lines = []
    for summary in synthesis.dimensions:
        label = _DIMENSION_LABEL[summary.dimension]
        if summary.state is DimensionState.UNSUPPORTED:
            lines.append(f"{label}: no forward signal.")
            continue
        steps = ", ".join(f"{e.movement.value} ({e.source_period or 'period unknown'})" for e in summary.history)
        lines.append(f"{label}: {_STATE_LABEL[summary.state]} -- {steps}.")
    return tuple(lines)


@dataclass(frozen=True)
class StateObservation:
    """One state signal as it enters the picture -- with the signal
    itself, so every observation leads back to its evidence."""

    signal_id: str
    evidence_kind: ForwardEvidenceKind
    source_period: str | None
    span: EvidenceSpan
    not_established: frozenset[EconomicAspect]
    signal: ForwardStateSignal


@dataclass(frozen=True)
class StateDimensionSummary:
    """Every observation of one state dimension for a company. There is
    deliberately no state, no "current" observation and no conflict:
    observations are not known to be about the same agreement."""

    state_dimension: StateDimension
    observations: tuple[StateObservation, ...]
    """Fiscal-period order; observations with no period last, by id."""
    established_by_none: frozenset[EconomicAspect]
    """Aspects not one observation establishes -- all of them, when there
    are no observations."""

    @property
    def supported(self) -> bool:
        return bool(self.observations)


@dataclass(frozen=True)
class CompanyForwardPicture:
    """A company's forward evidence of both shapes, side by side and never
    combined: the annual syntheses of revision evidence, unchanged, and
    the observations of state evidence."""

    company: str
    annual: tuple[ForwardEconomicSynthesis, ...]
    """Exactly what `synthesize_forward_signals` returns for the company's
    revision signals."""
    states: tuple[StateDimensionSummary, ...]
    """Every `StateDimension`, in declaration order."""
    evidence_kinds: tuple[ForwardEvidenceKind, ...]
    picture_version: str

    def state(self, state_dimension: StateDimension) -> StateDimensionSummary:
        return next(s for s in self.states if s.state_dimension is state_dimension)


def _observation_key(o: StateObservation) -> tuple[bool, tuple[int, int], str]:
    ordinal = period_ordinal(o.source_period)
    return (ordinal is None, ordinal or (0, 0), o.signal_id)


def synthesize_company_forward_picture(signals: Iterable[object]) -> tuple[CompanyForwardPicture, ...]:
    """Pure and deterministic, independent of input order. Each signal is
    either a revision (`ForwardEconomicSignal`) or a state
    (`ForwardStateSignal`); one that is both or neither is refused."""
    revisions: list[ForwardEconomicSignal] = []
    states: dict[str, list[StateObservation]] = {}
    for signal in signals:
        if _is_revision(signal):
            revisions.append(signal)  # type: ignore[arg-type]
        elif _is_state(signal):
            states.setdefault(signal.company, []).append(StateObservation(  # type: ignore[attr-defined]
                signal_id=signal.signal_id, evidence_kind=signal.evidence_kind,  # type: ignore[attr-defined]
                source_period=signal.source_period, span=signal.span,  # type: ignore[attr-defined]
                not_established=signal.not_established, signal=signal,  # type: ignore[attr-defined,arg-type]
            ))
        else:
            raise ValueError(f"{signal!r} is neither a revision nor a state signal, or claims to be both")
    annual = synthesize_forward_signals(revisions)
    companies = sorted({s.company for s in revisions} | set(states))
    pictures = []
    for company in companies:
        company_annual = tuple(a for a in annual if a.company == company)
        observations = states.get(company, [])
        summaries = []
        for dimension in StateDimension:
            ordered = tuple(sorted((o for o in observations if o.signal.state_dimension is dimension), key=_observation_key))
            unestablished = frozenset.intersection(*(o.not_established for o in ordered)) if ordered else ALL_ECONOMIC_ASPECTS
            summaries.append(StateDimensionSummary(dimension, ordered, unestablished))
        kinds = {k for a in company_annual for k in a.evidence_kinds} | {o.evidence_kind for o in observations}
        pictures.append(CompanyForwardPicture(
            company=company, annual=company_annual, states=tuple(summaries),
            evidence_kinds=tuple(sorted(kinds, key=lambda k: k.value)), picture_version=PICTURE_VERSION,
        ))
    return tuple(pictures)


_STATE_DIMENSION_LABEL = {StateDimension.CONTRACTED_VOLUME: "Contracted volume"}


def describe_company_forward_picture(picture: CompanyForwardPicture) -> tuple[str, ...]:
    """The annual lines exactly as `describe_synthesis` states them, each
    under its horizon, then the state observations, then what none of
    them establishes. Evidence only -- nothing about the investment."""
    lines = []
    for synthesis in picture.annual:
        lines.append(f"{synthesis.horizon_kind.value.replace('_', ' ')} {synthesis.horizon_period}:")
        lines.extend(f"  {line}" for line in describe_synthesis(synthesis))
    for summary in picture.states:
        label = _STATE_DIMENSION_LABEL[summary.state_dimension]
        if not summary.supported:
            lines.append(f"{label}: no state evidence.")
            continue
        for o in summary.observations:
            lines.append(f"{label} ({o.source_period or 'period unknown'}): {o.signal.explanation}")
        missing = ", ".join(a.value.replace("_", " ") for a in EconomicAspect if a in summary.established_by_none)
        if missing:
            lines.append(f"{label}: not established by any observation -- {missing}.")
    return tuple(lines)

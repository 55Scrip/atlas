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
visibility, and range width is not interpreted. They are added only
when a kind of forward evidence that genuinely speaks to them exists.

**Latest signal, full history.** Within a dimension, signals are placed
in fiscal-period order; the most recent one gives the current state,
and every earlier one stays in the history, so a raise followed by a
cut reads as both, in order. Only fiscal `source_period` is used --
never a date, so nothing here is "recent".

**Not only for guidance.** The synthesis reads anything that satisfies
`ForwardEconomicSignal` -- a company, a horizon, a dimension, a movement,
an effect, a period and a provenance id. Guidance interpretations are
the only kind today; a future contract or capacity interpretation fits
without changing this module.

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
    "ForwardEconomicSignal",
    "DimensionState",
    "SignalEntry",
    "DimensionSummary",
    "ForwardEconomicSynthesis",
    "synthesize_forward_signals",
    "describe_synthesis",
]

SYNTHESIS_VERSION = "forward-synthesis-v1"


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

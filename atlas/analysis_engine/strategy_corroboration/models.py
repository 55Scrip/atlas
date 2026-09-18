"""The records this layer produces.

Every corroboration item names the observation, the channel it came from,
what it corroborates, how it sits in time, and the rule that linked it.
There is no total and no score: support and weakening coexist as separate
tuples, and `CoverageState` says which silence a reader is looking at.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from atlas.analysis_engine.strategy_corroboration.contracts import (
    CorroborationRelation,
    CoverageState,
    EvidenceClass,
    IndependenceChannel,
    TemporalRelation,
)

__all__ = ["ObservedEvidence", "CorroborationItem", "NodeCorroboration", "CompanyCorroboration"]


@dataclass(frozen=True)
class ObservedEvidence:
    """One observation, with everything needed to check it and to test
    whether it is the same event as another."""

    evidence_id: str
    evidence_class: EvidenceClass
    channel: IndependenceChannel
    measure: str
    """The canonical measure name -- "capital_expenditure" -- never free
    text."""
    period: str
    """The fiscal period the observation covers, as the source states
    it."""
    published_at: datetime | date | None
    """When the source that carries it was published. Distinct from
    `period`: fiscal 2025 capital expenditure published in February 2026
    is a 2025 measurement and 2026 information."""
    value: float | None = None
    prior_value: float | None = None
    unit: str | None = None
    currency: str | None = None
    source_record_id: str = ""
    semantic_owner: str = ""
    """Which Atlas layer owns this object -- `business_facts`,
    `forward_claims`. Recorded so nothing here is mistaken for a second
    truth about it."""

    @property
    def direction(self) -> str | None:
        """Which way the measure moved, or `None` when there is nothing
        to compare against. Direction only -- no magnitude, no
        percentage, and deliberately no threshold: "capital expenditure
        rose" is defensible, and "capital expenditure rose enough"
        requires a doctrine Atlas does not have."""
        if self.value is None or self.prior_value is None:
            return None
        if self.value > self.prior_value:
            return "increased"
        if self.value < self.prior_value:
            return "decreased"
        return "unchanged"

    @property
    def event_key(self) -> tuple:
        """Two observations sharing this are the same underlying event
        counted twice. Channel, measure and period together: one
        company's fiscal-2025 capital expenditure is one fact however
        many records or speakers mention it."""
        return (self.channel, self.measure, self.period)


@dataclass(frozen=True)
class CorroborationItem:
    """One observation, linked to one strategy node, with the rule."""

    node_id: str
    evidence: ObservedEvidence
    relation: CorroborationRelation
    temporal: TemporalRelation
    derivation_rule: str
    explanation: str = ""

    def __post_init__(self) -> None:
        if not self.derivation_rule:
            raise ValueError("a corroboration link names the rule that produced it")
        if self.evidence.evidence_class is EvidenceClass.STATED_INTENT:
            raise ValueError(
                "management language cannot corroborate management language; "
                "STATED_INTENT exists to be excluded"
            )
        if (
            self.temporal is TemporalRelation.PRECEDES_STRATEGY
            and self.relation is not CorroborationRelation.CONTEXT_ONLY
        ):
            raise ValueError(
                "an observation whose period precedes the statement cannot corroborate "
                "executing it; that is backwards leakage"
            )


@dataclass(frozen=True)
class NodeCorroboration:
    """What Atlas observed about one strategy node, and why."""

    node_id: str
    company: str
    node_kind: str
    subject_text: str
    supporting: tuple[CorroborationItem, ...] = ()
    weakening: tuple[CorroborationItem, ...] = ()
    context: tuple[CorroborationItem, ...] = ()
    searched_measures: tuple[str, ...] = ()
    """Measures Atlas looked for. Without this, "nothing found" and
    "nothing looked for" are the same output."""
    unavailable_measures: tuple[str, ...] = ()
    """Measures the strategy implies and Atlas has no channel for --
    headcount, research spending, physical capacity."""

    @property
    def coverage(self) -> CoverageState:
        if self.supporting and self.weakening:
            return CoverageState.MIXED
        if self.supporting:
            return CoverageState.OBSERVED_SUPPORTING
        if self.weakening:
            return CoverageState.OBSERVED_WEAKENING
        if self.unavailable_measures and not self.searched_measures:
            return CoverageState.EVIDENCE_SOURCE_UNAVAILABLE
        if not self.searched_measures:
            return CoverageState.SEMANTIC_LINK_UNAVAILABLE
        return CoverageState.NO_INDEPENDENT_EVIDENCE

    @property
    def independent_event_count(self) -> int:
        """Distinct underlying events, not items. Two links built from
        one fiscal year's capital expenditure are one observation."""
        return len({i.evidence.event_key for i in self.supporting + self.weakening})

    @property
    def may_not_conclude(self) -> tuple[str, ...]:
        """Carried on every result, because the sentence a reader is
        most likely to form from "supported" is one of these."""
        claims = [
            "that the strategy caused any observed change",
            "that the strategy is succeeding or will succeed",
            "that the observed amounts are economically material",
            "that an adequate return will follow",
        ]
        if self.coverage is CoverageState.NO_INDEPENDENT_EVIDENCE:
            claims.insert(0, "that the company did not act -- Atlas found no evidence, which is not the same")
        if self.coverage is CoverageState.EVIDENCE_SOURCE_UNAVAILABLE:
            claims.insert(0, "anything at all about this measure; Atlas has no channel that could observe it")
        return tuple(claims)


@dataclass(frozen=True)
class CompanyCorroboration:
    """Everything Atlas observed about one company's strategy nodes."""

    company: str
    nodes: tuple[NodeCorroboration, ...] = ()
    corroborator_version: str = ""
    evaluated_at: datetime | None = None
    excluded_channels: tuple[str, ...] = field(default_factory=tuple)
    """Channels deliberately not consulted, named in the output so their
    absence is a decision rather than an oversight -- share price above
    all."""

    def node(self, node_id: str) -> NodeCorroboration | None:
        return next((n for n in self.nodes if n.node_id == node_id), None)

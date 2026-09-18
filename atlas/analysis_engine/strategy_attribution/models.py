"""The records this layer produces.

Every attribution has three sides -- a strategy node, an action or
allocation, and a **linking fact** -- and cannot be built without all
three. There is no edge whose justification is that both ends exist.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from atlas.analysis_engine.strategy_attribution.contracts import (
    ActionTense,
    AttributionBasis,
    AttributionResolution,
    AttributionStatus,
    EvidenceRole,
)

__all__ = ["EvidenceRef", "AttributedAmount", "LinkingFact", "ActionAttribution", "CompanyAttribution"]


@dataclass(frozen=True)
class EvidenceRef:
    """One locatable passage or record, and the role it plays."""

    role: EvidenceRole
    source_record_id: str
    source_kind: str
    period: str | None
    published_at: datetime | date | None
    semantic_owner: str
    text: str = ""
    speaker_title: str | None = None

    @property
    def is_management_authored(self) -> bool:
        return self.source_kind == "transcript"


@dataclass(frozen=True)
class AttributedAmount:
    """An amount tied to a purpose, with what is left over stated.

    **The residual is never allocated.** If management attributes $4bn
    of a $10bn programme, the other $6bn is unattributed and stays that
    way; inferring it would require the disclosed categories to be
    collectively exhaustive, which no evidence here establishes."""

    value_text: str
    """Management's own words for the amount -- "more than $200 million",
    "approximately $3 billion". Kept verbatim rather than parsed, because
    "more than" and "approximately" are part of the claim."""
    unit_text: str = ""
    total_context_text: str = ""
    """The larger figure this was drawn from, where the passage states
    one. Empty when it does not."""
    residual_is_unallocated: bool = True

    @property
    def may_not_conclude(self) -> tuple[str, ...]:
        return (
            "that any amount beyond the attributed one belongs to this strategy",
            "that the attributed amount is economically material",
        )


@dataclass(frozen=True)
class LinkingFact:
    """The fact that connects a strategy to an action.

    Without one there is no attribution. The type exists so that the
    link is a thing with provenance rather than an inference performed
    in a function and forgotten."""

    basis: AttributionBasis
    resolution: AttributionResolution
    target_name: str
    """The named project, place, counterparty or asset. Empty only for
    COMPANY resolution."""
    evidence: EvidenceRef
    tense: ActionTense
    amount: AttributedAmount | None = None

    def __post_init__(self) -> None:
        if self.resolution is not AttributionResolution.COMPANY and not self.target_name:
            raise ValueError("a resolution finer than the company names the thing it resolves to")
        if self.evidence.role is not EvidenceRole.LINKING:
            raise ValueError("a linking fact carries linking evidence")


@dataclass(frozen=True)
class ActionAttribution:
    """One strategy node, and what Atlas can and cannot place against it."""

    node_id: str
    company: str
    node_kind: str
    subject_text: str
    status: AttributionStatus
    links: tuple[LinkingFact, ...] = ()
    action_evidence: tuple[EvidenceRef, ...] = ()
    """Independent evidence that an action occurred, when Atlas has any.
    Separate from `links` on purpose: a linking fact says what the money
    was for, and this says that money moved. One source rarely does
    both."""
    searched_channels: tuple[str, ...] = ()
    unavailable_channels: tuple[str, ...] = ()
    derivation_rule: str = ""

    @property
    def resolutions(self) -> tuple[AttributionResolution, ...]:
        return tuple(dict.fromkeys(link.resolution for link in self.links))

    @property
    def has_independent_action_evidence(self) -> bool:
        return any(not ref.is_management_authored for ref in self.action_evidence)

    @property
    def attribution_is_management_authored(self) -> bool:
        """True when every linking fact came from a transcript.

        The load-bearing property of this layer: an attribution can be
        precise, quantified and entirely management's own account."""
        return bool(self.links) and all(link.evidence.is_management_authored for link in self.links)

    @property
    def may_conclude(self) -> str:
        if self.status is AttributionStatus.NO_ATTRIBUTION_EVIDENCE:
            return (
                "Atlas has found no evidence allocating any observed action specifically "
                "to this strategy; observations remain at company level."
            )
        if self.status is AttributionStatus.AMBIGUOUS:
            return (
                f"the action can be placed at {', '.join(r.value for r in self.resolutions)} "
                "level, and not allocated further"
            )
        if self.status is AttributionStatus.CANDIDATE_ONLY:
            return "a candidate link exists and no linking fact supports it"
        target = ", ".join(sorted({link.target_name for link in self.links if link.target_name}))
        tense = "was" if any(link.tense is ActionTense.OBSERVED_PAST for link in self.links) else "is intended to be"
        return f"an allocation {tense} tied to {target or 'the company'} by the cited passage"

    @property
    def may_not_conclude(self) -> tuple[str, ...]:
        claims = [
            "that the strategy caused any observed change",
            "that the attributed amount is economically material",
            "that the strategy is succeeding",
        ]
        if self.attribution_is_management_authored:
            claims.insert(
                0,
                "that the allocation is independently verified -- the link is management's own account",
            )
        if any(link.tense is ActionTense.STATED_INTENT for link in self.links):
            claims.insert(0, "that the stated amount was actually spent")
        if self.status is AttributionStatus.NO_ATTRIBUTION_EVIDENCE:
            claims.insert(0, "that no such allocation occurred -- Atlas found no evidence, which is different")
        if self.status is AttributionStatus.AMBIGUOUS:
            claims.insert(0, "which of the strategies within that scope received the action")
        return tuple(claims)


@dataclass(frozen=True)
class CompanyAttribution:
    company: str
    nodes: tuple[ActionAttribution, ...] = ()
    attributor_version: str = ""
    evaluated_at: datetime | None = None
    unavailable_channels: tuple[str, ...] = field(default_factory=tuple)
    """Channels audited and found absent corpus-wide, named so their
    absence is a measurement rather than an omission."""

    def node(self, node_id: str) -> ActionAttribution | None:
        return next((n for n in self.nodes if n.node_id == node_id), None)

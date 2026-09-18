"""What Atlas records about how central a strategy node appears.

Every field is a count or a set, and every one of them carries the
evidence it was counted from. There is no total, no weight and no label:
the reader is handed the signals and does the combining, because any
combination Atlas performed here would be a judgement disguised as
arithmetic.

**Management and analysts are kept in separate fields and never added.**
An issue analysts press management about four quarters running is
evidence of market attention; it is not evidence that management
prioritises it, and the two are different facts about a company. Merging
them would let the sell-side author Atlas's view of a strategy.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from atlas.analysis_engine.strategy_salience.contracts import CallSection, SpeakerRole

__all__ = [
    "PassageRef",
    "SpeakerMention",
    "AnalystAttention",
    "PriorityLanguage",
    "GraphLinkage",
    "ForwardEvidenceLink",
    "SalienceEvidence",
]


@dataclass(frozen=True)
class PassageRef:
    """One locatable passage: which record, which period, who said it,
    and where in the call. Every counter in this module is a count of
    these, so no number exists that cannot be expanded back into the
    sentences behind it."""

    source_record_id: str
    period: str | None
    speaker: str | None
    speaker_title: str | None
    role: SpeakerRole
    section: CallSection
    text: str


@dataclass(frozen=True)
class SpeakerMention:
    """One management voice that evidenced this node, and where."""

    speaker: str | None
    title: str | None
    role: SpeakerRole
    periods: tuple[str, ...]
    refs: tuple[PassageRef, ...]


@dataclass(frozen=True)
class AnalystAttention:
    """Market attention on this node's subject -- deliberately its own
    type, so it can never be added to a management count by accident.

    What it means: analysts asked about this. What it does not mean:
    management prioritises it, the issue is real, or the issue is
    large."""

    distinct_analysts: tuple[str, ...]
    periods: tuple[str, ...]
    refs: tuple[PassageRef, ...]

    @property
    def analyst_count(self) -> int:
        return len(self.distinct_analysts)


@dataclass(frozen=True)
class PriorityLanguage:
    """Management naming something a priority, in words that commit.

    Strict by design. The corpus offers fifteen such sentences across
    four companies and 277 sentences containing "important", "excited",
    "opportunity" or "well positioned" -- an eighteen-to-one ratio that
    is the whole argument for the strictness. Vague enthusiasm is not
    counted here at all, in either direction: its absence is not
    evidence against a node."""

    refs: tuple[PassageRef, ...]

    @property
    def count(self) -> int:
        return len(self.refs)


@dataclass(frozen=True)
class GraphLinkage:
    """How many distinct typed relations touch this node, by relation.

    **Degree is not importance.** A node with six edges may simply share
    a common factor with six other nodes. This is published as structure
    a reader can inspect, not as a ranking, and nothing in this package
    sorts by it."""

    by_relation: dict[str, int] = field(default_factory=dict)
    linked_node_ids: tuple[str, ...] = ()

    @property
    def degree(self) -> int:
        return len(self.linked_node_ids)


@dataclass(frozen=True)
class ForwardEvidenceLink:
    """A guidance revision or customer commitment the caller has
    associated with this node.

    Supplied by the caller, never fetched: the forward-evidence layer
    owns those objects and this package does not import it. On the
    benchmark corpus every one of these is empty, and that is a finding
    rather than a gap -- see the sprint report."""

    kind: str
    signal_id: str
    description: str


@dataclass(frozen=True)
class SalienceEvidence:
    """Everything Atlas can say about how central one strategy node
    appears, with nothing combined.

    Deliberately absent: a score, a rank, a label, and any field derived
    from revenue, earnings or capital. What is here is what a reader
    would otherwise have to reconstruct by hand from sixteen earnings
    calls."""

    node_id: str
    company: str
    node_kind: str
    subject_text: str

    # --- management-authored signals ---------------------------------
    periods: tuple[str, ...] = ()
    """Distinct reporting periods in which this node was observed,
    ascending. Taken from the node's own `observed_periods`, which is
    already one-node-per-assertion, so a duplicated corpus cannot
    inflate it."""
    speakers: tuple[SpeakerMention, ...] = ()
    prepared_remark_refs: tuple[PassageRef, ...] = ()
    """Evidence stated before any analyst spoke: what management chose
    to raise."""
    qa_refs: tuple[PassageRef, ...] = ()
    """Evidence stated in answers: what management was asked about."""
    priority_language: PriorityLanguage = PriorityLanguage(refs=())

    # --- market-authored signals, never merged with the above --------
    analyst_attention: AnalystAttention = AnalystAttention((), (), ())

    # --- structural signals -------------------------------------------
    graph_linkage: GraphLinkage = field(default_factory=GraphLinkage)
    resource_commitment_links: tuple[str, ...] = ()
    forward_links: tuple[ForwardEvidenceLink, ...] = ()

    # --- temporal ------------------------------------------------------
    continuity: str = ""
    latest_period: str | None = None
    corpus_latest_period: str | None = None
    """The most recent period anywhere in this company's corpus. Carried
    so a reader can see whether a node's last mention *is* the latest
    call or four quarters behind it -- without Atlas applying a decay
    weight it cannot justify."""

    @property
    def period_count(self) -> int:
        return len(self.periods)

    @property
    def management_speaker_count(self) -> int:
        """Distinct management voices. Analysts are not in `speakers` at
        all, so this cannot accidentally include them."""
        return len(self.speakers)

    @property
    def is_current(self) -> bool | None:
        """Whether the node's latest observation is the corpus's latest
        period. `None` when either is unknown.

        Deliberately not "is this still true": a strategy stated three
        quarters ago and not repeated may be unchanged, completed, or
        quietly dropped, and this corpus cannot tell those apart."""
        if self.latest_period is None or self.corpus_latest_period is None:
            return None
        return self.latest_period == self.corpus_latest_period

    @property
    def all_refs(self) -> tuple[PassageRef, ...]:
        """Every passage behind every signal, for provenance checks."""
        refs: list[PassageRef] = []
        for mention in self.speakers:
            refs.extend(mention.refs)
        refs.extend(self.prepared_remark_refs)
        refs.extend(self.qa_refs)
        refs.extend(self.priority_language.refs)
        refs.extend(self.analyst_attention.refs)
        seen: set[tuple[str, str]] = set()
        unique: list[PassageRef] = []
        for ref in refs:
            key = (ref.source_record_id, ref.text)
            if key not in seen:
                seen.add(key)
                unique.append(ref)
        return tuple(unique)

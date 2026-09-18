"""The strategy graph's records.

**Every node carries its passage.** `source_text` is verbatim, never a
paraphrase and never generated prose. A node whose passage cannot be
located in its own source record is a node Atlas cannot defend, so
extraction produces none -- the same rule `ForwardClaim` holds itself to,
for the same reason.

**Time is three separate questions**, answered the way `ForwardClaim`
answers them, because the sources are the same records:

- `source_period` -- the fiscal quarter the call reported on, the
  provider's own label ("2026Q2"). It orders one company's calls.
- `statement_at` -- when management said it. `None` unless the source
  supplies it, and Alpha Vantage does not. A fetch time is never
  substituted: it would make a two-year-old strategy look like this
  morning's.
- `observed_periods` -- every period in which this assertion was
  restated, ascending. This is what makes strategy temporal rather than
  a snapshot: a node is not replaced when it is repeated, it accumulates
  an observation, and the 2025Q3 reading stays queryable after the
  2026Q2 one arrives.

**A node is never overwritten by a later one.** `superseded_by` records
that a later node modified this one; both remain in the graph, and a
consumer asking for the current strategy filters, rather than trusting
that history was deleted correctly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from atlas.analysis_engine.strategy.contracts import (
    ContinuityState,
    EvidenceStatus,
    FactorClass,
    OutcomeKind,
    RelationKind,
    ResourceKind,
    StrategyNodeKind,
    StrategyRejectionReason,
    SupportPolarity,
)

__all__ = [
    "StrategyEvidence",
    "StrategyNode",
    "StrategyEdge",
    "FactorParticipation",
    "CrossCompanyAdjacency",
    "RejectedStrategyCandidate",
    "CompanyStrategy",
]


@dataclass(frozen=True)
class StrategyEvidence:
    """A provenance-bearing link to one source observation.

    Deliberately not a copy of the source record: `source_record_id`
    points at the record Atlas already persists, and `source_text` is
    the one sentence the assertion rests on. Nothing here is a second
    truth about the document."""

    source_record_id: str
    source_text: str
    """The verbatim sentence. Extraction asserts it is a substring of
    the record's own content before building anything from it."""
    source_kind: str
    """The record's `document_type` -- "transcript", "company_filing"."""
    company: str
    source_period: str | None
    statement_at: datetime | None
    speaker_title: str | None
    polarity: SupportPolarity = SupportPolarity.SUPPORTS
    extractor_version: str = ""

    @property
    def evidence_id(self) -> str:
        return f"{self.source_record_id}:{hash(self.source_text) & 0xFFFFFFF:07x}"


@dataclass(frozen=True)
class StrategyNode:
    """One assertion about what a company is trying to do, doing,
    committing, depending on, expecting, or exposed to.

    `subject` is the assertion in Atlas's own controlled vocabulary --
    a `FactorClass`, `ResourceKind` or `OutcomeKind` -- never free text.
    `subject_text` is how management put it, kept only so a reader can
    disagree with the mapping."""

    node_id: str
    company: str
    kind: StrategyNodeKind
    status: EvidenceStatus

    factor: FactorClass | None = None
    resource: ResourceKind | None = None
    outcome: OutcomeKind | None = None
    subject_text: str = ""
    """Management's own words for the object, trimmed to the clause."""

    evidence: tuple[StrategyEvidence, ...] = ()
    observed_periods: tuple[str, ...] = ()
    continuity: ContinuityState = ContinuityState.NEW
    superseded_by: str | None = None

    derivation_rule: str | None = None
    """For DERIVED and HYPOTHESIS nodes: the named rule that produced
    this, so the composition is reproducible and arguable. `None` for
    OBSERVED nodes, whose derivation is "management said it"."""
    derived_from: tuple[str, ...] = ()
    """Node ids this was composed from. Empty for OBSERVED."""

    def __post_init__(self) -> None:
        if self.status is EvidenceStatus.OBSERVED and not self.evidence:
            raise ValueError("an OBSERVED node states what a source says, so it carries that source")
        if self.status in (EvidenceStatus.DERIVED, EvidenceStatus.HYPOTHESIS) and not self.derivation_rule:
            raise ValueError("a DERIVED or HYPOTHESIS node names the rule that produced it")
        if self.status is EvidenceStatus.OBSERVED and self.derivation_rule:
            raise ValueError("an OBSERVED node is not derived; it is read")

    @property
    def supporting(self) -> tuple[StrategyEvidence, ...]:
        return tuple(e for e in self.evidence if e.polarity is SupportPolarity.SUPPORTS)

    @property
    def contradicting(self) -> tuple[StrategyEvidence, ...]:
        """Evidence that argues against this node. **Emptiness here is
        not agreement.** Nothing in Atlas may read an empty tuple as
        confirmation; it means no contradicting passage was found, which
        is the normal state of almost every assertion."""
        return tuple(e for e in self.evidence if e.polarity is SupportPolarity.CONTRADICTS)


@dataclass(frozen=True)
class StrategyEdge:
    """A typed relation between two nodes.

    An edge carries its own status. An objective and an initiative can
    both be OBSERVED while the link between them is DERIVED, because
    management named both in one sentence and never said one serves the
    other."""

    source_id: str
    target_id: str
    relation: RelationKind
    status: EvidenceStatus
    evidence: tuple[StrategyEvidence, ...] = ()
    derivation_rule: str | None = None

    def __post_init__(self) -> None:
        if self.status is EvidenceStatus.OBSERVED and not self.evidence:
            raise ValueError("an OBSERVED edge carries the passage that states the relation")
        if self.status in (EvidenceStatus.DERIVED, EvidenceStatus.HYPOTHESIS) and not self.derivation_rule:
            raise ValueError("a DERIVED or HYPOTHESIS edge names its rule")


@dataclass(frozen=True)
class FactorParticipation:
    """How one company stands toward one canonical factor: it needs it,
    it is building capacity in it, or both.

    This is the whole of the cross-company machinery. Two companies
    joined here are two rows that mention the same canonical factor --
    an adjacency in Atlas's vocabulary, and nothing else."""

    company: str
    factor: FactorClass
    requires: tuple[str, ...] = ()
    """Node ids of DEPENDENCY nodes on this factor."""
    builds: tuple[str, ...] = ()
    """Node ids of INITIATIVE nodes adding capacity in this factor --
    for whoever ends up using it, which the evidence does not say."""


@dataclass(frozen=True)
class CrossCompanyAdjacency:
    """Two companies exposed to one canonical factor from opposite
    sides: A states it depends on X, B states it is building capacity
    in X.

    **This is a HYPOTHESIS and cannot be anything else**, and the
    hypothesis is narrower than it first looks. The first benchmark run
    modelled B's side as "provides" and produced "GOOGL provides compute
    capacity to NVDA" out of two sentences about two companies' own
    build-outs -- a commercial relationship manufactured by a join.
    Building capacity in a factor says nothing about who receives the
    output; a company overwhelmingly builds for itself.

    So what is on offer here is co-exposure: one factor, two companies,
    two opposite postures toward it, and a reason for a human to look.
    A supply relationship between the two would be a
    `CustomerCommitmentClaim` -- a different object, with a contract
    behind it."""

    factor: FactorClass
    requiring_company: str
    building_company: str
    requiring_node_id: str
    building_node_id: str
    status: EvidenceStatus = EvidenceStatus.HYPOTHESIS
    derivation_rule: str = "shared-canonical-factor"

    @property
    def may_conclude(self) -> str:
        return (
            f"{self.requiring_company} states a dependency on {self.factor.value}; "
            f"{self.building_company} states an initiative adding capacity in {self.factor.value}. "
            "Both are exposed to the same canonical factor, from opposite sides."
        )

    @property
    def may_not_conclude(self) -> tuple[str, ...]:
        return (
            f"that {self.building_company} supplies {self.requiring_company}, or ever will",
            f"that {self.building_company} benefits from {self.requiring_company}'s demand",
            f"that {self.building_company}'s capacity is available to anyone outside {self.building_company}",
            "that either company's revenue, earnings or cash flow is affected",
            "that a change in the factor moves the two in opposite directions",
        )


@dataclass(frozen=True)
class RejectedStrategyCandidate:
    """A sentence that carried a strategy marker and produced no node.

    Kept as real output: the rejections are how a reader audits whether
    the layer is conservative or merely quiet."""

    company: str
    source_record_id: str
    text: str
    reason: StrategyRejectionReason


@dataclass(frozen=True)
class CompanyStrategy:
    """Everything Atlas holds about one company's strategy, as a read
    model over evidence it already has. Nothing here is persisted."""

    company: str
    nodes: tuple[StrategyNode, ...] = ()
    edges: tuple[StrategyEdge, ...] = ()
    rejected: tuple[RejectedStrategyCandidate, ...] = ()
    unknowns: tuple[str, ...] = ()
    """Node kinds the corpus could not support, named explicitly. An
    empty strategy and an unexamined one must not look alike."""
    extractor_version: str = ""
    composed_at: datetime | None = None

    def of_kind(self, kind: StrategyNodeKind) -> tuple[StrategyNode, ...]:
        return tuple(n for n in self.nodes if n.kind is kind)

    def node(self, node_id: str) -> StrategyNode | None:
        return next((n for n in self.nodes if n.node_id == node_id), None)

    @property
    def factor_participation(self) -> tuple[FactorParticipation, ...]:
        by_factor: dict[FactorClass, tuple[list[str], list[str]]] = {}
        for node in self.nodes:
            if node.factor is None:
                continue
            requires, builds = by_factor.setdefault(node.factor, ([], []))
            if node.kind is StrategyNodeKind.DEPENDENCY:
                requires.append(node.node_id)
            elif node.kind is StrategyNodeKind.INITIATIVE:
                builds.append(node.node_id)
        return tuple(
            FactorParticipation(
                company=self.company, factor=factor, requires=tuple(req), builds=tuple(build)
            )
            for factor, (req, build) in sorted(by_factor.items(), key=lambda kv: kv[0].value)
        )

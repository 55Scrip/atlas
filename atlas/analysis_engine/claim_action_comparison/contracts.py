"""What one comparison of a claim against an observed action records.

The vocabulary is deliberately small and says nothing about causation, success
or materiality. A relation here means only: this observed action is capable of
bearing on what management claimed. Whether the claim was met, whether the
strategy worked, and whether any of it matters are later questions this layer
must not answer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

CLAIM_ACTION_COMPARISON_VERSION = "claim-action-comparison-1"


class Relation(str, Enum):
    """Earned from the frozen human adjudication of 58 pairs.

    There is no contradiction relation: the bounded corpus contains no action
    that runs against a claim, so one would be unearned.
    """

    #: the action is an observed instance of the act the claim describes
    RELEVANT_EXECUTION = "relevant_execution"
    #: the action concerns a dependency the claim explicitly names -- never the
    #: claimed act itself
    RELEVANT_DEPENDENCY = "relevant_dependency"
    #: comparable in kind, but it does not bear on this claim
    NOT_RELEVANT = "not_relevant"
    #: the claim states nothing this action could bear on, either way
    NOT_COMPARABLE = "not_comparable"


class Compatibility(str, Enum):
    """A dimension's verdict. UNKNOWN is a real answer, not a soft no."""

    MATCH = "match"
    MISMATCH = "mismatch"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class EntityBasis(str, Enum):
    """*How* the entity was matched, because the strength differs.

    An entity the action model put in a role it asserts (object, counterparty)
    is stronger evidence than one that merely appears in the sentence. The
    weaker basis is kept because Action Evidence truncates trailing adjuncts,
    so "West Texas" survives only in the verbatim sentence.
    """

    ASSERTED_ROLE = "asserted_role"
    SOURCE_SPAN = "source_span"
    SELF_DIRECTED_ACT = "self_directed_act"
    """The company acting on its own economic object -- buying back its own
    shares. There is no third party to match, so the usual external-entity
    evidence cannot exist. This basis is not "same issuer": it is granted only
    when both sides report the same completed act by the filer upon itself,
    and ISSUER_ONLY remains insufficient everywhere else."""
    ISSUER_ONLY = "issuer_only"
    NONE = "none"


class TemporalRelation(str, Enum):
    ACTION_AFTER_CLAIM = "action_after_claim"
    ACTION_SAME_PERIOD = "action_same_period"
    ACTION_BEFORE_CLAIM = "action_before_claim"
    UNKNOWN = "unknown"


#: Why a comparison refused. Every refusal names itself; silence is not an
#: answer this layer is allowed to give.
REFUSAL_REASONS = (
    "insufficient_claim_semantics",   # the claim states nothing observable
    "no_shared_event_vocabulary",     # the action is a state, not an act
    "entity_issuer_only",             # only the issuer matches
    "entity_unresolved",              # no entity evidence either way
    "event_mismatch",                 # the act observed is not the act claimed
    "temporal_action_before_claim",   # it happened before the claim was made
)


@dataclass(frozen=True)
class ClaimRef:
    """Enough to find the claim again, never a copy of it."""

    issuer: str
    node_id: str
    source_period: str
    predicate: str
    passage: str


@dataclass(frozen=True)
class ActionRef:
    issuer: str
    accession: str
    key: str
    predicate: str
    sentence: str


@dataclass(frozen=True)
class ClaimActionComparison:
    """One claim against one action. Inputs are never modified."""

    claim: ClaimRef
    action: ActionRef
    relation: Relation
    entity: Compatibility
    entity_basis: EntityBasis
    entity_surfaces: tuple[str, ...]
    event: Compatibility
    measure: Compatibility
    direction: Compatibility
    temporal: Compatibility
    temporal_relation: TemporalRelation
    dependency: Compatibility
    refusal_reasons: tuple[str, ...] = ()
    version: str = CLAIM_ACTION_COMPARISON_VERSION

    @property
    def is_relevant(self) -> bool:
        return self.relation in (Relation.RELEVANT_EXECUTION, Relation.RELEVANT_DEPENDENCY)

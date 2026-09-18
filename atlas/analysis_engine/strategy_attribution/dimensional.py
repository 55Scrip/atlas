"""Dimensional evidence as an attribution channel.

Sprint 9 left `AttributionBasis.DERIVED_STRUCTURAL` defined and
unreachable, with a note saying it existed so that "a layer that had no
word for it would quietly file the first segment figure it ever saw
under a management quote". Sprints 11 and 12 produced the data. This is
the channel that reads it, and it is written to refuse.

**The standard.** An attribution needs two edges, each independently
evidenced, and then a composition that is valid:

    strategy node --[management names the entity]--> entity
    entity        --[the filing's own context]-----> dimensional fact

Both edges, or nothing. Neither edge is inferred from the other, and
neither is inferred from belonging to the same company, the same
period, the same segment, the same market, or the same word.

**Why the second edge is the easy one.** A dimensional fact carries the
member the filer tagged it with. That the fact belongs to Comanche Peak
is not a judgment Atlas makes; it is what the document says. The hard
edge is the first: that a *strategy* belongs to that entity.

**Why both edges can hold and the answer still be no.** VST's 10-K
tags six facts to `ComanchePeakNuclearPowerPlantMember`, and management
says "the data center at Comanche Peak is completed on schedule". Both
edges exist. The facts are an asset retirement obligation, a
decommissioning trust's fair value, a regulatory liability and
insurance limits -- nothing about a data centre. Co-location at a site
is not attribution to an initiative, so the measure has to be checked
too, and this is the case that proves it.

**Three traps this corpus actually contains**, each of which a looser
rule would fall into:

`LineOfCreditFacilityMaximumBorrowingCapacity` is *capacity*, in
dollars, of a credit facility -- 20 of VST's 73 capacity-named facts.
A megawatt initiative must never collect them.

`ElectricGenerationFacilityCapacityAnnouncedRetirement` is 1,108 MW at
a named plant, and it is capacity being *retired*. Attaching it to a
growth initiative inverts its meaning.

Moss Landing Phase I reads 300 MW in January 2025 and 100 MW in
December. That is a fire, not a strategy. A level is not a change, and
two levels are not a change either unless something says so.

**Nothing here is specific to a company.** No ticker, no plant list, no
issuer namespace. Every rule is stated over the generic dimensional
contract, and VST is the benchmark that falsifies it rather than the
subject it was written for.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from atlas.analysis_engine.strategy_attribution.contracts import (
    AttributionBasis,
    AttributionResolution,
)

__all__ = [
    "DIMENSIONAL_CHANNEL_VERSION",
    "MeasureKind",
    "RejectionReason",
    "EntityReference",
    "NodeEntityEdge",
    "EntityFactEdge",
    "DimensionalCandidate",
    "classify_measure",
    "entity_display_name",
    "node_entity_edge",
    "entity_fact_edge",
    "compose",
]

DIMENSIONAL_CHANNEL_VERSION = "dimensional-attribution-1"


class MeasureKind(str, Enum):
    """What an observation is *of*.

    Attribution places an observation against a strategy; it cannot do
    that without knowing what kind of observation it is. Revenue in a
    segment an initiative touches is an economic observation, not
    evidence the initiative was executed, and the two must not share a
    word."""

    PHYSICAL_CAPACITY = "physical_capacity"
    """A quantity of physical capability -- megawatts, units. Only when
    the unit says so; a concept named "capacity" is not enough."""
    CAPACITY_RETIREMENT = "capacity_retirement"
    """Physical capability being withdrawn. Kept apart from
    PHYSICAL_CAPACITY because the sign is the meaning."""
    BORROWING_CAPACITY = "borrowing_capacity"
    """A credit facility's size. Shares the word "capacity" with the
    physical kind and nothing else."""
    RESOURCE_DEPLOYMENT = "resource_deployment"
    """Money spent or committed -- capital expenditure, research and
    development. The closest thing to evidence of execution."""
    ECONOMIC_OBSERVATION = "economic_observation"
    """Revenue, income, margin. What happened in a business, not what
    was done to it."""
    OBLIGATION = "obligation"
    """Liabilities, retirement obligations, regulatory liabilities."""
    TRANSACTION = "transaction"
    """Consideration, purchase price, acquired counts."""
    INSURANCE = "insurance"
    IMPAIRMENT = "impairment"
    """A write-down. Never evidence that an initiative advanced."""
    OTHER = "other"


#: Concept-local-name patterns, checked in order. Written against
#: US-GAAP and IFRS naming, never against an issuer's extensions -- an
#: issuer-specific concept falls to OTHER rather than being guessed at.
_MEASURE_PATTERNS: tuple[tuple[str, MeasureKind], ...] = (
    (r"Impairment", MeasureKind.IMPAIRMENT),
    (r"CapacityAnnouncedRetirement|PlannedRetirement", MeasureKind.CAPACITY_RETIREMENT),
    (r"(?:LineOfCredit|BorrowingBase|SecuritizationProgram|RepurchaseFacility).*Capacity",
     MeasureKind.BORROWING_CAPACITY),
    (r"Insurance", MeasureKind.INSURANCE),
    (r"AssetRetirementObligation|RegulatoryLiabilit|Provision|Obligation", MeasureKind.OBLIGATION),
    (r"BusinessAcquisition|BusinessCombination|ConsiderationTransferred|PurchasePrice",
     MeasureKind.TRANSACTION),
    (r"PaymentsToAcquire|CapitalExpenditure|ResearchAndDevelopment|PaymentsForCapital",
     MeasureKind.RESOURCE_DEPLOYMENT),
    (r"Revenue|OperatingIncome|GrossProfit|NetIncome|CostOfGoods|CostOfSales",
     MeasureKind.ECONOMIC_OBSERVATION),
)

#: Units that make a quantity physical. A concept's name never does.
_PHYSICAL_UNITS = ("mw", "gw", "kw", "mwh", "gwh", "megawatt", "gigawatt")


class RejectionReason(str, Enum):
    """Why a candidate did not become an attribution.

    Published rather than swallowed: the value of this channel on the
    present corpus is entirely in these."""

    NO_NODE_ENTITY_LINK = "no_node_entity_link"
    """No management evidence ties the strategy to the entity. The
    commonest answer, and the one that keeps a company's every segment
    fact from landing on its every initiative."""
    NO_ENTITY_FACT_LINK = "no_entity_fact_link"
    """The entity the strategy names has no dimension member -- Atlas
    holds no fact tagged to it."""
    AMBIGUOUS_ENTITY = "ambiguous_entity"
    """The name resolves to more than one member and nothing chooses."""
    MEASURE_MISMATCH = "measure_mismatch"
    """Both edges hold and the fact does not measure anything the node
    is about."""
    RESOLUTION_MISMATCH = "resolution_mismatch"
    TEMPORAL_MISMATCH = "temporal_mismatch"
    STATE_NOT_CHANGE = "state_not_change"
    """A level was offered as evidence of a change."""
    LEXICAL_ONLY = "lexical_only"
    """A shared word and nothing else."""
    CONTRARY_EVIDENCE = "contrary_evidence"
    """The fact bears on the entity and points the other way -- capacity
    being retired, an asset written down. Distinguished from a plain
    mismatch because it is not that the measure is irrelevant; it is
    that reading it as support would invert its meaning."""


@dataclass(frozen=True)
class EntityReference:
    """A named thing a fact is tagged to, as the filing spells it."""

    member_qname: str
    axis_qname: str
    display_name: str
    """The member's name in prose, derived from its QName. Used only to
    look for the name in a management passage -- never to decide that
    two differently-named members are the same thing."""
    source_locator: str


@dataclass(frozen=True)
class NodeEntityEdge:
    """Management's own words tying a strategy node to a named entity."""

    node_id: str
    entity: EntityReference
    passage: str
    source_record_id: str
    source_period: str
    is_management_authored: bool = True
    """Always true today: the only channel that carries this edge is a
    transcript. Recorded rather than assumed so the composition can say
    so out loud."""


@dataclass(frozen=True)
class EntityFactEdge:
    """The filing's own context tying a fact to a named entity."""

    entity: EntityReference
    fact_key: str
    concept: str
    value_text: str
    unit: str | None
    period_end: str | None
    measure: MeasureKind
    source_locator: str


@dataclass(frozen=True)
class DimensionalCandidate:
    """One (node, entity, fact) triple and what became of it."""

    node_id: str
    node_kind: str
    subject_text: str
    entity: EntityReference
    node_edge: NodeEntityEdge | None
    fact_edge: EntityFactEdge | None
    accepted: bool
    rejection: RejectionReason | None
    resolution: AttributionResolution | None = None
    basis: AttributionBasis | None = None
    establishes: str = ""
    does_not_establish: str = ""


_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
#: Words that describe a member's kind rather than name it. Stripped
#: only from the end, so "Moss Landing Power Plant" keeps its name.
_KIND_WORDS = (
    "member", "axis", "segment", "generation", "power", "plant", "station",
    "facility", "facilities", "project", "projects", "system", "phase",
    "nuclear", "battery", "energy", "storage", "center", "centre",
)


def entity_display_name(member_qname: str) -> str:
    """The member's name in prose.

    `vistra:ComanchePeakNuclearPowerPlantMember` -> `Comanche Peak`.
    The trailing kind words are dropped because a filer writes the
    asset's class into the member and a person says only the name. What
    is *not* done is any similarity, stemming or edit distance: the
    result is used to look for an exact phrase, and a name this cannot
    recover simply yields no candidate."""
    local = member_qname.split(":")[-1]
    words = _CAMEL.sub(" ", local).split()
    while words and words[-1].lower() in _KIND_WORDS:
        words.pop()
    return " ".join(words)


def classify_measure(concept: str, unit: str | None = None) -> MeasureKind:
    """What kind of observation a fact is.

    Unit first for the physical kinds, because the word "capacity" in a
    concept name is shared by megawatts and credit facilities, and only
    the unit tells them apart."""
    local = concept.split(":")[-1]
    for pattern, kind in _MEASURE_PATTERNS:
        if re.search(pattern, local):
            if kind is MeasureKind.BORROWING_CAPACITY and unit and _is_physical(unit):
                break
            return kind
    if unit and _is_physical(unit):
        return MeasureKind.PHYSICAL_CAPACITY
    return MeasureKind.OTHER


def _is_physical(unit: str) -> bool:
    tail = unit.split(":")[-1].lower()
    return tail in _PHYSICAL_UNITS


#: The name must appear as a whole phrase, and must not be part of a
#: longer capitalised name. VST's filing carries a `Texas` reporting
#: segment; management says "our new gas-fired units in West Texas".
#: "Texas" is in that sentence and the sentence is not about the Texas
#: segment -- West Texas is a place inside ERCOT, the segment is a
#: reporting unit, and a rule that could not tell them apart would put
#: Permian gas spending onto a segment that does not contain it.
def _names_entity(passage: str, display_name: str) -> bool:
    """Whether this passage names this entity.

    Case-sensitive, because that is the evidence that a phrase is a
    name rather than a noun. A filer coins `CurrentAssetsMember` and
    `LandMember` alongside `ComanchePeakNuclearPowerPlantMember`; all
    three split into title-cased words, and only one of them is a
    thing. Management writes "Comanche Peak" and "our current assets",
    so requiring the capitalisation to survive tells them apart without
    a list of accounting words to exclude -- and a filer who names an
    asset in lower case simply yields no candidate, which is the safe
    direction.
    """
    if not display_name:
        return False
    pattern = re.compile(r"(?<![\w'])" + r"\s+".join(map(re.escape, display_name.split()))
                         + r"(?![\w'])")
    for match in pattern.finditer(passage):
        before = passage[: match.start()].rstrip()
        after = passage[match.end():].lstrip()
        preceded = bool(re.search(r"\b[A-Z][a-zA-Z]*$", before)) and not before.endswith((".", "!", "?"))
        followed = bool(re.match(r"[A-Z][a-zA-Z]*", after))
        if not preceded and not followed:
            return True
    return False


def node_entity_edge(
    *, node_id: str, passages: "list[tuple[str, str, str]]", entity: EntityReference
) -> NodeEntityEdge | None:
    """The first management passage that names this entity.

    `passages` is `(text, record_id, period)` from the node's own
    evidence -- never the company's whole transcript corpus. A sentence
    that names the entity while supporting a *different* node says
    nothing about this one.
    """
    for text, record_id, period in passages:
        if _names_entity(text, entity.display_name):
            return NodeEntityEdge(
                node_id=node_id, entity=entity, passage=text,
                source_record_id=record_id, source_period=period,
            )
    return None


def entity_fact_edge(
    *, entity: EntityReference, fact_key: str, concept: str, value_text: str,
    unit: str | None, period_end: str | None, source_locator: str,
) -> EntityFactEdge:
    """The filing's own tagging. Structural, and the easy edge: that the
    fact belongs to this member is what the document says, not
    something Atlas decided."""
    return EntityFactEdge(
        entity=entity, fact_key=fact_key, concept=concept, value_text=value_text,
        unit=unit, period_end=period_end, measure=classify_measure(concept, unit),
        source_locator=source_locator,
    )


#: What a node is about, and therefore which measures could bear on it.
#: Deliberately narrow: a measure not listed for a node kind is a
#: mismatch, so adding a new measure never silently widens attribution.
_MEASURES_FOR_CLAIM: dict[str, frozenset[MeasureKind]] = {
    "capacity": frozenset({MeasureKind.PHYSICAL_CAPACITY}),
    "spend": frozenset({MeasureKind.RESOURCE_DEPLOYMENT}),
    "transaction": frozenset({MeasureKind.TRANSACTION}),
}

_CAPACITY_CLAIM = re.compile(
    r"\b(?:megawatts?|MW|GW|gigawatts?|capacity|uprates?|generation)\b", re.I)
_SPEND_CLAIM = re.compile(
    r"\b(?:invest(?:ing|ment|ments)?|capital|spend(?:ing)?|allocat\w*|expenditures?|build\w*)\b", re.I)
_TRANSACTION_CLAIM = re.compile(r"\b(?:acqui\w+|purchase[ds]?|merger)\b", re.I)


def _claim_kinds(subject_text: str, passage: str) -> frozenset[MeasureKind]:
    """Which measures could speak to what this node claims.

    Read from the node's own subject and the passage that links it to
    the entity -- not from the node kind, which says whether something
    is an objective or a dependency and nothing about what it concerns."""
    text = f"{subject_text} {passage}"
    allowed: set[MeasureKind] = set()
    if _CAPACITY_CLAIM.search(text):
        allowed |= _MEASURES_FOR_CLAIM["capacity"]
    if _SPEND_CLAIM.search(text):
        allowed |= _MEASURES_FOR_CLAIM["spend"]
    if _TRANSACTION_CLAIM.search(text):
        allowed |= _MEASURES_FOR_CLAIM["transaction"]
    return frozenset(allowed)


def compose(
    *, node_id: str, node_kind: str, subject_text: str, entity: EntityReference,
    node_edge: NodeEntityEdge | None, fact_edge: EntityFactEdge | None,
    entity_is_ambiguous: bool = False,
) -> DimensionalCandidate:
    """Both edges, or a reason.

    The order of the checks is the order of the claims: an entity Atlas
    cannot resolve, then a missing edge, then whether the fact measures
    anything the node is about. Nothing is accepted on two of three."""
    base = dict(node_id=node_id, node_kind=node_kind, subject_text=subject_text,
                entity=entity, node_edge=node_edge, fact_edge=fact_edge)

    def reject(reason: RejectionReason) -> DimensionalCandidate:
        return DimensionalCandidate(**base, accepted=False, rejection=reason)

    if entity_is_ambiguous:
        return reject(RejectionReason.AMBIGUOUS_ENTITY)
    if node_edge is None:
        return reject(RejectionReason.NO_NODE_ENTITY_LINK)
    if fact_edge is None:
        return reject(RejectionReason.NO_ENTITY_FACT_LINK)

    measure = fact_edge.measure
    # A withdrawal of capability can never evidence an initiative that
    # builds one, and a write-down never evidences progress. These are
    # rejected before the claim check so the reason names the real
    # problem rather than "mismatch".
    if measure in (MeasureKind.CAPACITY_RETIREMENT, MeasureKind.IMPAIRMENT):
        return reject(RejectionReason.CONTRARY_EVIDENCE)
    allowed = _claim_kinds(subject_text, node_edge.passage)
    if not allowed or measure not in allowed:
        return reject(RejectionReason.MEASURE_MISMATCH)
    # A megawatt figure at one date is the plant's size, not something
    # the strategy added. Accepting it as a level is honest; calling it
    # a change is not, and this layer never compares two of them.
    if measure is MeasureKind.PHYSICAL_CAPACITY:
        establishes = (f"a capacity of {fact_edge.value_text} {fact_edge.unit or ''} was reported "
                       f"at {entity.display_name} as at {fact_edge.period_end}")
        does_not = ("that this capacity was added by the initiative, that it changed, "
                    "or that the initiative caused any part of it")
        resolution = AttributionResolution.CAPACITY_ASSET
    else:
        establishes = (f"{fact_edge.concept.split(':')[-1]} of {fact_edge.value_text} was reported "
                       f"against {entity.display_name} for the period ending {fact_edge.period_end}")
        does_not = ("that the initiative caused it, that it was material, "
                    "or that the initiative succeeded")
        resolution = AttributionResolution.PROJECT
    return DimensionalCandidate(
        **base, accepted=True, rejection=None, resolution=resolution,
        basis=AttributionBasis.DERIVED_STRUCTURAL,
        establishes=establishes,
        does_not_establish=does_not
        + "; the link from the strategy to this entity is management's own statement, not independent",
    )


def dimensional_candidates(
    nodes: "list[tuple[str, str, str, list[tuple[str, str, str]]]]",
    facts: "list[object]",
) -> tuple[DimensionalCandidate, ...]:
    """Every (node, entity, fact) triple, accepted or rejected.

    `nodes` is `(node_id, kind, subject_text, passages)`; `facts` is
    whatever the dimensional store returns, read only through the
    attributes of the shared contract. Nothing here knows which
    provider filed them.

    Candidates are generated from the *entities the filings name*, then
    tested against the node's own passages. Generating from the strategy
    side instead would need Atlas to guess what a sentence refers to;
    generating from the filing side means every candidate starts from a
    name a filer actually used.
    """
    # One fact per semantic key. The store already collapses a report
    # that files a figure twice; a caller that hands the same fact over
    # twice must not turn one observation into two.
    seen_keys: set[str] = set()
    deduped = []
    for fact in facts:
        key = getattr(fact, "fact_key", None)
        if key is not None:
            if key in seen_keys:
                continue
            seen_keys.add(key)
        deduped.append(fact)
    facts = deduped

    entities: dict[str, EntityReference] = {}
    display_counts: dict[str, set[str]] = {}
    for fact in facts:
        for dimension in getattr(fact, "dimensions", ()) or ():
            member = dimension.member_qname
            if member in entities:
                continue
            display = entity_display_name(member)
            if not display:
                continue
            entities[member] = EntityReference(
                member_qname=member, axis_qname=dimension.axis_qname,
                display_name=display, source_locator=fact.source_locator,
            )
            display_counts.setdefault(display.lower(), set()).add(member)

    out: list[DimensionalCandidate] = []
    for node_id, kind, subject_text, passages in nodes:
        for member, entity in entities.items():
            edge = node_entity_edge(node_id=node_id, passages=passages, entity=entity)
            if edge is None:
                continue          # no candidate at all: the strategy never names it
            ambiguous = len(display_counts[entity.display_name.lower()]) > 1
            tagged = [f for f in facts
                      if any(d.member_qname == member for d in (getattr(f, "dimensions", ()) or ()))]
            if not tagged:
                out.append(compose(node_id=node_id, node_kind=kind, subject_text=subject_text,
                                   entity=entity, node_edge=edge, fact_edge=None,
                                   entity_is_ambiguous=ambiguous))
                continue
            for fact in tagged:
                fact_edge = entity_fact_edge(
                    entity=entity, fact_key=fact.fact_key, concept=fact.concept,
                    value_text=fact.value_text, unit=fact.unit,
                    period_end=fact.period_end, source_locator=fact.source_locator)
                out.append(compose(node_id=node_id, node_kind=kind, subject_text=subject_text,
                                   entity=entity, node_edge=edge, fact_edge=fact_edge,
                                   entity_is_ambiguous=ambiguous))
    return tuple(out)

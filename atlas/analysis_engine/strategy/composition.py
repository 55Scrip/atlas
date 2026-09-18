"""Putting readings together -- and being explicit that the result is no
longer a reading.

Everything in this module is DERIVED or HYPOTHESIS, never OBSERVED. A
company saying the same thing in four consecutive quarters is four
observations of one assertion, and the judgement that they *are* one
assertion is Atlas's, not management's. Same for an economic engine
assembled out of an initiative and an outcome, and same -- most of all
-- for two companies meeting at a canonical factor.

**Repetition is not corroboration.** Management repeats strategy
language every quarter by design; it is how a strategy is communicated.
Counting the repetitions as independent evidence would make the
best-rehearsed strategy look like the best-evidenced one. So a repeated
assertion adds a period to `observed_periods` and nothing else: one
node, several observations, and a continuity state that says which.
"""
from __future__ import annotations

from datetime import datetime

from atlas.analysis_engine.strategy.contracts import (
    ContinuityState,
    EvidenceStatus,
    FactorClass,
    RelationKind,
    StrategyNodeKind,
)
from atlas.analysis_engine.strategy.extraction import EXTRACTOR_VERSION, extract_strategy
from atlas.analysis_engine.strategy.models import (
    CompanyStrategy,
    CrossCompanyAdjacency,
    RejectedStrategyCandidate,
    StrategyEdge,
    StrategyEvidence,
    StrategyNode,
)

__all__ = [
    "compose_company_strategy",
    "find_cross_company_adjacencies",
    "ENGINE_RULE",
    "PURSUIT_RULE",
    "THREAT_RULE",
]

#: Named derivation rules. A DERIVED node without one cannot be built
#: (`StrategyNode.__post_init__`), so these strings are the complete
#: list of ways Atlas is allowed to conclude something nobody said.
SUCCESS_RULE = "success-condition-from-observed-dependency"
FAILURE_RULE = "failure-mode-from-observed-dependency"
PURSUIT_RULE = "objective-and-initiative-share-a-factor"
THREAT_RULE = "dependency-and-failure-mode-share-a-factor"


def _period_key(period: str | None) -> tuple[int, int]:
    """Orders "2026Q2" after "2025Q4". A period Atlas cannot parse sorts
    first, so an unlabelled statement never wins a recency contest."""
    if not period or "Q" not in period:
        return (0, 0)
    year, _, quarter = period.partition("Q")
    try:
        return (int(year), int(quarter))
    except ValueError:
        return (0, 0)


def _identity(node: StrategyNode) -> tuple:
    """What makes two extracted nodes the same assertion.

    Deliberately coarse -- kind plus canonical subject -- because the
    surface wording changes every quarter while the assertion does not.
    Deliberately not the sentence, because then every restatement would
    be a new strategy."""
    return (node.company, node.kind, node.factor, node.resource, node.outcome)


def _merge(group: list[StrategyNode]) -> StrategyNode:
    """One node per assertion, carrying every observation of it.

    The earliest observation supplies the node's identity and its
    `subject_text`: a strategy is dated from when it was first stated,
    not from the last time it was mentioned."""
    ordered = sorted(group, key=lambda n: (_period_key(n.observed_periods[0] if n.observed_periods else None), n.node_id))
    first = ordered[0]
    periods: list[str] = []
    for node in ordered:
        for period in node.observed_periods:
            if period not in periods:
                periods.append(period)
    periods.sort(key=_period_key)
    evidence: list[StrategyEvidence] = []
    seen: set[tuple[str, str]] = set()
    for node in ordered:
        for item in node.evidence:
            key = (item.source_record_id, item.source_text)
            if key in seen:
                continue
            seen.add(key)
            evidence.append(item)

    if len(periods) <= 1:
        continuity = ContinuityState.NEW
    elif len({n.subject_text for n in ordered}) > 1:
        # Same canonical subject, different words for it across periods.
        # Not a new strategy and not simply a restatement either.
        continuity = ContinuityState.MODIFIED
    else:
        continuity = ContinuityState.CONTINUING

    return StrategyNode(
        node_id=first.node_id,
        company=first.company,
        kind=first.kind,
        status=first.status,
        factor=first.factor,
        resource=first.resource,
        outcome=first.outcome,
        subject_text=first.subject_text,
        evidence=tuple(evidence),
        observed_periods=tuple(periods),
        continuity=continuity,
    )


def _derived_edges(nodes: tuple[StrategyNode, ...]) -> tuple[StrategyEdge, ...]:
    """Relations nobody stated, that follow from two that were.

    Both rules join on the canonical factor, which is the only join
    Atlas can defend: an objective about production capacity and an
    initiative building production capacity are about the same thing in
    Atlas's vocabulary, whether or not one sentence ever named both."""
    by_kind: dict[StrategyNodeKind, list[StrategyNode]] = {}
    for node in nodes:
        by_kind.setdefault(node.kind, []).append(node)

    edges: list[StrategyEdge] = []
    for objective in by_kind.get(StrategyNodeKind.OBJECTIVE, []):
        if objective.factor is None:
            continue
        for initiative in by_kind.get(StrategyNodeKind.INITIATIVE, []):
            if initiative.factor is objective.factor:
                edges.append(
                    StrategyEdge(
                        source_id=objective.node_id,
                        target_id=initiative.node_id,
                        relation=RelationKind.PURSUED_BY,
                        status=EvidenceStatus.DERIVED,
                        derivation_rule=PURSUIT_RULE,
                    )
                )
    for dependency in by_kind.get(StrategyNodeKind.DEPENDENCY, []):
        for failure in by_kind.get(StrategyNodeKind.FAILURE_MODE, []):
            if failure.factor is dependency.factor:
                edges.append(
                    StrategyEdge(
                        source_id=dependency.node_id,
                        target_id=failure.node_id,
                        relation=RelationKind.THREATENED_BY,
                        status=EvidenceStatus.DERIVED,
                        derivation_rule=THREAT_RULE,
                    )
                )
    return tuple(edges)


def _conditions_and_failures(nodes: tuple[StrategyNode, ...]) -> tuple[StrategyNode, ...]:
    """Success conditions and failure modes, derived from dependencies
    the company actually stated.

    Both were zero across four benchmarks, and the audit found why: the
    corpus almost never contains an explicit conditional. Management
    says "our build depends on the availability of components"; it does
    not go on to say "therefore the availability of components is a
    condition of success, and its absence is a failure mode". Those two
    sentences are *direct transformations* of the first -- they add no
    proposition, only a change of voice.

    So Atlas may derive them, and only them:

        observed:  X depends on factor Y
        derived:   availability of Y is a condition for X
        derived:   insufficient Y can prevent or delay X

    Nothing else is generated. There is no rule that invents a second
    condition, no rule that reads a risk factor, and both outputs are
    DERIVED with their rule attached -- because a transformation of
    evidence is not evidence, however direct it is."""
    derived: list[StrategyNode] = []
    for dependency in nodes:
        if dependency.kind is not StrategyNodeKind.DEPENDENCY or dependency.factor is None:
            continue
        for kind, rule in (
            (StrategyNodeKind.SUCCESS_CONDITION, SUCCESS_RULE),
            (StrategyNodeKind.FAILURE_MODE, FAILURE_RULE),
        ):
            derived.append(
                StrategyNode(
                    node_id=f"{kind.value}:{dependency.node_id}",
                    company=dependency.company,
                    kind=kind,
                    status=EvidenceStatus.DERIVED,
                    factor=dependency.factor,
                    # Phrased as a statement about the factor, not as a
                    # prefix glued onto whatever words resolved it.
                    # "availability of in the UAE" was the first
                    # version's output and it is not a sentence.
                    subject_text=(
                        f"{dependency.subject_text} is available"
                        if kind is StrategyNodeKind.SUCCESS_CONDITION
                        else f"{dependency.subject_text} is insufficient or delayed"
                    ),
                    evidence=dependency.evidence,
                    observed_periods=dependency.observed_periods,
                    derivation_rule=rule,
                    derived_from=(dependency.node_id,),
                )
            )
    return tuple(derived)


def compose_company_strategy(records, *, composed_at: datetime) -> CompanyStrategy:
    """The whole read model for one company, from records Atlas already
    has. Deterministic: same records in, same graph out, with no clock
    read except the one the caller passes."""
    records = list(records)
    company = records[0].company if records else ""

    raw_nodes: list[StrategyNode] = []
    observed_edges: list[StrategyEdge] = []
    rejected: list[RejectedStrategyCandidate] = []
    for record in records:
        nodes, edges, rejects = extract_strategy(record, extracted_at=composed_at)
        raw_nodes.extend(nodes)
        observed_edges.extend(edges)
        rejected.extend(rejects)

    grouped: dict[tuple, list[StrategyNode]] = {}
    for node in raw_nodes:
        grouped.setdefault(_identity(node), []).append(node)
    merged = tuple(_merge(group) for group in grouped.values())
    merged = tuple(sorted(merged, key=lambda n: (n.kind.value, n.subject_text, n.node_id)))

    # An observed edge whose endpoints were merged away must be repointed
    # at the surviving node, or the graph would carry dangling ids.
    survivor: dict[str, str] = {}
    for group_key, group in grouped.items():
        kept = next(n for n in merged if _identity(n) == group_key)
        for node in group:
            survivor[node.node_id] = kept.node_id
    repointed: list[StrategyEdge] = []
    seen_edges: set[tuple[str, str, RelationKind]] = set()
    for edge in observed_edges:
        source = survivor.get(edge.source_id, edge.source_id)
        target = survivor.get(edge.target_id, edge.target_id)
        key = (source, target, edge.relation)
        if key in seen_edges:
            continue
        seen_edges.add(key)
        repointed.append(
            StrategyEdge(
                source_id=source,
                target_id=target,
                relation=edge.relation,
                status=edge.status,
                evidence=edge.evidence,
            )
        )

    nodes = merged + _conditions_and_failures(merged)

    derived = [e for e in _derived_edges(nodes) if (e.source_id, e.target_id, e.relation) not in seen_edges]
    edges = tuple(repointed) + tuple(derived)

    present = {n.kind for n in nodes}
    unknowns = tuple(
        kind.value for kind in StrategyNodeKind if kind not in present
    )

    return CompanyStrategy(
        company=company,
        nodes=nodes,
        edges=tuple(sorted(edges, key=lambda e: (e.relation.value, e.source_id, e.target_id))),
        rejected=tuple(rejected),
        unknowns=unknowns,
        extractor_version=EXTRACTOR_VERSION,
        composed_at=composed_at,
    )


def find_cross_company_adjacencies(
    strategies: list[CompanyStrategy],
) -> tuple[CrossCompanyAdjacency, ...]:
    """Companies that meet at a canonical factor -- one needing it, the
    other producing it.

    **The output is a question, not a finding.** Every adjacency is a
    HYPOTHESIS by construction, and `CrossCompanyAdjacency` carries its
    own list of things it does not license anyone to conclude. Nothing
    here creates a beneficiary edge, and there is no code path that
    could: `RelationKind` has no member for it, and the building side is
    not modelled as supply."""
    requires: dict[FactorClass, list[tuple[str, str]]] = {}
    builds: dict[FactorClass, list[tuple[str, str]]] = {}
    for strategy in strategies:
        for participation in strategy.factor_participation:
            for node_id in participation.requires:
                requires.setdefault(participation.factor, []).append((strategy.company, node_id))
            for node_id in participation.builds:
                builds.setdefault(participation.factor, []).append((strategy.company, node_id))

    found: list[CrossCompanyAdjacency] = []
    for factor in sorted(set(requires) & set(builds), key=lambda f: f.value):
        for requiring_company, requiring_node in sorted(requires[factor]):
            for building_company, building_node in sorted(builds[factor]):
                if requiring_company == building_company:
                    continue  # a company is not adjacent to itself
                found.append(
                    CrossCompanyAdjacency(
                        factor=factor,
                        requiring_company=requiring_company,
                        building_company=building_company,
                        requiring_node_id=requiring_node,
                        building_node_id=building_node,
                    )
                )
    return tuple(found)

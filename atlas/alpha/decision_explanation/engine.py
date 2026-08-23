"""Decision Explanation & Traceability engine (Atlas Decision Layer
Sprint 6). Pure, deterministic functions only -- no I/O, matching
every sibling Decision Layer engine in this program.

**Computes nothing new.** Every function below reclassifies and
deduplicates fields already present on `InvestmentDecision`,
`RecommendationConviction`, `DecisionReadiness`, `DecisionPath`, and
the Case's own `EvidenceGraph`/`WeakDependency` list -- never a new
judgment about any individual Case. See this package's own
`__init__.py` for the full audit these functions are built from.

**Deduplication discipline.** The same real fact (a `DecisionBlockerKind`
code, say) is frequently named by more than one upstream layer at once
-- Investment Decision's own `blockers` already includes every present
Decision Readiness blocker verbatim, and Recommendation Conviction's
own `limiting_reasons` very often names the identical code again. A
naive concatenation would count that one real fact multiple times.
`_merge` below collapses same-`(kind, id)` references into one entry,
keeping every layer that named it in `named_by`, in this module's own
fixed `_LAYER_ORDER` (Deliverable 5: highest-importance-first,
Investment Decision's own synthesis outranks every layer it was built
from)."""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.decision_memory.models import ChangeDirection
from atlas.alpha.decision_path.models import DecisionPath
from atlas.alpha.decision_readiness.models import DecisionReadiness
from atlas.alpha.evidence_graph.models import GraphNode, WeakDependency
from atlas.alpha.investment_decision.models import DecisionReason, DecisionReasonSource, InvestmentDecision
from atlas.alpha.recommendation_conviction.models import (
    ConvictionReason,
    ConvictionReasonSource,
    ConvictionStrength,
    RecommendationConviction,
)

from .models import (
    BlockingFinding,
    DecisionExplanation,
    DecisionExplanationChange,
    DecisionExplanationComparison,
    DecisionExplanationSummary,
    ExplanationChain,
    ExplanationLayer,
    ExplanationReference,
    ExplanationReferenceKind,
    ExplanationSection,
    ExplanationSectionKind,
    PortfolioDecisionExplanationBreakdown,
    SupportingFinding,
)

__all__ = [
    "build_decision_explanation",
    "summarize_decision_explanation",
    "compare_decision_explanations",
    "detect_decision_explanation_change",
    "build_portfolio_decision_explanation_breakdown",
]

#: Deliverable 5 -- the fixed order later layers are folded in. A fact
#: already named by an earlier layer keeps its original position; only
#: a genuinely new fact (named by no earlier layer) is appended here.
_LAYER_ORDER: tuple[ExplanationLayer, ...] = (
    ExplanationLayer.INVESTMENT_DECISION,
    ExplanationLayer.RECOMMENDATION_CONVICTION,
    ExplanationLayer.DECISION_READINESS,
    ExplanationLayer.EVIDENCE_GRAPH,
)

#: Duplicated locally from `atlas.alpha.decision_memory.engine`'s own
#: private `_STRENGTH_RANK` -- that name is module-private by design
#: (each package owns its own rank table, the same "no shared mutable
#: ordering module" discipline every Decision Layer sprint has
#: followed since Sprint 5's own `_direction` docstring). Higher rank
#: is stronger, matching `ConvictionStrength`'s own declared order.
_STRENGTH_RANK: dict[ConvictionStrength, int] = {
    ConvictionStrength.UNAVAILABLE: 0,
    ConvictionStrength.VERY_WEAK: 1,
    ConvictionStrength.WEAK: 2,
    ConvictionStrength.MODERATE: 3,
    ConvictionStrength.STRONG: 4,
    ConvictionStrength.VERY_STRONG: 5,
}


def _reason_ref(code: str) -> ExplanationReference:
    return ExplanationReference(kind=ExplanationReferenceKind.REASON_CODE, id=code)


def _merge_supporting(
    by_layer: dict[ExplanationLayer, tuple[DecisionReason | ConvictionReason, ...]],
) -> tuple[SupportingFinding, ...]:
    """First-seen order across `_LAYER_ORDER`, `named_by` collecting
    every layer that named the identical code."""
    order: list[str] = []
    named_by: dict[str, list[ExplanationLayer]] = {}
    for layer in _LAYER_ORDER:
        for reason in by_layer.get(layer, ()):
            code = reason.code
            if code not in named_by:
                order.append(code)
                named_by[code] = []
            named_by[code].append(layer)
    return tuple(SupportingFinding(reference=_reason_ref(code), named_by=tuple(named_by[code])) for code in order)


def _merge_blocking(
    by_layer: dict[ExplanationLayer, tuple[DecisionReason | ConvictionReason, ...]],
    change_trigger_codes: frozenset[str],
) -> tuple[BlockingFinding, ...]:
    order: list[str] = []
    named_by: dict[str, list[ExplanationLayer]] = {}
    for layer in _LAYER_ORDER:
        for reason in by_layer.get(layer, ()):
            code = reason.code
            if code not in named_by:
                order.append(code)
                named_by[code] = []
            named_by[code].append(layer)
    return tuple(
        BlockingFinding(
            reference=_reason_ref(code),
            named_by=tuple(named_by[code]),
            is_change_trigger=code in change_trigger_codes,
        )
        for code in order
    )


def _evidence_graph_findings(
    weak_dependency_kinds: frozenset[str], weak_dependencies: tuple[WeakDependency, ...], finding_nodes: tuple[GraphNode, ...]
) -> tuple[str, ...]:
    """Deliverable 4's own traceability win: `RecommendationConviction
    .limiting_reasons` already deduplicates an Evidence Graph weakness
    down to its bare `WeaknessKind` code (e.g. `"no_support"`), losing
    which specific Finding it was about. This resolves that same code
    back to every real `FINDING` node it actually applies to, using
    the Case's own already-computed `WeakDependency` list -- never a
    new weakness computation, a pure re-join against real node ids."""
    finding_ids = {n.id for n in finding_nodes}
    matched = sorted(
        {w.node_id for w in weak_dependencies if w.kind.value in weak_dependency_kinds and w.node_id in finding_ids}
    )
    return tuple(matched)


def build_decision_explanation(
    case_id: str,
    *,
    decision: InvestmentDecision,
    conviction: RecommendationConviction,
    readiness: DecisionReadiness,
    path: DecisionPath,
    latest_snapshot_hash: str | None,
    weak_dependencies: tuple[WeakDependency, ...],
    finding_nodes: tuple[GraphNode, ...],
    generated_at: datetime,
) -> DecisionExplanation:
    """Deliverable 3 -- one coherent explanation, a pure function of
    five already-computed inputs. Never summarizes differently
    depending on wording: the same five inputs always produce the
    identical `DecisionExplanation`."""
    change_trigger_codes = frozenset(
        {r.code for r in (decision.change_trigger,) if r is not None}
        | {r.code for r in (conviction.strengthening_trigger,) if r is not None}
    )

    supporting_by_layer: dict[ExplanationLayer, tuple] = {
        ExplanationLayer.INVESTMENT_DECISION: tuple(
            r for r in decision.supporting_reasons if r.source is not DecisionReasonSource.READINESS_BLOCKER
        ),
        ExplanationLayer.RECOMMENDATION_CONVICTION: tuple(
            r for r in conviction.supporting_reasons if r.source is not ConvictionReasonSource.READINESS_BLOCKER
        ),
        ExplanationLayer.DECISION_READINESS: tuple(
            DecisionReason(DecisionReasonSource.READINESS_SUPPORT, r.kind.value) for r in readiness.supporting_reasons
        ),
    }
    supporting = _merge_supporting(supporting_by_layer)

    blocking_by_layer: dict[ExplanationLayer, tuple] = {
        ExplanationLayer.INVESTMENT_DECISION: tuple(decision.blockers),
        ExplanationLayer.RECOMMENDATION_CONVICTION: tuple(conviction.limiting_reasons),
        ExplanationLayer.DECISION_READINESS: tuple(
            DecisionReason(DecisionReasonSource.READINESS_BLOCKER, b.kind.value) for b in readiness.blockers
        ),
    }
    blocking = list(_merge_blocking(blocking_by_layer, change_trigger_codes))

    weak_dependency_kinds = frozenset(
        r.code for r in conviction.limiting_reasons if r.source is ConvictionReasonSource.EVIDENCE_GRAPH
    )
    resolved_finding_ids = _evidence_graph_findings(weak_dependency_kinds, weak_dependencies, finding_nodes)
    already_referenced = {bf.reference.id for bf in blocking}
    for finding_id in resolved_finding_ids:
        if finding_id in already_referenced:
            continue
        blocking.append(
            BlockingFinding(
                reference=ExplanationReference(kind=ExplanationReferenceKind.FINDING, id=finding_id),
                named_by=(ExplanationLayer.EVIDENCE_GRAPH,),
                is_change_trigger=False,
            )
        )

    dependency_steps = tuple(_reason_ref(step.dependency.code) for step in path.steps)

    historical_reference = (
        ExplanationReference(kind=ExplanationReferenceKind.DECISION_SNAPSHOT, id=latest_snapshot_hash)
        if latest_snapshot_hash is not None
        else None
    )

    order = (
        ExplanationSection(ExplanationSectionKind.SUPPORTING, len(supporting)),
        ExplanationSection(ExplanationSectionKind.BLOCKING, len(blocking)),
        ExplanationSection(ExplanationSectionKind.DEPENDENCY, len(dependency_steps)),
        ExplanationSection(ExplanationSectionKind.HISTORICAL, 1 if historical_reference is not None else 0),
    )

    chain = ExplanationChain(
        case_id=case_id,
        order=order,
        supporting=supporting,
        blocking=tuple(blocking),
        dependency_steps=dependency_steps,
        historical_reference=historical_reference,
    )

    return DecisionExplanation(
        case_id=case_id,
        action=decision.action,
        conviction_strength=conviction.strength,
        chain=chain,
        primary_supporting=supporting[0] if supporting else None,
        primary_blocking=blocking[0] if blocking else None,
        generated_at=generated_at,
    )


def summarize_decision_explanation(explanation: DecisionExplanation) -> DecisionExplanationSummary:
    return DecisionExplanationSummary(
        case_id=explanation.case_id,
        action=explanation.action,
        primary_supporting=explanation.primary_supporting,
        primary_blocking=explanation.primary_blocking,
        generated_at=explanation.generated_at,
    )


def compare_decision_explanations(a: DecisionExplanation, b: DecisionExplanation) -> DecisionExplanationComparison:
    """Deliverable 9 -- shared supporting findings, each side's own
    differing blockers, shared dependencies. Never a winner. Every
    result keeps its own `ExplanationReference` (never a bare id
    string) so a renderer can resolve it through the same closed
    vocabularies every other reference in this package already uses --
    a `FINDING`-kind reference here must never render as an anonymous
    raw id."""
    a_supporting_by_id = {sf.reference.id: sf.reference for sf in a.chain.supporting}
    b_supporting_by_id = {sf.reference.id: sf.reference for sf in b.chain.supporting}
    shared_supporting = tuple(
        a_supporting_by_id[i] for i in sorted(set(a_supporting_by_id) & set(b_supporting_by_id))
    )

    a_blocking_by_id = {bf.reference.id: bf.reference for bf in a.chain.blocking}
    b_blocking_by_id = {bf.reference.id: bf.reference for bf in b.chain.blocking}
    differing_a = tuple(a_blocking_by_id[i] for i in sorted(set(a_blocking_by_id) - set(b_blocking_by_id)))
    differing_b = tuple(b_blocking_by_id[i] for i in sorted(set(b_blocking_by_id) - set(a_blocking_by_id)))

    a_dependency_by_id = {r.id: r for r in a.chain.dependency_steps}
    b_dependency_by_id = {r.id: r for r in b.chain.dependency_steps}
    shared_dependencies = tuple(
        a_dependency_by_id[i] for i in sorted(set(a_dependency_by_id) & set(b_dependency_by_id))
    )

    return DecisionExplanationComparison(
        a=a,
        b=b,
        shared_supporting=shared_supporting,
        differing_blocking_a=differing_a,
        differing_blocking_b=differing_b,
        shared_dependencies=shared_dependencies,
    )


def detect_decision_explanation_change(
    previous: DecisionExplanation | None, current: DecisionExplanation, *, detected_at: datetime
) -> DecisionExplanationChange | None:
    """"No event, no timestamp" -- `None` on the first-ever computation
    or when nothing about the explanation actually moved. Identity for
    a reference across the two snapshots is its own `(kind, id)`."""
    if previous is None:
        return None

    previous_supporting = {sf.reference.id: sf for sf in previous.chain.supporting}
    current_supporting = {sf.reference.id: sf for sf in current.chain.supporting}
    new_supporting = tuple(current_supporting[i] for i in current_supporting if i not in previous_supporting)

    previous_blocking = {bf.reference.id: bf for bf in previous.chain.blocking}
    current_blocking = {bf.reference.id: bf for bf in current.chain.blocking}
    resolved_blocking = tuple(previous_blocking[i] for i in previous_blocking if i not in current_blocking)
    new_blocking = tuple(current_blocking[i] for i in current_blocking if i not in previous_blocking)

    evidence_expanded = len(current.chain.supporting) > len(previous.chain.supporting)

    conviction_direction: ChangeDirection | None = None
    if previous.conviction_strength != current.conviction_strength:
        previous_rank = _STRENGTH_RANK[previous.conviction_strength]
        current_rank = _STRENGTH_RANK[current.conviction_strength]
        conviction_direction = ChangeDirection.STRONGER if current_rank > previous_rank else ChangeDirection.WEAKER

    if not new_supporting and not resolved_blocking and not new_blocking and conviction_direction is None:
        return None

    return DecisionExplanationChange(
        case_id=current.case_id,
        new_supporting=new_supporting,
        resolved_blocking=resolved_blocking,
        new_blocking=new_blocking,
        evidence_expanded=evidence_expanded,
        conviction_direction=conviction_direction,
        detected_at=detected_at,
    )


def build_portfolio_decision_explanation_breakdown(
    items: tuple[tuple[str, DecisionExplanationChange | None], ...],
) -> PortfolioDecisionExplanationBreakdown:
    """Deliverable 7 -- ticker groupings only, in the caller's own
    existing order; never re-ranked."""
    recently_changed = tuple(ticker for ticker, change in items if change is not None)
    new_supporting_findings = tuple(
        ticker for ticker, change in items if change is not None and change.new_supporting
    )
    resolved_blockers = tuple(ticker for ticker, change in items if change is not None and change.resolved_blocking)
    recently_strengthened = tuple(
        ticker for ticker, change in items if change is not None and change.conviction_direction is ChangeDirection.STRONGER
    )
    return PortfolioDecisionExplanationBreakdown(
        recently_changed=recently_changed,
        new_supporting_findings=new_supporting_findings,
        resolved_blockers=resolved_blockers,
        recently_strengthened=recently_strengthened,
    )

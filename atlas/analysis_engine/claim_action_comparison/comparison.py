"""Compare one StrategyClaim with one ActionEvidence record.

The comparator consumes both committed read models and modifies neither. It
answers one question -- is this observed action capable of bearing on this
claim? -- and refuses by name when it cannot tell. Same issuer is never
enough, a shared place is never enough, a shared unit is never enough, and a
shared year is never enough.
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Sequence

from atlas.analysis_engine.action_evidence import ActionEvidence, ActionType, QuantityKind
from atlas.analysis_engine.claim_action_comparison.contracts import (
    ActionRef, ClaimActionComparison, ClaimRef, Compatibility, EntityBasis, Relation,
    TemporalRelation,
)
from atlas.analysis_engine.strategy_claim import EventKind, MeasureKind, StrategyClaim

__all__ = ["compare", "compare_many"]

#: Which observed act can evidence which claimed event. Earned from the frozen
#: corpus, and deliberately incomplete: nothing a filing asserts says
#: "construction started", "a facility was established" or "shares were
#: repurchased", so claims resting on those events have no action vocabulary
#: to match and are refused rather than approximated.
_EVENT_FROM_TYPE: dict[EventKind, frozenset[ActionType]] = {
    EventKind.CONTRACT_ENTERED: frozenset({ActionType.CONTRACT_ENTERED}),
    EventKind.COMPLETION: frozenset({ActionType.COMPLETION}),
}
#: A capital-deployment claim is evidenced by an action that says capital was
#: deployed -- in the action's own object, not merely by its type. An
#: acquisition is capital leaving the company, but the filing has to call it
#: capital allocation for it to bear on a claim about allocating capital.
_CAPITAL_OBJECT = re.compile(r"\b(?:capital allocation|capital expenditures?|capex|"
                             r"allocation of capital|investments? in)\b", re.I)
#: A state of affairs is not an act. "Waymo is now providing paid rides"
#: cannot be compared with a claim about what a company will do.
_NOT_AN_ACT = frozenset({ActionType.ONGOING_ACTIVITY})

_MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], start=1)}
_PERIOD = re.compile(r"(?P<y>\d{4})\s*Q(?P<q>[1-4])", re.I)
_STOP = frozenset({"the", "a", "an", "of", "our", "its", "their", "and", "or", "for", "to",
                   "with", "by", "on", "in", "at", "from", "that", "this", "these", "those",
                   "any", "all", "is", "are", "be", "been", "as", "terms"})


def _word_in(token: str, text: str) -> bool:
    """Whole-word containment, tolerating a plural on either side."""
    stem = re.escape(token.rstrip("s"))
    return re.search(rf"(?<![A-Za-z]){stem}s?(?![A-Za-z])", text, re.I) is not None


def _entity(claim: StrategyClaim, surfaces: Sequence[str],
            action: ActionEvidence) -> tuple[Compatibility, EntityBasis, tuple[str, ...]]:
    """Where the claim's own named things appear in the action, if anywhere.

    Only surfaces the sources preserved are used: the claim's entity mentions
    and the capitalised names inside its object. No alias table, no fuzzy
    matching, no identity resolution -- if nothing matches, the comparison
    refuses rather than guessing.
    """
    named = {s for s in surfaces if s}
    named |= set(re.findall(r"\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*", claim.object_text or ""))
    named = {n for n in named if n.lower() not in _STOP and len(n) > 2}
    if not named:
        return Compatibility.UNKNOWN, EntityBasis.NONE, ()
    asserted = f"{action.object_text or ''} {action.counterparty_text or ''}"
    role = tuple(sorted(n for n in named if _word_in(n, asserted)))
    if role:
        return Compatibility.MATCH, EntityBasis.ASSERTED_ROLE, role
    span = tuple(sorted(n for n in named if _word_in(n, action.sentence)))
    if span:
        return Compatibility.MATCH, EntityBasis.SOURCE_SPAN, span
    return Compatibility.MISMATCH, EntityBasis.ISSUER_ONLY, ()


def _event(claim: StrategyClaim, action: ActionEvidence) -> Compatibility:
    if not claim.event_kinds:
        return Compatibility.NOT_APPLICABLE
    for kind in claim.event_kinds:
        if action.action_type in _EVENT_FROM_TYPE.get(kind, frozenset()):
            return Compatibility.MATCH
        if kind is EventKind.CAPITAL_DEPLOYED and _CAPITAL_OBJECT.search(action.object_text or ""):
            return Compatibility.MATCH
    return Compatibility.MISMATCH


def _measure(claim: StrategyClaim, action: ActionEvidence) -> Compatibility:
    """Recorded, never decisive.

    Measure agreement cannot license relevance (a shared unit is not
    aboutness) and measure disagreement cannot refuse it: the corpus's one
    true capital-deployment pair reports its scale in megawatts, so gating on
    the measure would throw the true pair away.
    """
    if not claim.measure_kinds:
        return Compatibility.NOT_APPLICABLE
    if not action.quantities:
        return Compatibility.UNKNOWN
    kinds = {q.kind for q in action.quantities}
    wanted = set()
    for m in claim.measure_kinds:
        if m in (MeasureKind.CAPITAL_DEPLOYMENT, MeasureKind.CAPITAL_RETURNED):
            wanted.add(QuantityKind.MONETARY)
        elif m is MeasureKind.CAPACITY:
            wanted.add(QuantityKind.CAPACITY)
    return Compatibility.MATCH if kinds & wanted else Compatibility.MISMATCH


def _action_ym(action: ActionEvidence) -> tuple[int, int] | None:
    """The action's own stated date, never today's. No year, no answer."""
    if action.date is None:
        return None
    raw = action.date.raw_text
    year = re.search(r"\b(19|20)\d{2}\b", raw)
    if not year:
        return None
    month = next((v for k, v in _MONTHS.items() if re.search(rf"\b{k}\b", raw, re.I)), None)
    return int(year.group(0)), month or 0


def _temporal(claim: StrategyClaim, action: ActionEvidence) -> tuple[Compatibility, TemporalRelation]:
    ym = _action_ym(action)
    p = _PERIOD.search(claim.provenance.source_period or "")
    if ym is None or p is None:
        return Compatibility.UNKNOWN, TemporalRelation.UNKNOWN
    y, m = ym
    py, pq = int(p.group("y")), int(p.group("q"))
    start, end = (pq - 1) * 3 + 1, pq * 3
    if y > py or (y == py and m > end):
        return Compatibility.MATCH, TemporalRelation.ACTION_AFTER_CLAIM
    if y == py and (m == 0 or start <= m <= end):
        return Compatibility.MATCH, TemporalRelation.ACTION_SAME_PERIOD
    return Compatibility.MISMATCH, TemporalRelation.ACTION_BEFORE_CLAIM


def _dependency(claim: StrategyClaim, action: ActionEvidence) -> Compatibility:
    """Does the action concern something the claim named as a dependency?

    Only an explicit dependency counts, and every distinctive word of it has
    to appear. Satisfying a dependency is never execution of the claim.
    """
    if not claim.dependencies:
        return Compatibility.NOT_APPLICABLE
    hay = f"{action.object_text or ''} {action.counterparty_text or ''} {action.sentence}"
    for dep in claim.dependencies:
        tokens = [t for t in re.findall(r"[A-Za-z][A-Za-z-]+", dep.raw_text)
                  if t.lower() not in _STOP and len(t) > 3]
        if tokens and all(_word_in(t, hay) for t in tokens):
            return Compatibility.MATCH
    return Compatibility.MISMATCH


def compare(claim: StrategyClaim, action: ActionEvidence,
            entity_surfaces: Sequence[str] = ()) -> ClaimActionComparison:
    """How one observed action stands to one claim. Pure and deterministic."""
    cref = ClaimRef(issuer=claim.provenance.issuer, node_id=claim.provenance.node_id,
                    source_period=claim.provenance.source_period or "",
                    predicate=claim.predicate, passage=claim.source_passage)
    aref = ActionRef(issuer=action.locator.issuer, accession=action.locator.accession,
                     key=action.key, predicate=action.predicate, sentence=action.sentence)
    ent, basis, surfaces = _entity(claim, entity_surfaces, action)
    ev = _event(claim, action)
    me = _measure(claim, action)
    tc, tr = _temporal(claim, action)
    dep = _dependency(claim, action)
    # direction is never compared: no ActionEvidence field states one, and
    # inventing it for symmetry would assert something no source says.
    di = Compatibility.NOT_APPLICABLE
    reasons: list[str] = []

    def out(relation: Relation) -> ClaimActionComparison:
        return ClaimActionComparison(
            claim=cref, action=aref, relation=relation, entity=ent, entity_basis=basis,
            entity_surfaces=surfaces, event=ev, measure=me, direction=di, temporal=tc,
            temporal_relation=tr, dependency=dep, refusal_reasons=tuple(reasons))

    if not claim.event_kinds and not claim.measure_kinds:
        reasons.append("insufficient_claim_semantics")
        return out(Relation.NOT_COMPARABLE)
    if action.action_type in _NOT_AN_ACT:
        reasons.append("no_shared_event_vocabulary")
        return out(Relation.NOT_COMPARABLE)
    if ent is Compatibility.MISMATCH:
        reasons.append("entity_issuer_only")
        return out(Relation.NOT_RELEVANT)
    if ent is Compatibility.UNKNOWN:
        reasons.append("entity_unresolved")
        return out(Relation.NOT_RELEVANT)
    if ev is not Compatibility.MATCH:
        if dep is Compatibility.MATCH:
            return out(Relation.RELEVANT_DEPENDENCY)
        reasons.append("event_mismatch")
        return out(Relation.NOT_RELEVANT)
    if tr is TemporalRelation.ACTION_BEFORE_CLAIM:
        reasons.append("temporal_action_before_claim")
        return out(Relation.NOT_RELEVANT)
    return out(Relation.RELEVANT_EXECUTION)


def compare_many(claims: Iterable[tuple[StrategyClaim, Sequence[str]]],
                 actions: Iterable[ActionEvidence]) -> tuple[ClaimActionComparison, ...]:
    """Every claim against every action of the same issuer, in a stable order.

    Pair generation is coarse on purpose and is not evidence: each pair still
    goes through `compare`.
    """
    acts = sorted(actions, key=lambda a: (a.locator.issuer, a.locator.accession, a.key))
    out = []
    for claim, surfaces in claims:
        for action in acts:
            if action.locator.issuer == claim.provenance.issuer:
                out.append(compare(claim, action, surfaces))
    return tuple(out)

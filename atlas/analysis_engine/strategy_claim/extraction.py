"""Reading a claim out of the passage management actually spoke.

The predicate decides everything. A verb map earned by the corpus says what
kind of evidence a claim licenses; a number is attached only when it is that
verb's own object. Nothing is inferred from a topic noun, and nothing is read
from Action Evidence.
"""
from __future__ import annotations

import re
from typing import Iterable, Sequence

from atlas.analysis_engine.strategy_claim.contracts import (
    ClaimProvenance, ClaimStatus, ClaimType, Dependency, Direction, EventKind, Horizon,
    Magnitude, MeasureKind, Observability, StrategyClaim,
)

__all__ = ["read_claim", "claims_for_node", "PREDICATES"]

#: (pattern, claim type, direction, measures, events). Every entry is a verb a
#: benchmark passage used. A noun alone never appears here: "capacity" in a
#: topic phrase is not a claim to add capacity.
PREDICATES: tuple[tuple[str, ClaimType, Direction, tuple, tuple], ...] = (
    (r"break ground|begin(?:ning)? construction|construct(?:ing)?", ClaimType.BUILD, Direction.BUILD,
     (), (EventKind.CONSTRUCTION_STARTED,)),
    (r"repurchased?|repurchasing", ClaimType.CAPITAL_RETURN, Direction.RETURN,
     (MeasureKind.CAPITAL_RETURNED,), (EventKind.SHARE_REPURCHASE,)),
    (r"allocat(?:e|ing|ed)\s+capital|invest(?:ing|ed|ment)?\s+more(?!\s+than)|invest(?:ing|ed)?|"
     r"requires?\s+growth\s+capital|will\s+require\s+growth\s+capital|allocated",
     ClaimType.CAPITAL_ALLOCATION, Direction.DEPLOY,
     (MeasureKind.CAPITAL_DEPLOYMENT,), (EventKind.CAPITAL_DEPLOYED,)),
    (r"secure|sign(?:ing|ed)?|enter(?:ing|ed)?\s+into", ClaimType.CONTRACTING, Direction.EXPAND,
     (), (EventKind.CONTRACT_ENTERED,)),
    (r"completed?|complete", ClaimType.DELIVERY, Direction.COMPLETE, (), (EventKind.COMPLETION,)),
    (r"establish(?:ing|ed)?", ClaimType.BUILD, Direction.BUILD, (), (EventKind.FACILITY_ESTABLISHED,)),
    (r"bring(?:ing)?|add(?:ing|ed)?", ClaimType.ADOPTION, Direction.INCREASE, (), ()),
)
_PREDICATE_RX = [(re.compile(r"\b(" + p + r")\b", re.I), t, d, m, e) for p, t, d, m, e in PREDICATES]

#: A claim's object may itself name a measurable quantity -- "investing in AI
#: compute capacity" is about capacity as well as capital.
_CAPACITY_OBJECT = re.compile(r"\b(?:capacity|megawatts?|MW|GW)\b", re.I)
#: A verb of spending only licenses a *measure* when the claim names something
#: measurable or states an amount. "invest more in driving success for our
#: merchants" is a priority: real, directional, and with nothing to count.
_MEASURABLE_OBJECT = re.compile(
    r"\b(?:capital|capacity|shares?|megawatts?|MW|GW|units?|fabs?|facilit(?:y|ies)|"
    r"plants?|sites?|assets?|programs?|dollars?)\b", re.I)
#: The object can name the instrument and so decide the claim: money allocated
#: *to a share repurchase programme* is capital returned, not capital deployed.
_CLAUSE_END = re.compile(r",(?!\d)|;|\.(?!\d)")
_RETURN_OBJECT = re.compile(
    r"\b(?:share repurchases?|buy-?backs?|repurchase program(?:me)?s?|dividends?|"
    r"to our (?:equity holders|shareholders|stockholders))\b", re.I)

#: A predicate inside "if we don't have something to bring to the table" is
#: not a claim; the clause states a hypothetical, and often denies it.
_HYPOTHETICAL = re.compile(r"\b(?:if|unless|whether|in the event)\b", re.I)
_NEGATED = re.compile(r"\b(?:not|n't|never|no longer)\b", re.I)
#: A sentence may open with a participial adjunct ("Adding to the existing
#: fab, we plan to begin construction..."). The adjunct is not the claim.
_ACTOR = re.compile(r"\b(?:we|we're|we've|we'll|our|the Company)\b", re.I)
_THESIS = re.compile(r"\b(?:we (?:believe|think)|we(?:'re| are) confident|in our view|our (?:belief|thesis))\b", re.I)
_FORWARD = re.compile(r"\b(?:plan to|plans to|aim to|aims to|will|we'll|expect to|expects to|intend to)\b", re.I)
_PROGRESSIVE = re.compile(r"\b(?:we(?:'re| are)|is|are)\s+\w+ing\b", re.I)
_PAST = re.compile(r"\b(?:we|the Company)\s+(?:\w+ed|repurchased|allocated|completed)\b", re.I)

_HORIZON = re.compile(
    r"\b(?:on schedule|over an? [\w-]+(?:-year)? period|after \d{4}|by \d{4}|in \d{4} and beyond|"
    r"in early calendar \d{4}|in late \d{4}|in fiscal Q[1-4]|in Q[1-4]|fiscal Q[1-4]|"
    r"over the next [\w-]+ years?|by year[- ]end(?: \d{4})?|this (?:year|quarter)|near[- ]term|long[- ]term)\b",
    re.I)
#: A marker names its dependency on one side only. "Y because X" and "Y driven
#: by X" put it on the right; "X underpins Y" puts it on the left. Reading a
#: left-marker rightwards captures the claim itself as its own dependency.
_DEPENDENCY = re.compile(
    r"\b(because|depends? on|depending on|is necessary to|are necessary to|"
    r"as permitted by the terms of|before any offsets from|driven by)\b", re.I)
_DEPENDENCY_LEFT = re.compile(r"\b(underpins?|led us to)\b", re.I)
_MAGNITUDE = re.compile(
    r"(?P<qual>approximately|more than|about|up to|over|at least)?\s*"
    r"(?P<sym>\$)\s?(?P<val>\d[\d,]*(?:\.\d+)?(?:\s*(?:billion|million|thousand))?)"
    r"|(?P<qual2>approximately|more than|about|up to|over|at least)?\s*"
    r"(?P<val2>\d[\d,]*(?:\.\d+)?)\s*(?P<unit2>MW|GW|megawatts?|gigawatts?)\b", re.I)


def _status(passage: str) -> ClaimStatus:
    if _THESIS.search(passage):
        return ClaimStatus.MANAGEMENT_THESIS
    if _FORWARD.search(passage):
        return ClaimStatus.FORWARD_INTENT
    if _PROGRESSIVE.search(passage):
        return ClaimStatus.ASSERTED_STRATEGY
    if _PAST.search(passage):
        return ClaimStatus.OBSERVATIONAL_STATEMENT
    return ClaimStatus.ASSERTED_STRATEGY


def _magnitude(passage: str, predicate_end: int) -> Magnitude | None:
    """A magnitude only when it is the predicate's own object: in the same
    sentence, after the verb, and not inside a hedge about what would be
    needed ("there's going to probably need to be a spread around that $555 a
    megawatt day")."""
    tail = passage[predicate_end:]
    if re.search(r"\b(?:need to be|would need|depending on|spread around)\b", passage[:predicate_end], re.I):
        return None
    m = _MAGNITUDE.search(tail)
    if not m:
        return None
    if m.group("sym"):
        return Magnitude(value_text=m.group("val").strip(), unit="$", qualifier=(m.group("qual") or "").strip())
    return Magnitude(value_text=m.group("val2").strip(), unit=m.group("unit2"),
                     qualifier=(m.group("qual2") or "").strip())


def _trim(phrase: str, head: bool, limit: int = 120) -> str:
    """Keep whole words: a dependency cut mid-word reads as a different one."""
    if len(phrase) <= limit:
        return phrase
    cut = phrase[:limit].rsplit(" ", 1)[0] if head else phrase[-limit:].split(" ", 1)[-1]
    return cut.strip()


def _dependencies(passage: str, predicate: str = "") -> tuple[Dependency, ...]:
    out = []
    for m in _DEPENDENCY.finditer(passage):
        rest = passage[m.end():].strip()
        phrase = _CLAUSE_END.split(rest)[0].strip()
        if phrase:
            out.append(Dependency(raw_text=_trim(phrase, head=True), marker=m.group(1)))
    for m in _DEPENDENCY_LEFT.finditer(passage):
        head = passage[:m.start()].strip()
        phrase = _CLAUSE_END.split(head)[-1].strip()
        if phrase:
            out.append(Dependency(raw_text=_trim(phrase, head=False), marker=m.group(1)))
    # A claim is never its own dependency.
    if predicate:
        out = [d for d in out if predicate.lower() not in d.raw_text.lower()]
    return tuple(out)


def _observability(measures, events, status) -> Observability:
    if measures:
        return Observability.QUANTITATIVELY_OBSERVABLE
    if events:
        return Observability.QUALITATIVELY_OBSERVABLE
    if status is ClaimStatus.MANAGEMENT_THESIS:
        return Observability.NOT_DIRECTLY_OBSERVABLE
    return Observability.PARTIALLY_OBSERVABLE


def read_claim(passage: str, provenance: ClaimProvenance, entities: Sequence[str] = ()) -> StrategyClaim | None:
    """One claim, or None when the passage states no management predicate."""
    # The main clause carries the claim. A sentence that opens with a
    # participial adjunct ("Adding to the existing fab, we plan to begin
    # construction...") puts a verb before the actor that is not the predicate,
    # so a candidate after the first actor token outranks an earlier one.
    actor = _ACTOR.search(passage)
    actor_at = actor.start() if actor else 0
    best = None
    for rx, ctype, direction, measures, events in _PREDICATE_RX:
        for m in rx.finditer(passage):
            rank = (m.start() < actor_at, m.start())
            if best is None or rank < best[0]:
                best = (rank, m, ctype, direction, measures, events)
    if best is None:
        return None
    _, m, ctype, direction, measures, events = best
    # A predicate governed by a condition or a negation states no claim.
    clause_start = max((b.end() for b in _CLAUSE_END.finditer(passage[:m.start()])), default=0)
    governing = passage[clause_start:m.start()]
    if _HYPOTHETICAL.search(governing) or _NEGATED.search(governing):
        return None
    # A full stop inside a number is not the end of the clause: splitting on a
    # bare "." turned "$4.9 billion to our share repurchase program" into "$4".
    object_text = _CLAUSE_END.split(passage[m.end():].strip())[0].strip()
    measures = set(measures)
    if _CAPACITY_OBJECT.search(object_text):
        measures.add(MeasureKind.CAPACITY)
    status = _status(passage)
    magnitude = _magnitude(passage, m.end())
    if _RETURN_OBJECT.search(object_text):
        ctype, direction = ClaimType.CAPITAL_RETURN, Direction.RETURN
        measures = {MeasureKind.CAPITAL_RETURNED}
        events = (EventKind.SHARE_REPURCHASE,)
    if measures and magnitude is None and not (
            _MEASURABLE_OBJECT.search(object_text) or _MEASURABLE_OBJECT.search(m.group(1))):
        measures = set()
    horizon = _HORIZON.search(passage)
    return StrategyClaim(
        provenance=provenance, source_passage=passage, claim_type=ctype, status=status,
        predicate=m.group(1), direction=direction, object_text=object_text,
        entities=tuple(entities), observability=_observability(measures, events, status),
        measure_kinds=tuple(sorted(measures, key=lambda x: x.value)), event_kinds=tuple(events),
        magnitude=magnitude, horizon=Horizon(raw_text=horizon.group(0)) if horizon else None,
        dependencies=_dependencies(passage, m.group(1)),
    )


def claims_for_node(node_id: str, issuer: str, node_kind: str,
                    passages: Iterable[tuple[str, str, str, str]],
                    entities: Sequence[str] = ()) -> tuple[StrategyClaim, ...]:
    """Claims from a node's own evidence: `(text, record_id, period, speaker)`."""
    out = []
    for text, record_id, period, speaker in passages:
        claim = read_claim(text, ClaimProvenance(issuer=issuer, node_id=node_id, node_kind=node_kind,
                                                 source_record_id=record_id, source_period=period,
                                                 speaker_title=speaker), entities)
        if claim is not None:
            out.append(claim)
    return tuple(out)

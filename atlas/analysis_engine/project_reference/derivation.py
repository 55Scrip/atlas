"""Read a project reference out of an object phrase, or read nothing.

The object of a claim or an action is already the source's own words for what
was done to what. This module asks one question of it: does its *head* name a
physical thing being built or run? A facility word somewhere in the phrase is
not enough -- "closure activities at our Baldwin facility" is about activities,
and "a revolving credit facility" is about money.
"""
from __future__ import annotations

import re

from atlas.analysis_engine.action_evidence import ActionEvidence
from atlas.analysis_engine.project_reference.contracts import (
    ProjectKind, ProjectReference, ReferenceProvenance, SourceRole,
)
from atlas.analysis_engine.strategy_claim import StrategyClaim

#: Head nouns the corpus earns. The word must be the head of the object, not
#: merely present in it. "room" is absent on purpose: every "clean room" in the
#: corpus is capacity language ("new clean room space"), not a project.
_HEADS: dict[str, ProjectKind] = {
    "fab": ProjectKind.FAB, "fabs": ProjectKind.FAB,
    "facility": ProjectKind.FACILITY, "facilities": ProjectKind.FACILITY,
    "cleanroom": ProjectKind.CLEANROOM, "cleanrooms": ProjectKind.CLEANROOM,
    "unit": ProjectKind.UNKNOWN, "units": ProjectKind.UNKNOWN,
}
_HEAD_RE = re.compile(r"(?<![A-Za-z])(" + "|".join(sorted(_HEADS, key=len, reverse=True))
                      + r")(?![A-Za-z])", re.IGNORECASE)

#: A facility that is *financed* rather than built. The corpus earns exactly
#: one such word, and it is the most dangerous false positive available: a
#: "credit facility" is a line of money, not a building.
_FINANCIAL = ("credit",)

_LEADING_PREP = re.compile(r"^(?:for|on|of|to|in|at|into|from|with)\s+", re.IGNORECASE)

#: A trailing phrase about *when*, not *where*. "in early calendar 2026" is a
#: date; "in Boise, Idaho" is a place. Only a time word makes it the former.
_TEMPORAL_TAIL = re.compile(
    r"\s+(?:by|in|on|during|through|over|before|after|beginning|starting)\s+"
    r"[^,;]*?(?<![A-Za-z])(?:\d{4}|calendar|fiscal|quarter|quarterly|month|year)(?![A-Za-z])"
    r"[^,;]*$", re.IGNORECASE)

_LOCATIVE_TAIL = re.compile(r"^\s+(?:at|in|near)\s+(\S.*)$", re.IGNORECASE)
_LOCATIVE_BEFORE = re.compile(r"(?<![A-Za-z])(?:at|in|near)(?![A-Za-z])\s", re.IGNORECASE)

#: Words that end a noun phrase when walking leftwards off the head.
_PHRASE_STOP = frozenset((
    "of", "in", "at", "on", "for", "to", "from", "with", "by", "near", "into",
    "and", "or", "but", "not", "that", "which", "than", "as",
))
_DETERMINERS = frozenset(("a", "an", "the", "our", "its", "their", "this", "that",
                          "these", "those"))
#: Ordinals the corpus states. Never counted, so never extended by inference.
_ORDINALS = frozenset(("first", "second"))


def _noun_phrase(text: str, head_end: int) -> str:
    """The head's own noun phrase: walk left off the head until the source
    changes direction with a preposition, a conjunction or a comma."""
    left = text[:head_end]
    tokens = left.split()
    keep = len(tokens)
    for i in range(len(tokens) - 2, -1, -1):
        word = tokens[i]
        if word.lower().strip(",;:") in _PHRASE_STOP or word.endswith((",", ";", ":")):
            keep = i + 1
            break
        keep = i
    return " ".join(tokens[keep:])


def _read_object(object_text: str) -> tuple[str, ProjectKind, str | None] | None:
    """(surface, kind, location) -- or None when the object names no project."""
    phrase = _LEADING_PREP.sub("", object_text.strip(), count=1)
    phrase = _TEMPORAL_TAIL.sub("", phrase)
    # A facility word inside a locative adjunct belongs to the place, not to the
    # object: "closure activities AT those ponds at our Baldwin facility". The
    # head of what remains is its last noun.
    matches = [m for m in _HEAD_RE.finditer(phrase)
               if not _LOCATIVE_BEFORE.search(phrase[:m.start()])]
    if not matches:
        return None
    head = matches[-1]
    tail = phrase[head.end():]
    location: str | None = None
    if tail.strip():
        locative = _LOCATIVE_TAIL.match(tail)
        if locative is None:
            return None
        location = locative.group(1).strip()
    surface = _noun_phrase(phrase, head.end())
    if any(w in surface.lower().split() for w in _FINANCIAL):
        return None
    return surface, _HEADS[head.group(1).lower()], location


def _describe(surface: str) -> tuple[tuple[str, ...], str | None]:
    tokens = surface.split()
    modifiers = tuple(t for t in tokens[:-1] if t.lower() not in _DETERMINERS)
    ordinal = next((t.lower() for t in modifiers if t.lower() in _ORDINALS), None)
    return modifiers, ordinal


def _build(read, provenance: ReferenceProvenance, role: SourceRole) -> tuple[ProjectReference, ...]:
    surface, kind, location = read
    modifiers, ordinal = _describe(surface)
    return (ProjectReference(provenance=provenance, surface=surface, kind=kind,
                             location_surface=location, modifiers=modifiers,
                             ordinal=ordinal, source_role=role),)


def references_from_claim(claim: StrategyClaim) -> tuple[ProjectReference, ...]:
    read = _read_object(claim.object_text)
    if read is None:
        return ()
    return _build(read, ReferenceProvenance(
        issuer=claim.provenance.issuer, owner_kind="strategy_claim",
        owner_key=claim.provenance.node_id, source_object_text=claim.object_text,
        source_passage=claim.source_passage, source_period=claim.provenance.source_period,
    ), SourceRole.OBJECT_OF_CLAIM)


def references_from_action(action: ActionEvidence) -> tuple[ProjectReference, ...]:
    read = _read_object(action.object_text)
    if read is None:
        return ()
    return _build(read, ReferenceProvenance(
        issuer=action.locator.issuer, owner_kind="action_evidence",
        owner_key=action.locator.key, source_object_text=action.object_text,
        source_passage=action.sentence, source_period=None,
    ), SourceRole.OBJECT_OF_ACTION)

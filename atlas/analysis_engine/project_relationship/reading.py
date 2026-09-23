"""Read declared relationships out of filing paragraphs, or read nothing.

Every rule here answers the same question: did the filer *say* this? A shared
place, a shared head noun, a shared year and a shared list position all fail
that test on their own, so none of them licenses a record.
"""
from __future__ import annotations

import re

from atlas.analysis_engine.project_relationship.contracts import (
    ContextForm, Direction, EndpointRole, ProjectRelationshipEvidence,
    RelationshipEndpoint, RelationshipKind, SourceParagraph, SourceSpan, StructuralContext,
)

#: Words the filings use for a physical plant. A relationship between two
#: phrases that name no plant is somebody else's relationship.
_HEADS = ("fab", "fabs", "facility", "facilities", "cleanroom", "cleanrooms", "plant", "plants")
_HEAD_RE = re.compile(r"(?<![A-Za-z])(" + "|".join(_HEADS) + r")(?![A-Za-z])", re.IGNORECASE)
#: The singular forms a bare definite anaphor can use.
_ANAPHOR_RE = re.compile(r"(?<![A-Za-z])the\s+(fab|facility|cleanroom|plant)(?![A-Za-z])", re.IGNORECASE)

_BULLET = re.compile(r"^\s*[•▪●∙]\s*")
_LEAD_IN = re.compile(r":\s*$")
#: Page furniture sits between bullets without ending the list.
_FURNITURE = re.compile(r"^\s*(?:\d+|\d+\s*\|.*|Table of Contents|[A-Z][A-Z .,&'\-]{1,40})\s*$")

#: Connectives that state a part-whole relationship outright.
_PART_WHOLE = re.compile(r",?\s+(consisting of|which include|which includes)\s+", re.IGNORECASE)
#: An ordinal that numbers a plant -- not a half, a quarter or a phase of a
#: year. The trailing "in <Place>" is kept when the source attaches one: an
#: ordinal without its place says far less than the filer did.
_ORDINAL = re.compile(r"(?<![A-Za-z])(?:a|the)\s+(second|third|fourth)\s+(?:[^,.;:]{0,80}?)"
                      r"(?<![A-Za-z])(?:" + "|".join(_HEADS) + r")(?![A-Za-z])"
                      r"(?:\s+in\s+[A-Z][\w.'\-]*(?:,\s*[A-Z][\w.'\-]*)?)?", re.IGNORECASE)
#: A short name the source gives to what it has just described.
_DEFINED = re.compile(r"\((the\s+[^()]{2,70})\)")
_SENTENCE_END = re.compile(r"(?<=[.;])\s+")


#: A "facility" that is money, and a caption that is an accounting line rather
#: than a building. Both use the plant words and neither names a plant.
_NOT_A_PLANT = re.compile(r"(?:(?<![A-Za-z])credit\s+)(?:" + "|".join(_HEADS) + r")(?![A-Za-z])"
                          r"|property,\s+plant\s+and\s+equipment", re.IGNORECASE)


def _names_a_plant(text: str) -> bool:
    """Whether the filer is talking about a building here. "Facility" is the
    same word for a credit line and for a fab, and "plant" is half of an
    accounting caption, so the word alone settles nothing."""
    return any(m for m in _HEAD_RE.finditer(text)
               if not any(bad.start() <= m.start() < bad.end() or bad.start() == m.start() - 7
                          for bad in _NOT_A_PLANT.finditer(text)))


def _span(p: SourceParagraph) -> SourceSpan:
    return SourceSpan(issuer=p.issuer, accession=p.accession, section=p.section,
                      paragraph_ordinal=p.ordinal)


def _sentences(text: str) -> list[tuple[int, str]]:
    out, at = [], 0
    for part in _SENTENCE_END.split(text):
        out.append((at, part))
        at += len(part) + 1
    return out


def _from_sentences(p: SourceParagraph, period):
    span = _span(p)
    for offset, sentence in _sentences(p.text):
        for m in _PART_WHOLE.finditer(sentence):
            whole, part = sentence[:m.start()].strip(), sentence[m.end():].strip()
            if not (whole and part and _names_a_plant(whole) and _names_a_plant(part)):
                continue
            yield ProjectRelationshipEvidence(
                kind=RelationshipKind.PART_WHOLE,
                left=RelationshipEndpoint(whole, EndpointRole.WHOLE, span),
                right=RelationshipEndpoint(part, EndpointRole.PART, span),
                direction=Direction.WHOLE_TO_PART, licensing_surface=m.group(1),
                context=StructuralContext(ContextForm.SENTENCE, None, m.group(1)),
                source_period=period)
        for m in _ORDINAL.finditer(sentence):
            yield ProjectRelationshipEvidence(
                kind=RelationshipKind.ORDINAL_DISTINCTION,
                left=RelationshipEndpoint(m.group(0), EndpointRole.NUMBERED_MEMBER, span),
                right=None, direction=Direction.NONE, licensing_surface=m.group(1),
                context=StructuralContext(ContextForm.SENTENCE, None, m.group(1)),
                source_period=period)
        for m in _DEFINED.finditer(sentence):
            term = m.group(1).strip()
            referent = sentence[:m.start()].strip()
            if not (_names_a_plant(term) and referent and _names_a_plant(referent)):
                continue
            yield ProjectRelationshipEvidence(
                kind=RelationshipKind.DEFINED_TERM,
                left=RelationshipEndpoint(term, EndpointRole.TERM, span),
                right=RelationshipEndpoint(referent, EndpointRole.REFERENT, span),
                direction=Direction.TERM_TO_REFERENT, licensing_surface=m.group(0),
                context=StructuralContext(ContextForm.SENTENCE, None, "("),
                source_period=period)


#: A phrase that introduces something. "The facility" does not introduce
#: anything -- it is already pointing at something else, so it cannot be what a
#: later "the facility" points back at.
_INTRODUCES = re.compile(r"(?<![A-Za-z])(?:a|an|our|its|their)(?![A-Za-z])", re.IGNORECASE)


def _from_anaphora(p: SourceParagraph, period):
    """A bare "the fab" points back only when the paragraph offers exactly one
    thing for it to point at. Two candidates is not a harder problem; it is a
    different sentence, and the source has not told us which."""
    span = _span(p)
    for m in _ANAPHOR_RE.finditer(p.text):
        head = m.group(1)
        before = p.text[:m.start()]
        found = []
        for h in re.finditer(r"(?<![A-Za-z])" + head + r"(?![A-Za-z])", before, re.IGNORECASE):
            starts = [d for d in _INTRODUCES.finditer(before[:h.start()])
                      if h.start() - d.end() <= 70 and "." not in before[d.end():h.start()]]
            if not starts:
                continue
            phrase = before[starts[-1].start():h.end()].strip()
            # A "the" between the two means the head belongs to that definite
            # phrase, which is itself pointing somewhere rather than introducing.
            if re.search(r"(?<![A-Za-z])the(?![A-Za-z])", before[starts[-1].end():h.start()],
                         re.IGNORECASE):
                continue
            if _names_a_plant(phrase):
                found.append(phrase)
        if len(found) != 1 or not _names_a_plant(m.group(0) + " " + found[0]):
            continue
        yield ProjectRelationshipEvidence(
            kind=RelationshipKind.ANAPHORIC_COREFERENCE,
            left=RelationshipEndpoint(m.group(0), EndpointRole.ANAPHOR, span),
            right=RelationshipEndpoint(found[0], EndpointRole.ANTECEDENT, span),
            direction=Direction.ANAPHOR_TO_ANTECEDENT, licensing_surface=m.group(0),
            context=StructuralContext(ContextForm.PARAGRAPH, None, "the"),
            source_period=period)


def read_relationships(paragraphs) -> tuple[ProjectRelationshipEvidence, ...]:
    """Every relationship the given paragraphs declare.

    Each rule reads one paragraph and stops there. A list cannot span two
    filings and a pronoun cannot reach into one, so nothing here needs to see
    the document as a whole -- and a reader that cannot look across paragraphs
    cannot accidentally relate two filings that merely use the same words."""
    out: list[ProjectRelationshipEvidence] = []
    for p in paragraphs:
        out.extend(_from_sentences(p, p.period))
        out.extend(_from_anaphora(p, p.period))
    return tuple(out)

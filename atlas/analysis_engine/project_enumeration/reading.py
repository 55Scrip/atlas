"""Read project enumerations out of filing paragraphs, or read nothing.

Two conditions, and the measurement behind each one:

* a lead-in the source ends with a colon. Dropped, the rule admits two more
  corpus lists -- a capital-allocation highlights list and one about a credit
  agreement funding development. Neither enumerates projects, and neither has
  a lead-in naming what its bullets are entries of.

* an entry that both names a plant and reports an observed action. Dropped,
  the rule admits five more -- two share-repurchase lists, a company
  acquisition, a buyback authorisation and a completed merger.

Neither condition looks at what a list is *about*. There is no topical rule
here, and adding one would be our reading of the filing rather than the
filing's own words.
"""
from __future__ import annotations

import re

from atlas.analysis_engine.action_evidence import ActionEvidence
from atlas.analysis_engine.project_enumeration.contracts import (
    EnumerationEntry, ProjectEnumerationEvidence, SourceParagraph, SourceSpan,
)

#: The words the filings use for a physical plant, and the two ways those words
#: are used for something else -- a line of credit, and an accounting caption.
_HEADS = ("fab", "fabs", "facility", "facilities", "cleanroom", "cleanrooms", "plant", "plants")
_HEAD_RE = re.compile(r"(?<![A-Za-z])(" + "|".join(_HEADS) + r")(?![A-Za-z])", re.IGNORECASE)
_NOT_A_PLANT = re.compile(r"(?:(?<![A-Za-z])credit\s+)(?:" + "|".join(_HEADS) + r")(?![A-Za-z])"
                          r"|property,\s+plant\s+and\s+equipment", re.IGNORECASE)

_BULLET = re.compile(r"^\s*[•▪●∙]\s*")
_LEAD_IN = re.compile(r":\s*$")
#: Page furniture sits between bullets without ending the list.
_FURNITURE = re.compile(r"^\s*(?:\d+|\d+\s*\|.*|Table of Contents|[A-Z][A-Z .,&'\-]{1,40})\s*$")


def _names_a_plant(text: str) -> bool:
    return any(m for m in _HEAD_RE.finditer(text)
               if not any(b.start() <= m.start() < b.end() or b.start() == m.start() - 7
                          for b in _NOT_A_PLANT.finditer(text)))


def _span(p: SourceParagraph) -> SourceSpan:
    return SourceSpan(issuer=p.issuer, accession=p.accession, section=p.section,
                      paragraph_ordinal=p.ordinal)


def _where(action: ActionEvidence) -> tuple[str, str, str, int]:
    """The paragraph an action names. This is the only link between a list entry
    and an action: the entry IS a paragraph, and the action says which paragraph
    it was read from. No text is compared."""
    locator = action.locator
    return (locator.issuer, locator.accession, locator.section, locator.paragraph_ordinal)


def _place(p: SourceParagraph) -> tuple[str, str, str, int]:
    return (p.issuer, p.accession, p.section, p.ordinal)


def _runs(paragraphs: list[SourceParagraph]):
    """(lead_in, entries) for each bulleted run that has a lead-in."""
    i = 0
    while i < len(paragraphs):
        if not _BULLET.match(paragraphs[i].text):
            i += 1
            continue
        start, entries = i, []
        while i < len(paragraphs):
            text = paragraphs[i].text
            if _BULLET.match(text):
                entries.append(paragraphs[i]); i += 1
            elif _FURNITURE.match(text):
                i += 1
            else:
                break
        lead = None
        for back in range(start - 1, -1, -1):
            text = paragraphs[back].text
            if _FURNITURE.match(text) or _BULLET.match(text):
                continue
            if _LEAD_IN.search(text):
                lead = paragraphs[back]
            break
        if lead is not None:
            yield lead, entries


def read_enumerations(paragraphs, actions) -> tuple[ProjectEnumerationEvidence, ...]:
    """Every list in these paragraphs that the source is enumerating projects in.

    ``actions`` are already-extracted ActionEvidence records. They are looked up
    by the paragraph they name, never by comparing their words to an entry's.
    """
    by_place: dict[tuple[str, str, str, int], list[str]] = {}
    for action in actions:
        by_place.setdefault(_where(action), []).append(action.locator.key)
    grouped: dict[tuple[str, str, str], list[SourceParagraph]] = {}
    for paragraph in paragraphs:
        grouped.setdefault((paragraph.issuer, paragraph.accession, paragraph.section),
                           []).append(paragraph)
    out: list[ProjectEnumerationEvidence] = []
    for _, group in sorted(grouped.items()):
        group = sorted(group, key=lambda p: p.ordinal)
        for lead, entries in _runs(group):
            read = []
            for position, entry in enumerate(entries, 1):
                surface = _BULLET.sub("", entry.text).strip()
                read.append(EnumerationEntry(
                    surface=surface, position=position, span=_span(entry),
                    action_keys=tuple(by_place.get(_place(entry), ())),
                    names_a_plant=_names_a_plant(surface)))
            grounded = tuple(e.position for e in read if e.action_keys and e.names_a_plant)
            if not grounded:
                continue
            out.append(ProjectEnumerationEvidence(
                container=_span(lead), lead_in=lead.text, entries=tuple(read),
                grounded_positions=grounded, source_period=lead.period))
    return tuple(out)

"""Read a governing phrase and the units it introduces, or read nothing.

Three things have to be visible in the source, and all three are checked:

* the start -- a paragraph ending in a colon with a list item directly after it.
  A colon on its own proves nothing: of 944 colon-terminated paragraphs in the
  held filings, 691 are followed by prose. Micron's own Properties section
  contains one, introducing a table the parser holds separately.
* the members -- the run of bullet-marked paragraphs, page furniture stepped
  over. Every interruption found inside a run in the held filings is a page
  number, a running header or a table-of-contents line; never a heading.
* the end -- the first following paragraph the source does not mark. A scope
  that runs to the end of a section without one is not recorded.

Nothing here reads what the paragraphs say.
"""
from __future__ import annotations

import re

from atlas.analysis_engine.structural_scope.contracts import (
    BoundaryKind, GovernedUnit, GovernedUnitKind, GovernorKind, SourceParagraph, SourceSpan,
    StructuralScopeEvidence,
)

_BULLET = re.compile(r"^\s*[•▪●∙]")
_COLON = re.compile(r":\s*$")
#: Page furniture interrupts a list without ending it: a page number, a running
#: header, a table-of-contents line.
_FURNITURE = re.compile(r"^\s*(?:\d+|\d+\s*\|.*|Table of Contents|[A-Z][A-Z .,&'\-]{1,40})\s*$")


def _span(p: SourceParagraph) -> SourceSpan:
    return SourceSpan(issuer=p.issuer, accession=p.accession, section=p.section,
                      paragraph_ordinal=p.ordinal)


def read_scopes(paragraphs) -> tuple[StructuralScopeEvidence, ...]:
    """Every scope the given paragraphs show. Paragraphs are grouped by document
    and section, because a list cannot span two filings and the item boundary is
    the outermost structure the source preserves."""
    grouped: dict[tuple[str, str, str], list[SourceParagraph]] = {}
    for paragraph in paragraphs:
        grouped.setdefault((paragraph.issuer, paragraph.accession, paragraph.section),
                           []).append(paragraph)
    out: list[StructuralScopeEvidence] = []
    for _, group in sorted(grouped.items()):
        group = sorted(group, key=lambda p: p.ordinal)
        for index, governor in enumerate(group):
            text = governor.text
            if _BULLET.match(text) or _FURNITURE.match(text) or not _COLON.search(text):
                continue
            first = index + 1
            if first >= len(group) or not _BULLET.match(group[first].text):
                continue
            units, at = [], first
            while at < len(group) and (_BULLET.match(group[at].text)
                                       or _FURNITURE.match(group[at].text)):
                if _BULLET.match(group[at].text):
                    units.append(GovernedUnit(
                        surface=group[at].text, kind=GovernedUnitKind.BULLET,
                        span=_span(group[at]), position=len(units) + 1))
                at += 1
            if at >= len(group):
                continue  # no end in sight, so no scope
            out.append(StructuralScopeEvidence(
                governor_surface=text, governor_kind=GovernorKind.LEAD_IN,
                governor_span=_span(governor), governed_units=tuple(units),
                boundary_kind=BoundaryKind.FIRST_UNMARKED_PARAGRAPH,
                boundary_span=_span(group[at]), source_period=governor.period))
    return tuple(out)

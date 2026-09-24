"""Which source units a governing phrase introduces, and where that stops.

A filing says things like "Outside the U.S., we are investing ... include the
following:" and then lists them. The list belongs to that sentence. Atlas held
the sentence and the list and nothing that said one introduced the other.

This records that, and only that. It is a fact about the document's layout:
these units follow this phrase, inside a boundary the document itself sets. It
is not a claim about what the phrase means, what the units are about, or how
any two of them relate. "Outside the U.S." governing a Singapore bullet says
the bullet is in that list -- not that Singapore is outside the United States,
which is a reading, and not ours to make here.

What the held filings actually carry is narrow. A parsed section has an item
heading, its paragraphs, its tables -- and no subsections: 0 of 357 across the
22 held filings. A paragraph carries an order index and text. There is no
nesting, no depth and no parent, so a heading governing a region of prose
cannot be represented at all. A colon-terminated paragraph followed by a run
of bullets can, because its start, its members and its end are all visible.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

STRUCTURAL_SCOPE_VERSION = "1.0.0"


class GovernorKind(str, Enum):
    LEAD_IN = "lead_in"
    """A paragraph ending in a colon, immediately followed by a list. The only
    governing form the held representation preserves: section headings survive
    as an item number, and nothing below that survives at all."""


class GovernedUnitKind(str, Enum):
    BULLET = "bullet"
    """A paragraph the source marks with a bullet. The only governed form that
    can be told apart from ordinary prose after parsing."""


class BoundaryKind(str, Enum):
    FIRST_UNMARKED_PARAGRAPH = "first_unmarked_paragraph"
    """The scope ends at the first following paragraph the source does not mark
    as a list item. The document sets this, not us."""


@dataclass(frozen=True)
class SourceParagraph:
    issuer: str
    accession: str
    section: str
    ordinal: int
    text: str
    period: str | None = None


@dataclass(frozen=True)
class SourceSpan:
    issuer: str
    accession: str
    section: str
    paragraph_ordinal: int


@dataclass(frozen=True)
class GovernedUnit:
    surface: str
    kind: GovernedUnitKind
    span: SourceSpan
    position: int
    """Where the unit sits in the run, from 1. Source order, and nothing more:
    the second bullet is the second bullet."""


@dataclass(frozen=True)
class StructuralScopeEvidence:
    governor_surface: str
    """The governing phrase, verbatim."""
    governor_kind: GovernorKind
    governor_span: SourceSpan
    governed_units: tuple[GovernedUnit, ...]
    boundary_kind: BoundaryKind
    boundary_span: SourceSpan
    """The first unit outside the scope. A scope whose end cannot be shown is
    not recorded, so this is never absent."""
    source_period: str | None
    version: str = STRUCTURAL_SCOPE_VERSION

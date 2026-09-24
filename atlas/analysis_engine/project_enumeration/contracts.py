"""When a filing is listing projects, and not merely mentioning one.

A 10-K is full of bulleted lists, and almost none of them are about projects:
they are lists of risks, of factors affecting demand, of the subjects of
forward-looking statements, of spending categories, of financing activities, of
audit procedures. Sprint 33 measured this -- of the 40 lists whose entries name
a plant, 6 enumerate projects -- and concluded that list shape settles nothing.

What separates the six is that the filer reports having *done* something in at
least one entry. That is not a judgement about the topic of the list; it is an
independently extracted observed action, sitting in the paragraph the entry
occupies. This layer records the conjunction and nothing else.

It says these entries are siblings of one enumeration. It does not say they are
different projects, and it offers no way to ask.
"""
from __future__ import annotations

from dataclasses import dataclass

PROJECT_ENUMERATION_VERSION = "1.0.0"


@dataclass(frozen=True)
class SourceSpan:
    """Where the words are. A later layer joins to other read models by this,
    not by comparing strings."""

    issuer: str
    accession: str
    section: str
    paragraph_ordinal: int


@dataclass(frozen=True)
class SourceParagraph:
    issuer: str
    accession: str
    section: str
    ordinal: int
    text: str
    period: str | None = None


@dataclass(frozen=True)
class EnumerationEntry:
    surface: str
    """The entry as written, with its bullet removed and nothing else changed."""
    position: int
    """Where the entry sits in the list, from 1. Source order, and descriptive
    only: the second bullet is not the second fab."""
    span: SourceSpan
    action_keys: tuple[str, ...]
    """The locator keys of the observed actions reported in this entry's own
    paragraph. Empty for an entry that reports none -- a filer may list one site
    it broke ground on beside three it is modernising, and the others are still
    entries of the list."""
    names_a_plant: bool


@dataclass(frozen=True)
class ProjectEnumerationEvidence:
    """One list the source is enumerating projects in."""

    container: SourceSpan
    """The lead-in's paragraph. Without a lead-in there is no enumeration to be
    a sibling of, and a bulleted run with no lead-in is a run of bullets."""
    lead_in: str
    """The lead-in verbatim. It is what the entries are entries OF, and Sprint
    32 showed a human reading can turn on it -- "Outside the U.S." governing
    what follows."""
    entries: tuple[EnumerationEntry, ...]
    grounded_positions: tuple[int, ...]
    """Which entries carry an observed action. These are why the list is read as
    an enumeration of projects at all, so they are named rather than counted."""
    source_period: str | None
    version: str = PROJECT_ENUMERATION_VERSION

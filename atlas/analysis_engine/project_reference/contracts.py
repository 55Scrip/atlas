"""What thing a claim or an action is about, in the source's own words.

A project reference is a *reference*, never an identity. It says: these are
the words the filer used for the thing being built, bought or finished. It
does not say whether two references denote the same real-world project --
that question is a different layer, and the corpus does not yet answer it.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

PROJECT_REFERENCE_VERSION = "1.0.0"


class ProjectKind(str, Enum):
    """The class of thing, read off the source's own head noun. Descriptive
    only: two references of the same kind are not thereby the same project,
    and two of different kinds are not thereby different ones."""

    FAB = "fab"
    """The source calls it a fab."""

    FACILITY = "facility"
    """The source calls it a facility -- the least specific word that still
    names a physical plant."""

    CLEANROOM = "cleanroom"
    """The source calls it a cleanroom."""

    UNKNOWN = "unknown"
    """The source names a thing at a place without naming what class of thing
    it is -- "our new gas-fired units". The reference is real; the class is
    not stated, and inventing one would be our word, not the filer's."""


class SourceRole(str, Enum):
    """Where in the source record the reference was read."""

    OBJECT_OF_CLAIM = "object_of_claim"
    """The object of what management said it would do or had done."""

    OBJECT_OF_ACTION = "object_of_action"
    """The object of a reported action."""


@dataclass(frozen=True)
class ReferenceProvenance:
    """Enough to go back to the exact words and to the record that owns them."""

    issuer: str
    owner_kind: str
    """"strategy_claim" or "action_evidence"."""
    owner_key: str
    """The owning record's own identifier, unchanged."""
    source_object_text: str
    """The object the reference was read from, verbatim."""
    source_passage: str
    """The sentence, verbatim."""
    source_period: str | None
    """The period the owning record carries, when it carries one."""


@dataclass(frozen=True)
class ProjectReference:
    provenance: ReferenceProvenance
    surface: str
    """The project phrase exactly as written, with its determiner: "a new NAND
    fab". Never normalised, never lower-cased, never stemmed."""
    kind: ProjectKind
    location_surface: str | None
    """The place the source attaches to this project, verbatim and unresolved
    -- "Boise, Idaho", "our Singapore site", "this site". None when the object
    names no place. A place that is merely nearby in the record is not one."""
    modifiers: tuple[str, ...]
    """The words the source uses to qualify the head, in source order and with
    source spelling: ("new", "NAND"), ("HBM", "advanced", "packaging"). These
    are what tell one project from another, so they are never dropped."""
    ordinal: str | None
    """An ordinal the source itself states -- "first", "second". Never counted,
    never inferred, and never a position in any set we constructed."""
    source_role: SourceRole
    version: str = PROJECT_REFERENCE_VERSION

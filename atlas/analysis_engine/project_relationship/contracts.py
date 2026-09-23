"""What a filing says about how two things it names are related.

This layer records relationships the source itself declares -- one thing is
part of another, two things are separate entries of one list, a term is
defined, a later phrase points back at an earlier one, a thing is numbered
within a set. It records the words and the structure that carry the claim.

It does not decide whether two references are the same project. A source can
say "the second fab in Boise" without telling us which fab the other one is,
and it can list two facilities without saying whether a third statement
elsewhere means either of them. Those are identity questions, and this layer
deliberately cannot answer them.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

PROJECT_RELATIONSHIP_VERSION = "1.0.0"


class RelationshipKind(str, Enum):
    """Only the forms the held filings actually declare."""

    DISTINCT_ENUMERATION = "distinct_enumeration"
    """This phrase is one entry of an enumeration the source introduces. Two
    entries of the same enumeration are, by the source's own layout, separate
    entries -- which is not the same as being separate projects."""

    PART_WHOLE = "part_whole"
    """The source states that one thing consists of, or includes, another."""

    ORDINAL_DISTINCTION = "ordinal_distinction"
    """The source numbers this one within a set -- "a second planned fab".
    It says a counterpart exists. It does not say which one."""

    ANAPHORIC_COREFERENCE = "anaphoric_coreference"
    """A bare definite phrase pointing back at the one thing in the same
    paragraph it can point at. Where more than one candidate exists, nothing
    is recorded."""

    DEFINED_TERM = "defined_term"
    """The source gives a short name to something it has just described."""


class EndpointRole(str, Enum):
    ENTRY = "entry"
    ENUMERATION = "enumeration"
    WHOLE = "whole"
    PART = "part"
    NUMBERED_MEMBER = "numbered_member"
    ANAPHOR = "anaphor"
    ANTECEDENT = "antecedent"
    TERM = "term"
    REFERENT = "referent"


class Direction(str, Enum):
    """Which way the source's statement runs. Reversing it would misreport."""

    ENTRY_TO_ENUMERATION = "entry_to_enumeration"
    WHOLE_TO_PART = "whole_to_part"
    ANAPHOR_TO_ANTECEDENT = "anaphor_to_antecedent"
    TERM_TO_REFERENT = "term_to_referent"
    NONE = "none"
    """The source names only one end -- an ordinal with no stated counterpart."""


class ContextForm(str, Enum):
    BULLETED_LIST = "bulleted_list"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"


@dataclass(frozen=True)
class SourceParagraph:
    """A paragraph as the filing's own parser produced it."""

    issuer: str
    accession: str
    section: str
    ordinal: int
    text: str
    period: str | None = None


@dataclass(frozen=True)
class SourceSpan:
    """Where the words are. A later layer joins to other read models by this,
    not by comparing strings."""

    issuer: str
    accession: str
    section: str
    paragraph_ordinal: int


@dataclass(frozen=True)
class RelationshipEndpoint:
    surface: str
    """The source's words, verbatim and unbounded by any parsing of ours. A
    phrase we trimmed is a phrase a later layer cannot check."""
    role: EndpointRole
    span: SourceSpan


@dataclass(frozen=True)
class StructuralContext:
    """The structure that licensed the record, kept because it is the evidence
    -- a bullet is only an entry of a list while its lead-in is known."""

    form: ContextForm
    lead_in: str | None
    connective: str | None
    """The exact words that carry the relationship: "consisting of", "the"."""


@dataclass(frozen=True)
class ProjectRelationshipEvidence:
    kind: RelationshipKind
    left: RelationshipEndpoint
    right: RelationshipEndpoint | None
    """None when the source states one end only."""
    direction: Direction
    licensing_surface: str
    """The clause that states the relationship, verbatim."""
    context: StructuralContext
    source_period: str | None
    version: str = PROJECT_RELATIONSHIP_VERSION

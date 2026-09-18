"""Whether two entity references denote the same real-world thing.

Sprint 14 gave the strategy graph the names management used -- Comanche
Peak, Permian, West Texas, Texas Energy Fund, PJM. Sprint 12 gave the
evidence layer the names filers tag facts with --
`vistra:ComanchePeakNuclearPowerPlantMember`, `vistra:TexasSegmentMember`,
`vistra:PJMMidAtlanticMember`. The attribution shadow stayed at zero
because nothing licenses Atlas to say a name on one side is the thing
named on the other.

**Candidate generation and proof are different operations, and the
separation is the whole design.** Lowercasing, punctuation stripping,
CamelCase expansion, token containment, acronym relations and edit
distance may all say "look at this pair". None of them may say "these
are the same". A signal is recorded on the claim so a reader can see
what drew attention, and it never appears as a basis.

**What can prove identity here.** One thing, so far: a filer declares a
human-readable label for the element it invented, in the taxonomy that
accompanies the filing. `abvolvo_FinancialServicesMember` is labelled
"Financial Services (member)" by Volvo, not by Atlas. That is identity
between a QName and a name, established by the source.

It is also why Volvo's two elements stay two things:
`abvolvo_FinancialServciesMember` is separately declared and separately
labelled "Financial Servcies (member)", typo and all. A rule that
merged them on spelling would contradict the document.

**What cannot.** Same issuer, same period, same location, same
megawatts, same entity kind, a shared word, a shared prefix, an
acronym, a normalized string. Several of those together are still
several of those. A relationship is not an identity: a project at a
facility is not the facility, a facility in a segment is not the
segment, a plant in a market is not the market.

**UNRESOLVED is not a failure mode, it is the common answer**, and it
is kept distinct from NOT_SAME: having no proof that two things are the
same is not proof that they differ.
"""
from __future__ import annotations

from enum import Enum

__all__ = ["IdentityStatus", "IdentityBasis", "ReferenceKind", "CandidateSignal"]


class ReferenceKind(str, Enum):
    """Where a reference came from. Kept because what a reference *is*
    constrains what could ever prove things about it."""

    STRATEGY_MENTION = "strategy_mention"
    """A name management used, from Sprint 14."""
    DIMENSIONAL_MEMBER = "dimensional_member"
    """An axis member QName a filer tagged facts with."""
    TAXONOMY_LABEL = "taxonomy_label"
    """A human-readable name the filer declared for one of its own
    elements, read from the label linkbase that ships with the filing."""


class CandidateSignal(str, Enum):
    """Reasons to look at a pair. Never reasons to accept one.

    Every member here is a string operation, which is exactly why none
    of them is an `IdentityBasis`."""

    EXACT_STRING = "exact_string"
    CASE_FOLDED = "case_folded"
    PUNCTUATION_NORMALIZED = "punctuation_normalized"
    CAMEL_CASE_EXPANDED = "camel_case_expanded"
    TOKEN_CONTAINMENT = "token_containment"
    ACRONYM = "acronym"
    SAME_ISSUER = "same_issuer"


class IdentityBasis(str, Enum):
    """What actually proved it.

    One member earned. The others considered and refused: same issuer,
    same period, same location, same capacity, same kind, and every
    string relation -- each of which can hold between two different
    things."""

    TAXONOMY_LABEL = "taxonomy_label"
    """The filer's own declared label for its own element, from the
    label linkbase in the filing's taxonomy. Identity between a QName
    and a name, asserted by the source rather than inferred."""


class IdentityStatus(str, Enum):
    SAME = "same"
    """Evidence establishes one real-world object."""
    NOT_SAME = "not_same"
    """Evidence establishes two. A filer declaring both elements
    separately is the case that arises here."""
    AMBIGUOUS = "ambiguous"
    """Evidence points at more than one target, or two pieces conflict.
    The alternatives are reported; the choice is not made."""
    UNRESOLVED = "unresolved"
    """No evidence either way. The common answer, and distinct from
    NOT_SAME: absence of proof is not proof of difference."""

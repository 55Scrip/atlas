"""Building identity claims, and refusing to build most of them."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from atlas.analysis_engine.entity_identity.contracts import (
    CandidateSignal,
    IdentityBasis,
    IdentityStatus,
    ReferenceKind,
)

__all__ = [
    "ENTITY_IDENTITY_VERSION",
    "EntityReference",
    "IdentityEvidence",
    "IdentityClaim",
    "candidate_signals",
    "resolve_identity",
    "build_identity_claims",
]

ENTITY_IDENTITY_VERSION = "entity-identity-1"


@dataclass(frozen=True)
class EntityReference:
    """A pointer to a name somebody else owns.

    Deliberately not a copy of the referent: the strategy mention still
    belongs to Sprint 14, the member still belongs to the dimensional
    store, and this layer adds a claim about them rather than a second
    record of them."""

    kind: ReferenceKind
    value: str
    """The name exactly as its owner holds it -- surface text for a
    mention, QName for a member, label text for a label."""
    issuer: str
    """Canonical issuer scope. Comparisons never cross it: "US",
    "Cloud", "West" and "Platform" mean different things at different
    companies, and a global namespace would make that invisible."""
    source_locator: str = ""
    period: str | None = None
    element_qname: str | None = None
    """For a taxonomy label, the element the filer attached it to."""


@dataclass(frozen=True)
class IdentityEvidence:
    basis: IdentityBasis
    source_locator: str
    detail: str
    """What the source actually says, quoted rather than summarised."""


@dataclass(frozen=True)
class IdentityClaim:
    left: EntityReference
    right: EntityReference
    status: IdentityStatus
    issuer_scope: str
    signals: tuple[CandidateSignal, ...] = ()
    """Why the pair was inspected. Never why it was accepted."""
    supporting: tuple[IdentityEvidence, ...] = ()
    contradictory: tuple[IdentityEvidence, ...] = ()
    alternatives: tuple[str, ...] = ()
    """Other references the evidence points at, when more than one does."""
    temporal_scope: str | None = None
    reason: str = ""

    @property
    def basis(self) -> IdentityBasis | None:
        return self.supporting[0].basis if self.supporting else None

    @property
    def may_conclude(self) -> str:
        if self.status is IdentityStatus.SAME:
            return (f"{self.left.value!r} and {self.right.value!r} denote one object "
                    f"for issuer {self.issuer_scope}, on the source's own statement")
        if self.status is IdentityStatus.NOT_SAME:
            return f"{self.left.value!r} and {self.right.value!r} denote different objects"
        if self.status is IdentityStatus.AMBIGUOUS:
            return "the evidence points at more than one target; Atlas does not choose"
        return "nothing about whether these are the same thing"

    @property
    def may_not_conclude(self) -> str:
        shared = ("that either reference can be substituted for the other in an "
                  "attribution without also satisfying that layer's own measure, "
                  "period and resolution rules")
        if self.status is IdentityStatus.UNRESOLVED:
            return ("that they are different -- no evidence was found either way; " + shared)
        return shared


_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
_PUNCT = re.compile(r"[^\w\s]")
_TRAILING = ("member", "axis", "domain")


def _local(value: str) -> str:
    return value.split(":")[-1].split("_")[-1] if ":" in value or "_" in value else value


def _expand(value: str) -> str:
    words = _CAMEL.sub(" ", _local(value)).split()
    while words and words[-1].casefold() in _TRAILING:
        words.pop()
    return " ".join(words)


def _normalise(value: str) -> str:
    return " ".join(_PUNCT.sub(" ", value).split()).casefold()


def _normalised_forms(value: str) -> set[str]:
    """Both readings of punctuation: as a separator and as noise.

    "U.S." is "u s" under one and "us" under the other, and a caller
    looking for "US" wants the second. Widening a *signal* costs
    nothing, because a signal can only decide whether to look."""
    return {_normalise(value), _PUNCT.sub("", value).casefold()}


def _acronym_of(value: str) -> str:
    return "".join(w[0] for w in _expand(value).split() if w).upper()


def candidate_signals(left: EntityReference, right: EntityReference) -> tuple[CandidateSignal, ...]:
    """Why this pair is worth inspecting.

    Returns signals and never a status. Every rule below is a string
    operation, which is the reason none of them can appear as an
    `IdentityBasis`: `West Texas` and `Texas` share a token, `PJM` is an
    acronym of `PJM Mid Atlantic`, and neither fact says anything about
    the world.
    """
    out: list[CandidateSignal] = []
    if left.issuer and left.issuer == right.issuer:
        out.append(CandidateSignal.SAME_ISSUER)
    a, b = left.value, right.value
    if a == b:
        out.append(CandidateSignal.EXACT_STRING)
    elif a.casefold() == b.casefold():
        out.append(CandidateSignal.CASE_FOLDED)
    if (_normalised_forms(a) & _normalised_forms(b)) and a.casefold() != b.casefold():
        out.append(CandidateSignal.PUNCTUATION_NORMALIZED)
    expanded_a, expanded_b = _expand(a), _expand(b)
    if _normalise(expanded_a) == _normalise(expanded_b) and a != b:
        out.append(CandidateSignal.CAMEL_CASE_EXPANDED)
    tokens_a = set(_normalise(expanded_a).split())
    tokens_b = set(_normalise(expanded_b).split())
    if tokens_a and tokens_b and (tokens_a <= tokens_b or tokens_b <= tokens_a) and tokens_a != tokens_b:
        out.append(CandidateSignal.TOKEN_CONTAINMENT)
    if a.isupper() and len(a) > 1 and _acronym_of(b) == a:
        out.append(CandidateSignal.ACRONYM)
    elif b.isupper() and len(b) > 1 and _acronym_of(a) == b:
        out.append(CandidateSignal.ACRONYM)
    return tuple(dict.fromkeys(out))


def resolve_identity(
    left: EntityReference,
    right: EntityReference,
    *,
    declared_labels: "dict[str, str] | None" = None,
) -> IdentityClaim:
    """One claim about one pair.

    `declared_labels` maps an element QName to the label its filer
    declared for it, read from the label linkbase that ships with the
    filing. It is the only evidence this function accepts, and it is
    passed in rather than fetched: proof must come from a source Atlas
    holds, never from this module's own opinion.
    """
    signals = candidate_signals(left, right)
    labels = declared_labels or {}
    base = dict(left=left, right=right, issuer_scope=left.issuer, signals=signals)

    if left.issuer != right.issuer:
        return IdentityClaim(**{**base, "issuer_scope": f"{left.issuer}|{right.issuer}"},
                             status=IdentityStatus.UNRESOLVED,
                             reason="different issuers; identity is issuer-scoped and this pair "
                                    "was not compared")

    # A relationship between two members is not an identity, and two
    # separately declared elements are two things -- the strongest
    # NOT_SAME available, because the filer said so by declaring both.
    if (left.kind is ReferenceKind.DIMENSIONAL_MEMBER
            and right.kind is ReferenceKind.DIMENSIONAL_MEMBER
            and left.value != right.value
            and left.value in labels and right.value in labels):
        return IdentityClaim(
            **base, status=IdentityStatus.NOT_SAME,
            contradictory=(IdentityEvidence(
                basis=IdentityBasis.TAXONOMY_LABEL, source_locator=left.source_locator,
                detail=f"the filer declares {left.value} as {labels[left.value]!r} and "
                       f"{right.value} as {labels[right.value]!r}: two elements, two labels"),),
            reason="both elements are separately declared by the filer")

    # The one basis the corpus earns: a filer's own label for its own
    # element, matched against a reference that IS that label.
    member, other = None, None
    if left.kind is ReferenceKind.DIMENSIONAL_MEMBER:
        member, other = left, right
    elif right.kind is ReferenceKind.DIMENSIONAL_MEMBER:
        member, other = right, left
    if member is not None and other is not None and other.kind is ReferenceKind.TAXONOMY_LABEL:
        declared = labels.get(member.value)
        if declared is None:
            return IdentityClaim(**base, status=IdentityStatus.UNRESOLVED,
                                 reason=f"no declared label is held for {member.value}")
        if _normalise(declared) == _normalise(other.value):
            matches = [q for q, text in labels.items() if _normalise(text) == _normalise(other.value)]
            if len(matches) > 1:
                return IdentityClaim(**base, status=IdentityStatus.AMBIGUOUS,
                                     alternatives=tuple(sorted(matches)),
                                     reason="the filer gives this label to more than one element")
            return IdentityClaim(
                **base, status=IdentityStatus.SAME,
                supporting=(IdentityEvidence(
                    basis=IdentityBasis.TAXONOMY_LABEL, source_locator=member.source_locator,
                    detail=f"the filer declares {member.value} with the label {declared!r}"),),
                temporal_scope=member.period,
                reason="the source names its own element")
        return IdentityClaim(
            **base, status=IdentityStatus.NOT_SAME,
            contradictory=(IdentityEvidence(
                basis=IdentityBasis.TAXONOMY_LABEL, source_locator=member.source_locator,
                detail=f"the filer declares {member.value} as {declared!r}, "
                       f"not {other.value!r}"),),
            reason="the declared label is a different name")

    # Everything else. The signals above are recorded and refused: a
    # shared token, an acronym, a normalized match and a shared issuer
    # are reasons to have looked, and no source has spoken.
    return IdentityClaim(
        **base, status=IdentityStatus.UNRESOLVED,
        reason="no source evidence connects these references; "
               f"inspected because of {[s.value for s in signals] or 'an explicit request'}")


def build_identity_claims(
    left_references: "list[EntityReference]",
    right_references: "list[EntityReference]",
    *,
    declared_labels: "dict[str, str] | None" = None,
) -> tuple[IdentityClaim, ...]:
    """Every pair worth inspecting, resolved.

    A pair reaches `resolve_identity` only when a signal suggests it or
    a label is held for it, so this is a bounded inspection rather than
    a cross product -- and the outcome of each pair is unaffected by
    how it was reached.
    """
    claims: list[IdentityClaim] = []
    seen: set[tuple[str, str, str]] = set()
    for left in left_references:
        for right in right_references:
            if left.issuer != right.issuer:
                continue
            key = (left.kind.value + "|" + left.value, right.kind.value + "|" + right.value,
                   left.issuer)
            if key in seen:
                continue
            signals = candidate_signals(left, right)
            informative = [s for s in signals if s is not CandidateSignal.SAME_ISSUER]
            if not informative and (declared_labels or {}).get(right.value) is None:
                continue
            seen.add(key)
            claims.append(resolve_identity(left, right, declared_labels=declared_labels))
    return tuple(claims)

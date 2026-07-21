"""Domain errors for the Knowledge Reference aggregate (DO-IMP-003).

**Corrected per docs/atlas_domain_object_architecture/
Knowledge-Reference-Pre-Commit-Architecture-Review.md, Outcome 2.**

Structural validity of the target reference itself (an unknown or
non-canonical target type, a malformed target id) is governed entirely
by the shared `atlas.core.domain.shared` module, which raises its own
`UnknownDomainObjectTypeError` / `InvalidTypedDomainObjectReferenceError`
directly — never duplicated here. That responsibility answers exactly
one question: is this a member of `DomainObjectType` at all? All six
adopted values (Observation, Knowledge Reference, Reasoning Trace,
Judgment, Decision, Outcome) answer yes to that question — every one of
them remains a canonically reference-eligible Domain Object type
(OE-002 §5.2: "No specific Domain Object type is required as its
target; the target's type is unrestricted by this document").

The errors below answer a different question entirely: given a
structurally valid, canonical target type, can Knowledge Reference
*capture* currently establish every invariant OE-006 §16 requires
acceptance to establish for it? OE-006 §9 recognizes no "accepted with
a deferred invariant" status — a candidate whose applicable invariant
cannot currently be established must be rejected, not accepted with a
gap. `TargetTypeUnavailableError` names exactly this condition, and its
own name and documentation deliberately avoid any suggestion that the
rejected type is unknown, invalid, or non-adopted — it is none of
those; it is temporarily unavailable for this specific capture
operation, for reasons stated per-type where it is raised (see
`atlas/core/application/knowledge_reference/
capture_knowledge_reference.py`).
"""

from __future__ import annotations


class KnowledgeReferenceError(Exception):
    """Base class for all Knowledge Reference domain errors."""


class KnowledgeReferenceNotFoundError(KnowledgeReferenceError):
    """Raised when a requested Knowledge Reference does not exist."""


class TargetNotFoundError(KnowledgeReferenceError):
    """Raised when a target of an implemented, currently capture-enabled
    type does not exist, or has not yet been accepted, in that type's own
    repository (INV-005). Today this can be raised for any of the six
    adopted types — Observation, Knowledge Reference, Judgment, Decision,
    Outcome, or Reasoning Trace.
    """


class CrossCaseTargetError(KnowledgeReferenceError):
    """Raised when a target of an implemented, currently capture-enabled
    type is verified to belong to a different Case than the capturing
    Knowledge Reference (INV-004). Today this can be raised for any of
    the six adopted types — Observation, Knowledge Reference, Judgment,
    Decision, Outcome, or Reasoning Trace.
    """


class TargetTypeUnavailableError(KnowledgeReferenceError):
    """Raised when the target type is a fully adopted, canonical
    `DomainObjectType` member, but Knowledge Reference capture cannot
    currently establish every invariant OE-006 §16 requires acceptance
    to establish for it.

    This is **not** a claim that the target type is unknown, invalid,
    or non-adopted — every `DomainObjectType` member remains a
    canonical, reference-eligible Domain Object (OE-002 §5.2). It is a
    claim about present *capture availability* only, kept for
    structural symmetry with the currently-enabled-set check: as of
    Reasoning Trace's own package (DO-IMP-009) and this availability
    widening, every one of the six adopted types now has both a
    working, accepted-instance repository and same-Case membership
    positively establishable, so this exception is not presently
    reachable for any adopted type.
    """

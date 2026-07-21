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
    repository (INV-005). Today this can be raised for an Observation,
    Knowledge Reference, Judgment, Decision, or Outcome target — every
    currently capture-enabled type except Reasoning Trace, which has no
    accepted-instance repository at all.
    """


class CrossCaseTargetError(KnowledgeReferenceError):
    """Raised when a target of an implemented, currently capture-enabled
    type is verified to belong to a different Case than the capturing
    Knowledge Reference (INV-004). Today this can be raised for an
    Observation, Knowledge Reference, Judgment, Decision, or Outcome
    target — every currently capture-enabled type.
    """


class TargetTypeUnavailableError(KnowledgeReferenceError):
    """Raised when the target type is a fully adopted, canonical
    `DomainObjectType` member, but Knowledge Reference capture cannot
    currently establish every invariant OE-006 §16 requires acceptance
    to establish for it.

    This is **not** a claim that the target type is unknown, invalid,
    or non-adopted — every `DomainObjectType` member remains a
    canonical, reference-eligible Domain Object (OE-002 §5.2). It is a
    claim about present *capture availability* only: canonical target
    eligibility and present capture availability are distinct facts,
    and this exception concerns exclusively the latter. Capture for
    each affected type becomes available once its own prerequisite
    implementation or reconciliation work lands — no change to
    Knowledge Reference's own schema or API contract is required when
    it does (see the review document cited above, §10).
    """

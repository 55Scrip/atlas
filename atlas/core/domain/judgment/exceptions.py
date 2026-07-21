"""Domain errors for the Judgment aggregate (DO-IMP-004).

Structural validity of a subject reference itself (an unknown or
non-canonical target type, a malformed target id) is governed entirely
by the shared `atlas.core.domain.shared` module, which raises its own
`UnknownDomainObjectTypeError` / `InvalidTypedDomainObjectReferenceError`
directly — never duplicated here.

The referential-validation error taxonomy below mirrors the one
corrected for Knowledge Reference (see
docs/atlas_domain_object_architecture/Knowledge-Reference-Pre-Commit-Architecture-Review.md,
Outcome 2): OE-006 §9 recognizes no "accepted with a deferred invariant"
status, so a subject reference whose applicable invariant (INV-004
same-Case, INV-005 prior acceptance) cannot currently be positively
established is rejected, not admitted with a gap.
"""

from __future__ import annotations


class JudgmentError(Exception):
    """Base class for all Judgment domain errors."""


class MissingCharacterizationError(JudgmentError):
    """Raised when a Judgment's characterization is missing or blank."""


class JudgmentNotFoundError(JudgmentError):
    """Raised when a requested Judgment does not exist."""


class TargetNotFoundError(JudgmentError):
    """Raised when a subject reference of a currently capture-enabled
    type does not exist, or has not yet been accepted, in that type's
    own repository (INV-005). Today this can be raised for a Knowledge
    Reference, Judgment, Observation, Decision, or Outcome subject —
    every currently capture-enabled type except Reasoning Trace, which
    has no accepted-instance repository at all.
    """


class CrossCaseTargetError(JudgmentError):
    """Raised when a subject reference of a currently capture-enabled
    type is verified to belong to a different Case than the capturing
    Judgment (INV-004).
    """


class TargetTypeUnavailableError(JudgmentError):
    """Raised when the subject's target type is a fully adopted,
    canonical `DomainObjectType` member, but Judgment capture cannot
    currently establish every invariant OE-006 §16 requires acceptance
    to establish for it.

    This is **not** a claim that the target type is unknown, invalid,
    or non-adopted — every `DomainObjectType` member remains a
    canonical, reference-eligible Domain Object (OE-002 §5.4). It is a
    claim about present *capture availability* only: Reasoning Trace
    has no accepted-instance repository at all, so INV-005 is
    determinately violated, not merely unverifiable, for it — the only
    remaining canonical target type this currently applies to. Capture
    against it becomes available once its own prerequisite
    implementation lands — no change to Judgment's own schema or API
    contract is required when it does.
    """

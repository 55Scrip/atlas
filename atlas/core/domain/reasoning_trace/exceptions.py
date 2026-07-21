"""Domain errors for the Reasoning Trace aggregate (DO-IMP-009).

Per docs/atlas_domain_object_architecture/
Reasoning-Trace-Implementation-Design.md, Section 27: these four
exceptions are the complete set. No `TargetTypeUnavailableError`-
equivalent is defined here, unlike Knowledge Reference's own taxonomy —
Reasoning Trace is implemented last among the six adopted Domain Object
types, so every one of them (Observation, Knowledge Reference,
Reasoning Trace itself, Judgment, Decision, Outcome) already has a
working, accepted-instance repository and a `case_id` by the time this
package exists. There is no type for such a gate to exclude.
"""

from __future__ import annotations


class ReasoningTraceError(Exception):
    """Base class for all Reasoning Trace domain errors."""


class ReasoningTraceNotFoundError(ReasoningTraceError):
    """Raised when a requested Reasoning Trace does not exist."""


class EmptySupportError(ReasoningTraceError):
    """Raised when a candidate support collection is empty, violating
    INV-013's "at least one supporting Domain Object" requirement.

    Raised by `ReasoningTrace.__post_init__` on every construction path
    (both `.capture()` and ordinary persistence reconstruction), so
    non-emptiness is enforced structurally regardless of which path
    constructs an instance. The application layer also checks this
    first, before any repository call, and raises this same class
    directly rather than duplicating it.
    """


class TargetNotFoundError(ReasoningTraceError):
    """Raised when a supporting reference of any of the six adopted
    types does not exist, or has not yet been accepted, in that type's
    own repository (INV-005).
    """


class CrossCaseTargetError(ReasoningTraceError):
    """Raised when a supporting reference is verified to belong to a
    different Case than the capturing Reasoning Trace (INV-004).
    """

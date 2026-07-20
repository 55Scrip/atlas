"""Shared domain errors for typed Domain Object references (DO-IMP-002).

These errors concern only structural validity — whether a candidate
target type or identifier is well-formed at all. They say nothing about
whether a referenced target exists, has been accepted, or belongs to
the same Case as whatever object holds a reference to it: that
referential validation is deliberately deferred to each owning Domain
Object's own application-layer construction path (Knowledge Reference,
Reasoning Trace, Judgment, Decision, Outcome), per INV-004/INV-005, and
is out of this package's scope (DO-IMP-002).
"""
from __future__ import annotations


class TypedReferenceError(Exception):
    """Base class for shared typed-reference structural errors."""


class UnknownDomainObjectTypeError(TypedReferenceError):
    """Raised when a candidate target type is not one of the six adopted
    Domain Object types this package's DomainObjectType enum admits.
    """


class InvalidTypedDomainObjectReferenceError(TypedReferenceError):
    """Raised when a TypedDomainObjectReference is constructed with a
    malformed target_type or target_id.
    """

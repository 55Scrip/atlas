"""Exceptions for `atlas.analysis_engine.business_data`'s own contract
violations. Mirrors `atlas.analysis_engine.exceptions` and
`atlas.decision_engine.exceptions`'s identical discipline: these
represent only an actual contract violation -- a malformed
`RawBusinessDocument` is never an exception, it is a typed
`ValidationRejection` (see `validation.py`), the same "ordinary
incompleteness is a typed result, not a raised error" rule this
codebase applies everywhere else.
"""
from __future__ import annotations


class BusinessDataError(Exception):
    """Base class for all Business Data errors."""


class BusinessDataContractError(BusinessDataError, ValueError):
    """A Business Data contract type was constructed in a way its own
    invariants forbid -- for example, a `RecordVersion` with a
    `version_number` below 1."""

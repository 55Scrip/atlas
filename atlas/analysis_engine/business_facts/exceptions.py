"""Exceptions for `atlas.analysis_engine.business_facts`'s own contract
violations. Mirrors `atlas.analysis_engine.business_data.exceptions`'s
identical discipline: these represent only an actual contract
violation -- ordinary extraction incompleteness (a metadata key
missing, a value of the wrong type, conflicting facts for the same
period) is never an exception, it is simply the absence of a
`BusinessFact` (see `extraction.py`'s own module docstring).
"""
from __future__ import annotations


class BusinessFactError(Exception):
    """Base class for all Business Fact errors."""


class BusinessFactContractError(BusinessFactError, ValueError):
    """A Business Fact contract type was constructed in a way its own
    invariants forbid."""

"""Exceptions for `atlas.analysis_engine.valuation`'s own contract
violations. Mirrors `atlas.analysis_engine.business_facts.exceptions`
and `atlas.analysis_engine.exceptions`'s identical discipline: ordinary
valuation incompleteness (a missing fact, a stale price, an
uncomputable signal) is never an exception -- it is a typed
`INSUFFICIENT_INPUT` result with a named reason, never raised.
"""
from __future__ import annotations


class ValuationEngineError(Exception):
    """Base class for all Valuation Engine errors."""


class ValuationEngineContractError(ValuationEngineError, ValueError):
    """A Valuation Engine contract type was constructed in a way its
    own invariants forbid."""

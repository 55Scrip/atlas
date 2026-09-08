from __future__ import annotations

__all__ = ["CaseInstrumentBindingError", "ConflictingCaseInstrumentBindingError"]


class CaseInstrumentBindingError(Exception):
    """Base for every binding-integrity failure."""


class ConflictingCaseInstrumentBindingError(CaseInstrumentBindingError):
    """Raised when a Case would be bound to a second, different
    instrument, or when a backfill finds one Case associated with two
    different securities.

    Deliberately loud. The whole point of moving identity out of
    membership is that Atlas stops guessing which company a Case is
    about; silently preferring Portfolio over Watchlist here would
    reintroduce the guess in a new place.
    """

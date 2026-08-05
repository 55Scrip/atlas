"""Data model for Atlas Alpha's provisional portfolio state.

See `atlas/alpha/portfolio/__init__.py` for this module's explicit
architectural boundary. Sprint 1A scope only: no trade log, no
reconciliation status — those are Sprint 1B additions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EntryMode(str, Enum):
    """How this Alpha portfolio state was established."""

    IMPORTED = "IMPORTED"
    FROM_SCRATCH = "FROM_SCRATCH"


@dataclass(frozen=True)
class AlphaHolding:
    """One investor-supplied holding line within the provisional state.

    `weight_percent` is the only field the manual existing-portfolio
    entry flow genuinely requires; `value_absolute` is optional, matching
    the Alpha First-Time Experience requirement that percentages alone
    must be sufficient.
    """

    ticker: str
    weight_percent: float
    value_absolute: float | None = None

    def __post_init__(self) -> None:
        if not self.ticker or not self.ticker.strip():
            raise ValueError("AlphaHolding.ticker must not be blank")
        if self.weight_percent < 0:
            raise ValueError("AlphaHolding.weight_percent must not be negative")
        if self.value_absolute is not None and self.value_absolute < 0:
            raise ValueError("AlphaHolding.value_absolute must not be negative")
        object.__setattr__(self, "ticker", self.ticker.strip().upper())


@dataclass(frozen=True)
class AlphaPreferences:
    """Optional investor preferences captured at entry time.

    Every field is optional (Alpha Sprint 1 requirement: "optional
    preferences" on both the existing-portfolio and from-scratch paths).
    Sprint 1A stores this as context only — no field here is read by any
    calculation.
    """

    notes: str | None = None


@dataclass(frozen=True)
class AlphaPortfolioState:
    """The single, process-wide provisional Alpha portfolio record.

    Singleton by design (no `id` field of its own): Atlas Alpha has no
    investor identity or session system yet (explicitly deferred), so
    exactly one state exists per running Atlas Alpha instance — the same
    singleton pattern `atlas.core.domain.investor_identity.InvestorIdentity`
    already established ("resolved as the one this data store has, if
    any").
    """

    established_at: datetime
    updated_at: datetime
    entry_mode: EntryMode
    holdings: tuple[AlphaHolding, ...] = ()
    cash_weight_percent: float | None = None
    cash_value_absolute: float | None = None
    objective: str | None = None
    horizon: str | None = None
    preferences: AlphaPreferences = field(default_factory=AlphaPreferences)

    @property
    def has_absolute_values(self) -> bool:
        """True only if every holding, and cash, carries an absolute value.

        Sprint 1B reads this to decide whether a confirmed trade may
        safely update allocation percentages automatically, or must be
        recorded without touching them (Alpha Sprint 1, Phase 4 revised
        plan, Decision 2). Computed, never stored, so it can never drift
        from the holdings it describes.
        """
        if any(holding.value_absolute is None for holding in self.holdings):
            return False
        return self.cash_value_absolute is not None

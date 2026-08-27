"""Data model for Atlas Alpha's provisional portfolio state.

See `atlas/alpha/portfolio/__init__.py` for this module's explicit
architectural boundary. Sprint 1B adds `AlphaTradeLogEntry` (external
trade recording) and `ReconciliationStatus` (portfolio reconciliation)
-- both remain provisional Alpha state; no Core entity is modified.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EntryMode(str, Enum):
    """How this Alpha portfolio state was established."""

    IMPORTED = "IMPORTED"
    FROM_SCRATCH = "FROM_SCRATCH"


class ReconciliationStatus(str, Enum):
    """A holding's status relative to the most recently applied trade.

    `NONE` is the default -- either never touched by a trade, or already
    cleanly reconciled. `UPDATED` means a confirmed trade updated this
    holding automatically (absolute-value mode). `AWAITING_RECONCILIATION`
    means a trade was recorded against this holding but its allocation
    percentage was deliberately left untouched (percentage-only mode) --
    Atlas does not invent the remainder (Alpha Sprint 1B, Mode B).
    """

    NONE = "NONE"
    UPDATED = "UPDATED"
    AWAITING_RECONCILIATION = "AWAITING_RECONCILIATION"


class TransactionType(str, Enum):
    """The external-execution kinds Atlas records (Atlas never trades).

    `ADD` is recorded and behaves identically to `BUY` throughout this
    module -- a separate label for "added to an existing position" with
    no distinct math, since Alpha has no cost-basis/lot tracking to make
    the two behave differently. `EXIT` marks a position fully closed: it
    removes the holding from the active portfolio outright (ATLAS-014),
    rather than reducing it the way `SELL` does -- see
    `service.py::_apply_trade_exit_mode`.
    """

    BUY = "BUY"
    SELL = "SELL"
    ADD = "ADD"
    EXIT = "EXIT"


@dataclass(frozen=True)
class AlphaHolding:
    """One investor-supplied holding line within the provisional state.

    `weight_percent` is always present on this stored shape -- every
    existing reader may keep assuming a real float -- but as of Zero-
    Effort Portfolio Onboarding it is a derived value whenever `quantity`
    and `price` (or `value_absolute`) are known; it is only ever taken
    literally from investor input in the manual-entry fallback, where no
    value data exists to derive it from. `quantity`/`price`/`currency`
    are optional: present when the source (a broker export, or a BUY/SELL
    report) supplied them, absent for pre-existing weight-only holdings.

    `case_id` is the Sprint 1A Foundation Patch's holding-to-Investment-
    Case association: once the investor opens an Investment Case from
    this holding, the Core Case's id is recorded here so a later "Open
    Investment Case" click reuses it instead of creating a new Case. It
    is Alpha-provisional bookkeeping only -- no field is added to Core's
    own Case object to hold this association (Alpha Sprint 1 Phase 4,
    Decision A: Alpha never adds Core-shaped state to Core).
    """

    ticker: str
    weight_percent: float
    value_absolute: float | None = None
    quantity: float | None = None
    price: float | None = None
    currency: str | None = None
    case_id: str | None = None
    reconciliation_status: ReconciliationStatus = ReconciliationStatus.NONE

    def __post_init__(self) -> None:
        if not self.ticker or not self.ticker.strip():
            raise ValueError("AlphaHolding.ticker must not be blank")
        if self.weight_percent < 0:
            raise ValueError("AlphaHolding.weight_percent must not be negative")
        if self.weight_percent > 100:
            raise ValueError("AlphaHolding.weight_percent must not exceed 100")
        if self.value_absolute is not None and self.value_absolute < 0:
            raise ValueError("AlphaHolding.value_absolute must not be negative")
        if self.quantity is not None and self.quantity <= 0:
            raise ValueError("AlphaHolding.quantity must be positive")
        if self.price is not None and self.price <= 0:
            raise ValueError("AlphaHolding.price must be positive")
        object.__setattr__(self, "ticker", self.ticker.strip().upper())
        if self.currency is not None:
            object.__setattr__(self, "currency", self.currency.strip().upper() or None)


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


@dataclass(frozen=True)
class AlphaTradeLogEntry:
    """A confirmed external trade execution, provisional Alpha bookkeeping.

    References an existing, immutable Core Outcome by id (`outcome_id`)
    and the Decision it followed from (`decision_id`) -- both plain
    string references, matching the rest of this codebase's convention
    (no SQL foreign key). Outcome itself is never modified and never
    references this entry back (Alpha Sprint 1B: "Outcome must never
    reference Alpha"). `outcome_id` is unique: at most one trade log
    entry exists per Outcome (enforced by the store's primary key).
    """

    outcome_id: str
    decision_id: str
    security: str
    transaction_type: TransactionType
    quantity: float
    execution_price: float
    executed_at: datetime
    fees: float | None = None

    def __post_init__(self) -> None:
        if not self.outcome_id or not self.outcome_id.strip():
            raise ValueError("AlphaTradeLogEntry.outcome_id must not be blank")
        if not self.decision_id or not self.decision_id.strip():
            raise ValueError("AlphaTradeLogEntry.decision_id must not be blank")
        if not self.security or not self.security.strip():
            raise ValueError("AlphaTradeLogEntry.security must not be blank")
        if self.quantity <= 0:
            raise ValueError("AlphaTradeLogEntry.quantity must be positive")
        if self.execution_price <= 0:
            raise ValueError("AlphaTradeLogEntry.execution_price must be positive")
        if self.fees is not None and self.fees < 0:
            raise ValueError("AlphaTradeLogEntry.fees must not be negative")
        if self.executed_at.tzinfo is None:
            raise ValueError("AlphaTradeLogEntry.executed_at must be timezone-aware")
        object.__setattr__(self, "security", self.security.strip().upper())

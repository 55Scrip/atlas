"""Persisted provider availability state (Provider & Quota Intelligence).

Exists because a *consumption counter* was used as an *availability
oracle*. `AlphaVantageQuotaTracker` stores one row per UTC calendar
date, so a new UTC day has no row, `calls_used_today()` returns 0 and
`has_budget()` returns `True` -- by construction, not by evidence. On
2026-09-01 Atlas read a fresh 0/25 budget at 00:05 UTC and Alpha Vantage
rejected the very first call with an explicit daily-limit payload; 16
consecutive calls were then spent, every one rejected.

The rule this module encodes:

    The local counter is a lower bound on *consumption*, and therefore
    only an upper bound on *availability*. It can prove Atlas should
    NOT call. It can never prove Atlas MAY call.

So `has_budget() == True` means "not known to be exhausted", never
"budget confirmed available", and a provider's own rejection always
outranks local optimism -- including outranking a fresh UTC date, which
is precisely the case the counter alone got wrong.

**Provider-keyed, never Alpha-Vantage-specific.** State is stored per
provider name, so a second provider gets its own availability without
touching this one. Nothing in this module imports a provider adapter or
knows what Alpha Vantage is; callers pass their own name.

**Why a separate concept from `ProviderFailureClassification`.** That
enum answers "can this *ticker* ever succeed?" -- a per-company
question. This answers "can this *provider* be called at all right
now?" Neither substitutes for the other, so this is a genuinely new
axis rather than a duplicate lifecycle.

**The reset boundary is deliberately not encoded.** Alpha Vantage does
not publish when its daily allowance resets -- verified against its own
support and premium pages, and absent from third-party documentation
too. `DEFAULT_DAILY_COOLDOWN` below is therefore a deliberately
conservative *safety floor* chosen so Atlas stops burning calls, and is
explicitly **not** a claim about when the provider actually resets. The
protocol that discovers the real boundary (a single control call after
the cooldown, which either clears the state or extends it) is designed
but not implemented here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum

from sqlalchemy import Column, MetaData, String, Table, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

#: The one place Alpha Vantage is named in this package's state model.
#: A second provider adds a sibling constant; nothing here branches on
#: the value.
ALPHA_VANTAGE_PROVIDER_NAME = "ALPHA_VANTAGE"

__all__ = [
    "ALPHA_VANTAGE_PROVIDER_NAME",
    "ProviderAvailability",
    "ProviderAvailabilityRecord",
    "ProviderAvailabilityStore",
    "ProviderBudgetGate",
    "DEFAULT_DAILY_COOLDOWN",
    "DEFAULT_SHORT_TERM_COOLDOWN",
    "create_provider_availability_table",
    "provider_availability_table",
]

#: Conservative safety floor, NOT a claim about the provider's reset
#: boundary (see module docstring). Long enough that Atlas cannot burn a
#: day's allowance re-discovering the same rejection; short enough that a
#: genuine calendar-day reset is not missed by a wide margin.
DEFAULT_DAILY_COOLDOWN = timedelta(hours=6)

#: A pacing rejection is recoverable in seconds. Deliberately an order of
#: magnitude above the ~1 request/second the provider's own message asks
#: for, so a burst that already tripped the limit backs off properly
#: rather than immediately re-tripping it.
DEFAULT_SHORT_TERM_COOLDOWN = timedelta(seconds=60)

metadata = MetaData()

provider_availability_table = Table(
    "provider_availability_state",
    metadata,
    Column("provider_name", String, primary_key=True),
    Column("state", String, nullable=False),
    Column("observed_at", String, nullable=False),
    Column("reason", String, nullable=False),
)


def create_provider_availability_table(engine: Engine) -> None:
    sync_table_schema(engine, provider_availability_table)


class ProviderAvailability(str, Enum):
    """Whether a provider can be called right now, and on whose word.

    The three "blocked" members are deliberately distinct: they differ
    in how long the block should last and in what evidence produced it,
    and collapsing them is what this sprint exists to undo.
    """

    #: Nothing is currently known to block a call. Explicitly not a
    #: guarantee -- only the absence of a known obstacle.
    AVAILABLE = "available"
    #: Atlas's own counter is spent. Derived from local state alone; the
    #: provider has said nothing.
    LOCALLY_EXHAUSTED = "locally_exhausted"
    #: The provider asked us to slow down. Recoverable in seconds.
    PROVIDER_THROTTLED_SHORT_TERM = "provider_throttled_short_term"
    #: The provider confirmed its daily allowance is spent. The
    #: strongest signal available, and the one that must outrank local
    #: optimism.
    PROVIDER_DAILY_EXHAUSTED = "provider_daily_exhausted"
    #: Transport failure -- timeout, 5xx, unparseable body. Unrelated to
    #: budget.
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    #: No basis for any claim: no persisted state, no call yet made.
    #: Deliberately distinct from `AVAILABLE`.
    UNKNOWN = "unknown"


#: The states that mean "do not call", paired with how long that lasts.
#: A state absent from this mapping never blocks.
_COOLDOWN_BY_STATE: dict[ProviderAvailability, timedelta] = {
    ProviderAvailability.PROVIDER_DAILY_EXHAUSTED: DEFAULT_DAILY_COOLDOWN,
    ProviderAvailability.PROVIDER_THROTTLED_SHORT_TERM: DEFAULT_SHORT_TERM_COOLDOWN,
}


@dataclass(frozen=True)
class ProviderAvailabilityRecord:
    """One provider's last observed availability, always with the reason
    and the moment it was observed -- a state without its cause would
    reintroduce exactly the "one word meaning several things" problem
    this sprint removes."""

    provider_name: str
    state: ProviderAvailability
    observed_at: datetime
    reason: str

    def is_blocking(self, *, now: datetime, cooldowns: dict | None = None) -> bool:
        """`True` while this record still forbids a call. Pure: the same
        record and the same `now` always give the same answer."""
        table = _COOLDOWN_BY_STATE if cooldowns is None else cooldowns
        cooldown = table.get(self.state)
        if cooldown is None:
            return False
        return now < self.observed_at + cooldown

    def blocked_until(self, *, cooldowns: dict | None = None) -> datetime | None:
        table = _COOLDOWN_BY_STATE if cooldowns is None else cooldowns
        cooldown = table.get(self.state)
        return None if cooldown is None else self.observed_at + cooldown


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


class ProviderAvailabilityStore:
    """Persisted so a confirmed provider rejection survives the frequent
    dev-server restarts this project already has -- an in-memory block
    would be forgotten on restart and the next process would cheerfully
    burn the allowance again, which is the exact failure being fixed."""

    def __init__(self, engine: Engine) -> None:
        create_provider_availability_table(engine)
        self._engine = engine

    def get(self, provider_name: str) -> ProviderAvailabilityRecord | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                select(
                    provider_availability_table.c.state,
                    provider_availability_table.c.observed_at,
                    provider_availability_table.c.reason,
                ).where(provider_availability_table.c.provider_name == provider_name)
            ).first()
        if row is None:
            return None
        return ProviderAvailabilityRecord(
            provider_name=provider_name,
            state=ProviderAvailability(row[0]),
            observed_at=_parse(row[1]),
            reason=row[2],
        )

    def record(
        self,
        provider_name: str,
        state: ProviderAvailability,
        *,
        reason: str,
        observed_at: datetime | None = None,
    ) -> ProviderAvailabilityRecord:
        moment = observed_at or _utc_now()
        statement = sqlite_insert(provider_availability_table).values(
            provider_name=provider_name,
            state=state.value,
            observed_at=moment.isoformat(),
            reason=reason,
        )
        statement = statement.on_conflict_do_update(
            index_elements=[provider_availability_table.c.provider_name],
            set_={"state": state.value, "observed_at": moment.isoformat(), "reason": reason},
        )
        with self._engine.begin() as connection:
            connection.execute(statement)
        return ProviderAvailabilityRecord(
            provider_name=provider_name, state=state, observed_at=moment, reason=reason
        )

    def clear(self, provider_name: str) -> None:
        """Records `AVAILABLE` rather than deleting the row, so "we
        checked and it was fine" stays distinguishable from "we have
        never checked" (`UNKNOWN`/no row)."""
        self.record(provider_name, ProviderAvailability.AVAILABLE, reason="Provider answered normally.")


class ProviderBudgetGate:
    """Composes the local counter with persisted provider state behind
    the single `has_budget()` shape every enrichment path already
    depends on -- so `AlphaPortfolioService`, `AlphaWatchlistService`,
    `enrich_holdings` and `refresh_company_data` gain provider-truth
    enforcement without any of them learning a new interface, and
    without importing a provider adapter.

    The composition is deliberately asymmetric, matching the trust
    model: local state may only ever make Atlas *more* pessimistic. A
    provider block wins outright; local exhaustion also blocks; only
    when neither objects is a call permitted.
    """

    def __init__(
        self,
        quota_tracker,
        availability_store: ProviderAvailabilityStore,
        *,
        provider_name: str,
        clock=None,
    ) -> None:
        self._quota = quota_tracker
        self._store = availability_store
        self._provider_name = provider_name
        self._clock = clock or _utc_now

    @property
    def provider_name(self) -> str:
        return self._provider_name

    def current_state(self) -> ProviderAvailability:
        record = self._store.get(self._provider_name)
        if record is not None and record.is_blocking(now=self._clock()):
            return record.state
        if not self._quota.has_budget():
            return ProviderAvailability.LOCALLY_EXHAUSTED
        if record is None:
            return ProviderAvailability.UNKNOWN
        return ProviderAvailability.AVAILABLE

    def blocking_record(self) -> ProviderAvailabilityRecord | None:
        record = self._store.get(self._provider_name)
        if record is not None and record.is_blocking(now=self._clock()):
            return record
        return None

    def has_budget(self) -> bool:
        """The one method every existing caller already knows. `False`
        whenever *either* the provider has blocked us or the local
        counter is spent."""
        if self.blocking_record() is not None:
            return False
        return bool(self._quota.has_budget())

    def record_daily_exhausted(self, reason: str) -> ProviderAvailabilityRecord:
        return self._store.record(
            self._provider_name,
            ProviderAvailability.PROVIDER_DAILY_EXHAUSTED,
            reason=reason,
            observed_at=self._clock(),
        )

    def record_short_term_throttle(self, reason: str) -> ProviderAvailabilityRecord:
        return self._store.record(
            self._provider_name,
            ProviderAvailability.PROVIDER_THROTTLED_SHORT_TERM,
            reason=reason,
            observed_at=self._clock(),
        )

    def record_available(self) -> None:
        self._store.clear(self._provider_name)

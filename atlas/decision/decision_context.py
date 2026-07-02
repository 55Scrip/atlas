from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from atlas.decision.memory import MemoryStore
from atlas.capabilities.watchlist_intelligence import WatchlistInput

if TYPE_CHECKING:
    from atlas.analysis.portfolio import Portfolio


@dataclass(frozen=True)
class DecisionContext:
    market_regime: str = "Unknown"
    portfolio: Portfolio | None = None
    watchlist: WatchlistInput | None = None
    historical_memory: MemoryStore | None = None
    investment_horizon: str = "long term"
    risk_profile: str = "balanced"
    available_capital: float | None = None
    cash_reserve_status: str = "unknown"
    comparison_tickers: tuple[str, ...] = ()

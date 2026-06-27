from dataclasses import dataclass

from atlas.analysis.memory import MemoryStore
from atlas.analysis.portfolio import Portfolio
from atlas.analysis.watchlist import Watchlist


@dataclass(frozen=True)
class DecisionContext:
    market_regime: str = "Unknown"
    portfolio: Portfolio | None = None
    watchlist: Watchlist | None = None
    historical_memory: MemoryStore | None = None
    investment_horizon: str = "long term"
    risk_profile: str = "balanced"
    available_capital: float | None = None
    cash_reserve_status: str = "unknown"
    comparison_tickers: tuple[str, ...] = ()

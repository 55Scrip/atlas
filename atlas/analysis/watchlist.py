import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class WatchlistItem:
    ticker: str


@dataclass(frozen=True)
class Watchlist:
    name: str
    items: tuple[WatchlistItem, ...]

    @classmethod
    def from_json_file(cls, path: Path) -> "Watchlist":
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        return cls.from_mapping(payload)

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "Watchlist":
        name = str(payload.get("name", "Watchlist")).strip() or "Watchlist"
        tickers = payload.get("tickers")
        if not isinstance(tickers, list) or not tickers:
            raise ValueError("Watchlist JSON must contain a non-empty tickers list.")
        return cls(
            name=name,
            items=tuple(WatchlistItem(ticker=str(ticker).upper()) for ticker in tickers),
        )

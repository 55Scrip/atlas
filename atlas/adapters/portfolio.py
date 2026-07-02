"""Boundary types and adapters for the legacy portfolio JSON format.

The legacy CLI portfolio file format stores positions as a relative `weight`
with no absolute currency market value:

    {"ticker": "NVDA", "company": "...", "sector": "...", "country": "...",
     "market_cap": 0, "weight": 0.12, "quality_score": 80, "risk_score": 40}

`Portfolio` and `PortfolioPosition` are the boundary types for this format.
They were previously in `atlas/analysis/portfolio.py` (deleted Sprint 135).

The Portfolio Domain (`atlas.domains.portfolio`) expects
`atlas.shared.Holding.market_value` to carry an absolute currency amount, and
derives weights from it.

Because the legacy format never recorded an absolute position size, this
adapter uses each position's `weight` directly as a stand-in market value.
This is deterministic and preserves all *relative* domain calculations
(sector/country allocation, concentration, top holdings) exactly, since those
calculations only depend on relative proportions between holdings. It does
not preserve a meaningful absolute `total_value` in currency terms -- callers
that need real currency totals should not rely on this adapter.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from atlas.analysis.scores import clamp_score
from atlas.capabilities.portfolio_intelligence import PortfolioFitInput
from atlas.shared import Holding, Portfolio as SharedPortfolio

DEFAULT_PORTFOLIO_ID = "legacy-portfolio"
DEFAULT_PORTFOLIO_NAME = "Legacy Portfolio"


@dataclass(frozen=True)
class PortfolioPosition:
    """One position in a legacy CLI portfolio JSON file."""

    ticker: str
    company: str
    sector: str
    country: str
    market_cap: float
    weight: float
    quality_score: int
    risk_score: int


@dataclass(frozen=True)
class Portfolio:
    """Legacy CLI portfolio loaded from a JSON file.

    Equivalent of the former `atlas.analysis.portfolio.Portfolio` (deleted Sprint 135).
    """

    positions: tuple[PortfolioPosition, ...]

    @classmethod
    def from_json_file(cls, path: Path) -> "Portfolio":
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        return cls.from_mapping(payload)

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "Portfolio":
        raw_positions = payload.get("positions")
        if not isinstance(raw_positions, list) or not raw_positions:
            raise ValueError("Portfolio JSON must contain a non-empty positions list.")
        return cls(positions=tuple(_position_from_mapping(item) for item in raw_positions))


def legacy_portfolio_to_domain_portfolio(
    legacy_portfolio: Portfolio,
    portfolio_id: str = DEFAULT_PORTFOLIO_ID,
    portfolio_name: str = DEFAULT_PORTFOLIO_NAME,
) -> SharedPortfolio:
    """Translate a legacy CLI portfolio into a Portfolio Domain entity.

    Deterministic, performs no I/O, and does not mutate its input.
    """

    holdings = tuple(
        Holding(
            company_id=position.ticker,
            ticker=position.ticker,
            quantity=0.0,
            current_price=None,
            market_value=position.weight,
            weight=position.weight,
            sector=position.sector,
            country=position.country,
            currency="USD",
            asset_type="equity",
            quality_score=position.quality_score,
            risk_score=position.risk_score,
            market_cap=float(position.market_cap),
        )
        for position in legacy_portfolio.positions
    )
    return SharedPortfolio(
        id=portfolio_id,
        name=portfolio_name,
        holdings=holdings,
    )


def portfolio_fit_input_from_profile(profile: PortfolioFitInput) -> PortfolioFitInput:
    """Identity adapter — providers now return PortfolioFitInput directly.

    Retained to avoid touching the four engine callers (conversation, dashboard,
    intelligence, decision). Callers can be cleaned up in a future sprint.
    """
    return profile


def _position_from_mapping(payload: dict[str, Any]) -> PortfolioPosition:
    required_fields = (
        "ticker",
        "company",
        "sector",
        "country",
        "market_cap",
        "weight",
        "quality_score",
        "risk_score",
    )
    missing = [field for field in required_fields if field not in payload]
    if missing:
        raise ValueError(f"Portfolio position is missing required fields: {', '.join(missing)}")
    return PortfolioPosition(
        ticker=str(payload["ticker"]).upper(),
        company=str(payload["company"]),
        sector=str(payload["sector"]),
        country=str(payload["country"]),
        market_cap=float(payload["market_cap"]),
        weight=_normalize_weight(float(payload["weight"])),
        quality_score=clamp_score(round(float(payload["quality_score"]))),
        risk_score=clamp_score(round(float(payload["risk_score"]))),
    )


def _normalize_weight(weight: float) -> float:
    normalized = weight / 100 if weight > 1 else weight
    return max(0.0, min(1.0, normalized))

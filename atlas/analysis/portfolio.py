import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from atlas.analysis.scores import clamp_score


@dataclass(frozen=True)
class PortfolioPosition:
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


@dataclass(frozen=True)
class CompanyPortfolioProfile:
    ticker: str
    company: str
    sector: str
    country: str
    market_cap: float
    quality_score: int
    risk_score: int


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

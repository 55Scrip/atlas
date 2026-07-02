"""Portfolio Intelligence capability engine (Sprint 113, extended Sprint 114).

Implements 7-dimension portfolio fit analysis using Blueprint-aligned types.
Ported from the private helper functions in `atlas/analysis/portfolio.py`.

This engine operates exclusively on `atlas.shared.Portfolio` and `PortfolioFitInput`.
It does NOT import or wrap the legacy `PortfolioIntelligenceEngine`.

Sprint 114 schema resolution:
  `atlas.shared.Holding` was extended with optional `quality_score`, `risk_score`,
  and `market_cap` fields (all default None). When populated (e.g. via the
  `legacy_portfolio_to_domain_portfolio` adapter), all 7 dimensions have full parity
  with the legacy `PortfolioIntelligenceEngine`.

Fallback behavior when enriched fields are absent (Holding.quality_score / risk_score /
market_cap are None):
  - quality_impact: score derived from target quality_score alone
    (50 + (target_quality - 50) * 0.5)
  - risk_impact: score derived from target risk_score alone
    (50 + (target_risk - 50) * 0.5)
  - market_cap_concentration: target cap bucket classified; portfolio mega-cap weight = 0
  - diversification_impact: mega-cap component treated as 0

These fallbacks are conservative — they produce lower-confidence scores than full parity
but are deterministic and never error.
"""

from __future__ import annotations

from atlas.capabilities.portfolio_intelligence.models import (
    PortfolioFitDimension,
    PortfolioFitInput,
    PortfolioFitResult,
)
from atlas.shared.entities import Holding, Portfolio


_DEFAULT_TARGET_WEIGHT = 0.05
_SCORE_NO_OVERLAP = 92


class PortfolioIntelligenceCapability:
    """Deterministic, local-only portfolio fit analysis capability.

    Accepts a Blueprint-aligned Portfolio and a PortfolioFitInput describing the
    target company. Returns a PortfolioFitResult with 7 scored dimensions and an
    aggregate fit score.

    No providers, no network calls, no recommendation language.
    """

    def analyze(
        self,
        portfolio: Portfolio,
        fit_input: PortfolioFitInput,
        target_weight: float = _DEFAULT_TARGET_WEIGHT,
    ) -> PortfolioFitResult:
        normalized_weight = _normalize_weight(target_weight)
        diversification = _diversification_impact(portfolio, fit_input, normalized_weight)
        sector = _sector_concentration(portfolio, fit_input, normalized_weight)
        country = _country_concentration(portfolio, fit_input, normalized_weight)
        market_cap = _market_cap_concentration(portfolio, fit_input, normalized_weight)
        overlap = _overlap_with_existing_holdings(portfolio, fit_input)
        quality = _quality_impact(portfolio, fit_input, normalized_weight)
        risk = _risk_impact(portfolio, fit_input, normalized_weight)
        fit_score = _aggregate_fit_score(
            diversification=diversification,
            sector=sector,
            country=country,
            market_cap=market_cap,
            overlap=overlap,
            quality=quality,
            risk=risk,
        )
        return PortfolioFitResult(
            ticker=fit_input.ticker,
            company=fit_input.company,
            fit_score=fit_score,
            diversification=diversification,
            sector_concentration=sector,
            country_concentration=country,
            market_cap_concentration=market_cap,
            overlap=overlap,
            quality_impact=quality,
            risk_impact=risk,
            summary=_build_summary(fit_input, fit_score, sector, overlap),
        )


# ---------------------------------------------------------------------------
# Dimension calculators
# ---------------------------------------------------------------------------

def _diversification_impact(
    portfolio: Portfolio,
    fit_input: PortfolioFitInput,
    target_weight: float,
) -> PortfolioFitDimension:
    sector_weight = _weight_by_attribute(portfolio.holdings, "sector", fit_input.sector)
    country_weight = _weight_by_attribute(portfolio.holdings, "country", fit_input.country)
    mega_cap_weight = _mega_cap_weight(portfolio)
    has_market_cap_data = any(h.market_cap is not None for h in portfolio.holdings)
    raw_score = 100 - round(
        (sector_weight * 55) + (country_weight * 25) + (mega_cap_weight * 20)
    )
    score = _clamp(raw_score)
    gap_note = "" if has_market_cap_data else " Mega-cap component unavailable (no market_cap on holdings)."
    return PortfolioFitDimension(
        score=score,
        note=(
            f"Adding {fit_input.ticker} would encounter existing {fit_input.sector} "
            f"exposure of {sector_weight:.1%} and {fit_input.country} exposure of "
            f"{country_weight:.1%}.{gap_note}"
        ),
    )


def _sector_concentration(
    portfolio: Portfolio,
    fit_input: PortfolioFitInput,
    target_weight: float,
) -> PortfolioFitDimension:
    current_weight = _weight_by_attribute(portfolio.holdings, "sector", fit_input.sector)
    pro_forma_weight = current_weight + target_weight
    score = _concentration_score(pro_forma_weight, preferred_limit=0.25, hard_limit=0.40)
    return PortfolioFitDimension(
        score=score,
        note=(
            f"Pro forma {fit_input.sector} exposure would be {pro_forma_weight:.1%} "
            f"including the target position."
        ),
    )


def _country_concentration(
    portfolio: Portfolio,
    fit_input: PortfolioFitInput,
    target_weight: float,
) -> PortfolioFitDimension:
    current_weight = _weight_by_attribute(portfolio.holdings, "country", fit_input.country)
    pro_forma_weight = current_weight + target_weight
    score = _concentration_score(pro_forma_weight, preferred_limit=0.45, hard_limit=0.65)
    return PortfolioFitDimension(
        score=score,
        note=(
            f"Pro forma {fit_input.country} exposure would be {pro_forma_weight:.1%} "
            f"including the target position."
        ),
    )


def _market_cap_concentration(
    portfolio: Portfolio,
    fit_input: PortfolioFitInput,
    target_weight: float,
) -> PortfolioFitDimension:
    existing_mega_cap_weight = _mega_cap_weight(portfolio)
    is_mega = _is_mega_cap(fit_input.market_cap)
    pro_forma_weight = existing_mega_cap_weight + (target_weight if is_mega else 0)
    has_market_cap_data = any(h.market_cap is not None for h in portfolio.holdings)
    cap_bucket = "mega-cap" if is_mega else "non-mega-cap"
    if has_market_cap_data:
        score = _concentration_score(pro_forma_weight, preferred_limit=0.35, hard_limit=0.55)
        return PortfolioFitDimension(
            score=score,
            note=(
                f"{fit_input.ticker} is a {cap_bucket} company. Pro forma mega-cap "
                f"exposure would be {pro_forma_weight:.1%}."
            ),
        )
    # Fallback: no market_cap data on holdings — classify target only
    return PortfolioFitDimension(
        score=50,
        note=(
            f"{fit_input.ticker} is a {cap_bucket} company. Existing portfolio mega-cap "
            f"weight unavailable (no market_cap on holdings)."
        ),
    )


def _overlap_with_existing_holdings(
    portfolio: Portfolio,
    fit_input: PortfolioFitInput,
) -> PortfolioFitDimension:
    existing_tickers = {h.ticker.upper() for h in portfolio.holdings}
    if fit_input.ticker.upper() in existing_tickers:
        return PortfolioFitDimension(
            score=20,
            note=f"{fit_input.ticker} already exists in the portfolio (direct overlap).",
        )
    same_sector = [h for h in portfolio.holdings if h.sector == fit_input.sector]
    if same_sector:
        tickers = ", ".join(h.ticker for h in same_sector)
        score = _clamp(80 - len(same_sector) * 10)
        return PortfolioFitDimension(
            score=score,
            note=f"{fit_input.ticker} overlaps by sector with existing holdings: {tickers}.",
        )
    return PortfolioFitDimension(
        score=_SCORE_NO_OVERLAP,
        note=f"{fit_input.ticker} has no direct ticker or sector overlap with current holdings.",
    )


def _quality_impact(
    portfolio: Portfolio,
    fit_input: PortfolioFitInput,
    target_weight: float,
) -> PortfolioFitDimension:
    enriched = [h for h in portfolio.holdings if h.quality_score is not None]
    if enriched:
        # Full parity: weighted average from enriched holdings
        current_quality = _weighted_average_optional(enriched, "quality_score")
        pro_forma_quality = _pro_forma_average(current_quality, fit_input.quality_score, target_weight)
        score = _clamp(round(50 + (pro_forma_quality - current_quality) * 4))
        direction = "improve" if pro_forma_quality >= current_quality else "dilute"
        return PortfolioFitDimension(
            score=score,
            note=(
                f"The target quality score of {fit_input.quality_score}/100 would {direction} "
                f"portfolio quality from {current_quality:.1f}/100 to {pro_forma_quality:.1f}/100."
            ),
        )
    # Fallback: no quality_score on holdings
    score = _clamp(round(50 + (fit_input.quality_score - 50) * 0.5))
    return PortfolioFitDimension(
        score=score,
        note=(
            f"Target quality score is {fit_input.quality_score}/100. Portfolio quality "
            f"delta unavailable (no quality_score on holdings)."
        ),
    )


def _risk_impact(
    portfolio: Portfolio,
    fit_input: PortfolioFitInput,
    target_weight: float,
) -> PortfolioFitDimension:
    enriched = [h for h in portfolio.holdings if h.risk_score is not None]
    if enriched:
        # Full parity: weighted average from enriched holdings
        current_risk = _weighted_average_optional(enriched, "risk_score")
        pro_forma_risk = _pro_forma_average(current_risk, fit_input.risk_score, target_weight)
        score = _clamp(round(50 + (pro_forma_risk - current_risk) * 4))
        direction = "improve" if pro_forma_risk >= current_risk else "weaken"
        return PortfolioFitDimension(
            score=score,
            note=(
                f"The target risk profile score of {fit_input.risk_score}/100 would {direction} "
                f"portfolio risk quality from {current_risk:.1f}/100 to {pro_forma_risk:.1f}/100."
            ),
        )
    # Fallback: no risk_score on holdings
    score = _clamp(round(50 + (fit_input.risk_score - 50) * 0.5))
    return PortfolioFitDimension(
        score=score,
        note=(
            f"Target risk profile score is {fit_input.risk_score}/100. Portfolio risk "
            f"delta unavailable (no risk_score on holdings)."
        ),
    )


def _aggregate_fit_score(
    diversification: PortfolioFitDimension,
    sector: PortfolioFitDimension,
    country: PortfolioFitDimension,
    market_cap: PortfolioFitDimension,
    overlap: PortfolioFitDimension,
    quality: PortfolioFitDimension,
    risk: PortfolioFitDimension,
) -> int:
    # Weights mirror legacy _aggregate_portfolio_score exactly.
    weighted = (
        diversification.score * 0.15
        + sector.score * 0.15
        + country.score * 0.10
        + market_cap.score * 0.10
        + overlap.score * 0.15
        + quality.score * 0.20
        + risk.score * 0.15
    )
    return _clamp(round(weighted))


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def _build_summary(
    fit_input: PortfolioFitInput,
    fit_score: int,
    sector: PortfolioFitDimension,
    overlap: PortfolioFitDimension,
) -> str:
    return (
        f"{fit_input.ticker} has a portfolio fit score of {fit_score}/100. "
        f"Key context: sector concentration ({sector.score}/100), "
        f"overlap ({overlap.score}/100)."
    )


# ---------------------------------------------------------------------------
# Internal helpers (ported from atlas/analysis/portfolio.py)
# ---------------------------------------------------------------------------

def _weight_by_attribute(holdings: tuple[Holding, ...], attribute: str, value: str) -> float:
    return sum(
        h.weight
        for h in holdings
        if getattr(h, attribute, "").lower() == value.lower()
    )


def _mega_cap_weight(portfolio: Portfolio) -> float:
    return sum(
        h.weight
        for h in portfolio.holdings
        if h.market_cap is not None and _is_mega_cap(h.market_cap)
    )


def _weighted_average_optional(holdings: list[Holding], attribute: str) -> float:
    total_weight = sum(h.weight for h in holdings)
    if total_weight <= 0:
        return 0.0
    return sum(getattr(h, attribute) * h.weight for h in holdings) / total_weight


def _pro_forma_average(current_value: float, target_value: int, target_weight: float) -> float:
    current_weight = max(0.0, 1.0 - target_weight)
    return current_value * current_weight + target_value * target_weight


def _concentration_score(weight: float, preferred_limit: float, hard_limit: float) -> int:
    if weight <= preferred_limit:
        return 90
    if weight >= hard_limit:
        return 25
    penalty_range = hard_limit - preferred_limit
    overage = weight - preferred_limit
    return _clamp(round(90 - (overage / penalty_range) * 65))


def _normalize_weight(weight: float) -> float:
    normalized = weight / 100 if weight > 1 else weight
    return max(0.0, min(1.0, normalized))


def _is_mega_cap(market_cap: float) -> bool:
    return market_cap >= 500_000_000_000


def _clamp(score: int) -> int:
    return max(0, min(100, score))

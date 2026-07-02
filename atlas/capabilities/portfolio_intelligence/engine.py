"""Portfolio Intelligence capability engine (Sprint 113).

Implements 7-dimension portfolio fit analysis using Blueprint-aligned types.
Ported from the private helper functions in `atlas/analysis/portfolio.py`.

This engine operates exclusively on `atlas.shared.Portfolio` and `PortfolioFitInput`.
It does NOT import or wrap the legacy `PortfolioIntelligenceEngine`.

Schema gap (documented — not silently changed):
  `atlas.shared.Holding` lacks `quality_score`, `risk_score`, and `market_cap`.
  The legacy `PortfolioPosition` carries all three, enabling 3 full dimensions:
    - quality_impact   → requires per-holding quality_score (not available)
    - risk_impact      → requires per-holding risk_score (not available)
    - market_cap_concentration → requires per-holding market_cap (not available)
    - diversification_impact   → mega-cap weight component requires market_cap (not available;
                                  sector and country components are computed normally)

  For these blocked components, a neutral score of 50 is returned with a note documenting
  the gap. Parity with the legacy engine on those dimensions requires extending
  `atlas.shared.Holding` — tracked as a Phase 4 prerequisite in PortfolioAnalysisMigrationPlan.

  Dimensions with full parity (atlas.shared.Holding has all required fields):
    - sector_concentration       ✓
    - country_concentration      ✓
    - overlap_with_existing_holdings ✓
    - diversification_impact     (partial: sector + country components ✓; mega-cap component = 0)
"""

from __future__ import annotations

from atlas.capabilities.portfolio_intelligence.models import (
    PortfolioFitDimension,
    PortfolioFitInput,
    PortfolioFitResult,
)
from atlas.shared.entities import Holding, Portfolio


_DEFAULT_TARGET_WEIGHT = 0.05
_SCORE_GAP_NEUTRAL = 50
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
        market_cap = _market_cap_concentration(fit_input, normalized_weight)
        overlap = _overlap_with_existing_holdings(portfolio, fit_input)
        quality = _quality_impact(fit_input)
        risk = _risk_impact(fit_input)
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
    # mega_cap_weight requires market_cap on Holding — not available in atlas.shared.Holding.
    # Component is treated as 0 (conservative underestimate); full parity blocked by schema gap.
    raw_score = 100 - round((sector_weight * 55) + (country_weight * 25))
    score = _clamp(raw_score)
    return PortfolioFitDimension(
        score=score,
        note=(
            f"Adding {fit_input.ticker} would encounter existing {fit_input.sector} "
            f"exposure of {sector_weight:.1%} and {fit_input.country} exposure of "
            f"{country_weight:.1%}. Mega-cap concentration not computed (schema gap)."
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
    fit_input: PortfolioFitInput,
    target_weight: float,
) -> PortfolioFitDimension:
    # Per-holding market_cap is not available on atlas.shared.Holding.
    # Only the target company's market_cap (from PortfolioFitInput) is known.
    # Partial result: classify target company, note existing mega-cap weight is unknown.
    is_mega = _is_mega_cap(fit_input.market_cap)
    cap_bucket = "mega-cap" if is_mega else "non-mega-cap"
    return PortfolioFitDimension(
        score=_SCORE_GAP_NEUTRAL,
        note=(
            f"{fit_input.ticker} is a {cap_bucket} company. Existing portfolio mega-cap "
            f"weight is unavailable (schema gap: atlas.shared.Holding lacks market_cap)."
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


def _quality_impact(fit_input: PortfolioFitInput) -> PortfolioFitDimension:
    # Weighted average of existing holding quality scores requires quality_score on Holding
    # (not available in atlas.shared.Holding). Only the target's quality_score is known.
    # Partial result: score reflects the target's standalone quality; no delta computed.
    score = _clamp(round(50 + (fit_input.quality_score - 50) * 0.5))
    return PortfolioFitDimension(
        score=score,
        note=(
            f"Target quality score is {fit_input.quality_score}/100. Portfolio quality "
            f"delta unavailable (schema gap: atlas.shared.Holding lacks quality_score)."
        ),
    )


def _risk_impact(fit_input: PortfolioFitInput) -> PortfolioFitDimension:
    # Weighted average of existing holding risk scores requires risk_score on Holding
    # (not available in atlas.shared.Holding). Only the target's risk_score is known.
    # Partial result: score reflects the target's standalone risk profile; no delta computed.
    score = _clamp(round(50 + (fit_input.risk_score - 50) * 0.5))
    return PortfolioFitDimension(
        score=score,
        note=(
            f"Target risk profile score is {fit_input.risk_score}/100. Portfolio risk "
            f"delta unavailable (schema gap: atlas.shared.Holding lacks risk_score)."
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
        f"overlap ({overlap.score}/100). "
        f"Quality and risk impact scores are partial pending schema alignment."
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

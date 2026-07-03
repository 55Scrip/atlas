"""Blueprint-aligned types for portfolio fit analysis.

These types are the future destination for logic currently in
`atlas/analysis/portfolio.py`. No existing caller uses them yet —
migration will happen incrementally in Sprints 113+.

Legacy mapping:
  CompanyPortfolioProfile  →  PortfolioFitInput
  PortfolioAnalysis        →  PortfolioFitResult
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PortfolioFitDimension:
    """A single scored dimension of portfolio fit with a human-readable note.

    Replaces the role of `PortfolioSignal` from `atlas/analysis/portfolio.py`,
    but uses neutral framing (note) rather than recommendation-adjacent (reasoning).
    """

    score: int
    note: str


@dataclass(frozen=True)
class PortfolioFitInput:
    """Input required to evaluate how a company fits an existing portfolio."""

    ticker: str
    company: str
    sector: str
    country: str
    market_cap: float
    quality_score: int
    risk_score: int


@dataclass(frozen=True)
class PortfolioFitResult:
    """Result of a portfolio fit analysis for a target company.

    Blueprint-aligned equivalent of legacy `PortfolioAnalysis`.

    Uses neutral, research-framed language — no buy/sell/hold/recommendation
    terminology in field names or expected values.

    Field mapping from PortfolioAnalysis:
      company                             → company              (unchanged)
      ticker                              → ticker               (unchanged)
      portfolio_score                     → fit_score            (renamed: neutral framing)
      recommendation                      → (omitted)            legacy enum not carried forward
      diversification_impact              → diversification      (PortfolioFitDimension)
      sector_concentration                → sector_concentration (PortfolioFitDimension)
      country_concentration               → country_concentration(PortfolioFitDimension)
      market_cap_concentration            → market_cap_concentration (PortfolioFitDimension)
      overlap_with_existing_holdings      → overlap              (PortfolioFitDimension)
      expected_portfolio_quality_impact   → quality_impact       (PortfolioFitDimension)
      expected_portfolio_risk_impact      → risk_impact          (PortfolioFitDimension)
      final_reasoning                     → summary              (renamed: neutral framing)

    Intentionally omitted:
      - recommendation (PortfolioRecommendation enum) — no advisory semantics in Blueprint layer
    """

    ticker: str
    company: str
    fit_score: int
    diversification: PortfolioFitDimension
    sector_concentration: PortfolioFitDimension
    country_concentration: PortfolioFitDimension
    market_cap_concentration: PortfolioFitDimension
    overlap: PortfolioFitDimension
    quality_impact: PortfolioFitDimension
    risk_impact: PortfolioFitDimension
    summary: str

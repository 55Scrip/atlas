"""Blueprint-aligned Portfolio Intelligence capability stub.

Phase 2 of the portfolio.py migration (Sprint 112).
Defines the future destination types for portfolio fit analysis.

Existing callers of `atlas.analysis.portfolio` are NOT migrated yet.
Migration will proceed incrementally in Sprints 113+.
"""

from atlas.capabilities.portfolio_intelligence.models import (
    PortfolioFitDimension,
    PortfolioFitInput,
    PortfolioFitResult,
)

__all__ = [
    "PortfolioFitDimension",
    "PortfolioFitInput",
    "PortfolioFitResult",
]

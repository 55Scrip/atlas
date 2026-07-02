"""Blueprint-aligned Portfolio Intelligence capability.

Phase 3 of the portfolio.py migration (Sprint 113).
Engine implemented; types and engine are both exported.

Existing callers of `atlas.analysis.portfolio` are NOT migrated yet.
Migration will proceed incrementally in Sprints 114+.
"""

from atlas.capabilities.portfolio_intelligence.engine import PortfolioIntelligenceCapability
from atlas.capabilities.portfolio_intelligence.models import (
    PortfolioFitDimension,
    PortfolioFitInput,
    PortfolioFitResult,
)

__all__ = [
    "PortfolioFitDimension",
    "PortfolioFitInput",
    "PortfolioFitResult",
    "PortfolioIntelligenceCapability",
]

"""Blueprint-aligned Portfolio Intelligence capability.

Phase 3 of the portfolio.py migration (Sprint 113).
Engine implemented; types and engine are both exported.

All callers of `atlas.analysis.portfolio` migrated as of Sprint 135.
`atlas.analysis.portfolio` deleted Sprint 135; types live in `atlas/adapters/portfolio.py`.
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

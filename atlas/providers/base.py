from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from atlas.analysis.company_analysis import CompanyAnalysis
    from atlas.analysis.portfolio import CompanyPortfolioProfile


class CompanyDataProvider(Protocol):
    def get_company_analysis(self, ticker: str) -> "CompanyAnalysis":
        """Return module-level company analysis for a ticker."""
        ...

    def get_portfolio_profile(self, ticker: str) -> "CompanyPortfolioProfile":
        """Return portfolio-level company profile for a ticker."""
        ...

from atlas.analysis.company_analysis import CompanyAnalysis
from atlas.analysis.portfolio import CompanyPortfolioProfile


class YahooFinanceProvider:
    def get_company_analysis(self, ticker: str) -> CompanyAnalysis:
        raise NotImplementedError(
            "Yahoo Finance company analysis mapping is not implemented yet."
        )

    def get_portfolio_profile(self, ticker: str) -> CompanyPortfolioProfile:
        raise NotImplementedError(
            "Yahoo Finance portfolio profile mapping is not implemented yet."
        )

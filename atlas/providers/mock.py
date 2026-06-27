from dataclasses import replace

from atlas.analysis.company_analysis import CompanyAnalysis, create_placeholder_company_analysis
from atlas.analysis.portfolio import CompanyPortfolioProfile


MOCK_COMPANY_NAMES: dict[str, str] = {
    "NVDA": "NVIDIA (NVDA)",
    "AMD": "Advanced Micro Devices (AMD)",
    "AAPL": "Apple (AAPL)",
    "MSFT": "Microsoft (MSFT)",
    "EVO": "Evolution (EVO)",
}


MOCK_COMPANY_PORTFOLIO_PROFILES: dict[str, CompanyPortfolioProfile] = {
    "NVDA": CompanyPortfolioProfile(
        ticker="NVDA",
        company="NVIDIA",
        sector="Semiconductors",
        country="United States",
        market_cap=3_300_000_000_000,
        quality_score=92,
        risk_score=77,
    ),
    "AAPL": CompanyPortfolioProfile(
        ticker="AAPL",
        company="Apple",
        sector="Consumer Electronics",
        country="United States",
        market_cap=3_000_000_000_000,
        quality_score=86,
        risk_score=72,
    ),
    "MSFT": CompanyPortfolioProfile(
        ticker="MSFT",
        company="Microsoft",
        sector="Software",
        country="United States",
        market_cap=3_400_000_000_000,
        quality_score=90,
        risk_score=78,
    ),
    "EVO": CompanyPortfolioProfile(
        ticker="EVO",
        company="Evolution",
        sector="Gaming Technology",
        country="Sweden",
        market_cap=18_000_000_000,
        quality_score=84,
        risk_score=70,
    ),
}


class MockCompanyAnalysisProvider:
    def __init__(self) -> None:
        self._companies = {
            ticker: _create_mock_company_analysis(ticker, company)
            for ticker, company in MOCK_COMPANY_NAMES.items()
        }

    def get_company_analysis(self, ticker: str) -> CompanyAnalysis:
        normalized_ticker = ticker.upper()
        try:
            return self._companies[normalized_ticker]
        except KeyError as exc:
            available = ", ".join(sorted(self._companies))
            raise LookupError(
                f"No mock company analysis available for {normalized_ticker}. "
                f"Available tickers: {available}"
            ) from exc

    def get_portfolio_profile(self, ticker: str) -> CompanyPortfolioProfile:
        normalized_ticker = ticker.upper()
        try:
            return MOCK_COMPANY_PORTFOLIO_PROFILES[normalized_ticker]
        except KeyError as exc:
            available = ", ".join(sorted(MOCK_COMPANY_PORTFOLIO_PROFILES))
            raise LookupError(
                f"No mock portfolio profile available for {normalized_ticker}. "
                f"Available tickers: {available}"
            ) from exc


def _create_mock_company_analysis(ticker: str, company: str) -> CompanyAnalysis:
    analysis = create_placeholder_company_analysis(company)
    if ticker == "AMD":
        return replace(
            analysis,
            valuation=replace(
                analysis.valuation,
                score=84,
                summary=f"{company} has a more attractive valuation profile than larger peers.",
            ),
            quality=replace(
                analysis.quality,
                score=82,
                summary=f"{company} is a strong business, but profitability trails the leader.",
            ),
            growth=replace(
                analysis.growth,
                score=88,
                summary=f"{company} has a solid AI-driven growth profile.",
            ),
            moat=replace(
                analysis.moat,
                score=76,
                summary=f"{company} has competitive assets, but the moat is less dominant.",
            ),
        )
    if ticker == "MSFT":
        return replace(
            analysis,
            valuation=replace(
                analysis.valuation,
                score=78,
                summary=f"{company} has a reasonable valuation for a durable compounder.",
            ),
            quality=replace(
                analysis.quality,
                score=88,
                summary=f"{company} has excellent quality across software and cloud.",
            ),
            growth=replace(
                analysis.growth,
                score=89,
                summary=f"{company} has durable growth, though less explosive than NVIDIA.",
            ),
            moat=replace(
                analysis.moat,
                score=92,
                summary=f"{company} has a broad ecosystem moat across enterprise software.",
            ),
        )
    if ticker == "AAPL":
        return replace(
            analysis,
            valuation=replace(
                analysis.valuation,
                score=76,
                summary=f"{company} has a fair valuation with modest growth expectations.",
            ),
            quality=replace(
                analysis.quality,
                score=86,
                summary=f"{company} remains a high-quality consumer ecosystem business.",
            ),
            growth=replace(
                analysis.growth,
                score=62,
                summary=f"{company} has slower growth than the AI infrastructure leaders.",
            ),
        )
    return analysis

from urllib.error import HTTPError, URLError

from atlas.analysis.comparison import ComparisonEngine
from atlas.analysis.engine import AtlasInvestmentEngine
from atlas.analysis.memory import MemoryEngine, MemoryStore
from atlas.analysis.portfolio import Portfolio, PortfolioIntelligenceEngine, PortfolioPosition
from atlas.providers import (
    CompanyDataProvider,
    MockCompanyAnalysisProvider,
    YahooFinanceProvider,
    YahooFinanceProviderError,
)


def _sample_portfolio() -> Portfolio:
    return Portfolio(
        positions=(
            PortfolioPosition(
                ticker="AAPL",
                company="Apple",
                sector="Consumer Electronics",
                country="United States",
                market_cap=3_000_000_000_000,
                weight=0.25,
                quality_score=86,
                risk_score=72,
            ),
        )
    )


def test_mock_provider_returns_company_analysis_and_portfolio_profile():
    provider: CompanyDataProvider = MockCompanyAnalysisProvider()

    analysis = provider.get_company_analysis("NVDA")
    profile = provider.get_portfolio_profile("NVDA")

    assert analysis.company == "NVIDIA (NVDA)"
    assert profile.ticker == "NVDA"
    assert profile.sector == "Semiconductors"


def test_yahoo_provider_maps_company_financial_market_and_analysis_data():
    provider: CompanyDataProvider = YahooFinanceProvider(fetcher=_fake_yahoo_fetcher)

    company = provider.get_company("NVDA")
    financials = provider.get_financials("NVDA")
    market_data = provider.get_market_data("NVDA")
    analysis = provider.get_company_analysis("NVDA")
    profile = provider.get_portfolio_profile("NVDA")

    assert company.name == "NVIDIA Corporation"
    assert company.exchange == "NasdaqGS"
    assert company.sector == "Technology"
    assert company.industry == "Semiconductors"
    assert company.market_cap == 3_300_000_000_000
    assert financials.revenue == 100_000_000_000
    assert financials.gross_margin == 0.74
    assert financials.operating_margin == 0.62
    assert financials.net_margin == 0.55
    assert financials.free_cash_flow == 45_000_000_000
    assert financials.eps == 2.5
    assert financials.shares_outstanding == 24_000_000_000
    assert market_data.current_price == 125
    assert market_data.fifty_two_week_high == 140
    assert market_data.fifty_two_week_low == 75
    assert market_data.pe_ratio == 50
    assert market_data.beta == 1.6
    assert market_data.dividend_yield == 0.0003
    assert analysis.company == "NVIDIA Corporation (NVDA)"
    assert profile.company == "NVIDIA Corporation"
    assert profile.sector == "Technology"


def test_yahoo_provider_reports_invalid_ticker_gracefully():
    provider = YahooFinanceProvider(
        fetcher=lambda _: {"quoteSummary": {"result": [], "error": None}}
    )

    try:
        provider.get_company("BAD")
    except YahooFinanceProviderError as exc:
        assert "No Yahoo Finance data found for BAD" in str(exc)
    else:
        raise AssertionError("YahooFinanceProvider should reject unknown tickers")


def test_yahoo_provider_handles_missing_fields_without_crashing():
    provider = YahooFinanceProvider(fetcher=_minimal_yahoo_fetcher)

    company = provider.get_company("MSFT")
    financials = provider.get_financials("MSFT")
    market_data = provider.get_market_data("MSFT")
    analysis = provider.get_company_analysis("MSFT")

    assert company.name == "Microsoft Corporation"
    assert company.exchange is None
    assert financials.revenue is None
    assert market_data.current_price is None
    assert analysis.company == "Microsoft Corporation (MSFT)"


def test_yahoo_provider_reports_rate_limits_gracefully():
    def rate_limited(_url: str):
        raise HTTPError(
            url="https://query1.finance.yahoo.com",
            code=429,
            msg="Too Many Requests",
            hdrs=None,
            fp=None,
        )

    provider = YahooFinanceProvider(fetcher=rate_limited)

    try:
        provider.get_company("NVDA")
    except YahooFinanceProviderError as exc:
        assert "rate limit" in str(exc)
    else:
        raise AssertionError("YahooFinanceProvider should report rate limits")


def test_yahoo_provider_reports_network_failures_gracefully():
    def network_failure(_url: str):
        raise URLError("offline")

    provider = YahooFinanceProvider(fetcher=network_failure)

    try:
        provider.get_company("NVDA")
    except YahooFinanceProviderError as exc:
        assert "network error" in str(exc)
    else:
        raise AssertionError("YahooFinanceProvider should report network failures")


def test_investment_engine_can_analyze_ticker_from_provider():
    provider = MockCompanyAnalysisProvider()

    report = AtlasInvestmentEngine().analyze_ticker("NVDA", provider)

    assert report.company == "NVIDIA (NVDA)"
    assert report.atlas_score > 0


def test_portfolio_engine_can_analyze_ticker_from_provider():
    provider = MockCompanyAnalysisProvider()

    analysis = PortfolioIntelligenceEngine().analyze_ticker(
        portfolio=_sample_portfolio(),
        ticker="NVDA",
        provider=provider,
    )

    assert analysis.ticker == "NVDA"
    assert analysis.company == "NVIDIA"


def test_comparison_engine_can_compare_tickers_from_provider():
    provider = MockCompanyAnalysisProvider()

    result = ComparisonEngine().compare_tickers(["NVDA", "AMD"], provider)

    assert tuple(candidate.ticker for candidate in result.candidates) == ("NVDA", "AMD")
    assert result.best_overall.winner.ticker in {"NVDA", "AMD"}


def test_memory_engine_can_save_ticker_from_provider(tmp_path):
    provider = MockCompanyAnalysisProvider()
    store = MemoryStore(tmp_path / "memory.json")

    entry = MemoryEngine().save_ticker(store=store, ticker="NVDA", provider=provider)

    assert entry.ticker == "NVDA"
    assert store.load() == (entry,)


def _fake_yahoo_fetcher(_url: str):
    return {
        "quoteSummary": {
            "result": [
                {
                    "price": {
                        "longName": "NVIDIA Corporation",
                        "exchangeName": "NasdaqGS",
                        "marketCap": {"raw": 3_300_000_000_000},
                        "regularMarketPrice": {"raw": 125},
                    },
                    "summaryProfile": {
                        "sector": "Technology",
                        "industry": "Semiconductors",
                    },
                    "financialData": {
                        "currentPrice": {"raw": 125},
                        "totalRevenue": {"raw": 100_000_000_000},
                        "grossMargins": {"raw": 0.74},
                        "operatingMargins": {"raw": 0.62},
                        "profitMargins": {"raw": 0.55},
                        "freeCashflow": {"raw": 45_000_000_000},
                    },
                    "defaultKeyStatistics": {
                        "trailingEps": {"raw": 2.5},
                        "sharesOutstanding": {"raw": 24_000_000_000},
                        "beta": {"raw": 1.6},
                    },
                    "summaryDetail": {
                        "fiftyTwoWeekHigh": {"raw": 140},
                        "fiftyTwoWeekLow": {"raw": 75},
                        "trailingPE": {"raw": 50},
                        "dividendYield": {"raw": 0.0003},
                    },
                }
            ],
            "error": None,
        }
    }


def _minimal_yahoo_fetcher(_url: str):
    return {
        "quoteSummary": {
            "result": [
                {
                    "price": {"longName": "Microsoft Corporation"},
                    "summaryProfile": {},
                    "financialData": {},
                    "defaultKeyStatistics": {},
                    "summaryDetail": {},
                }
            ],
            "error": None,
        }
    }

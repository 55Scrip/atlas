import pytest

from atlas.analysis.comparison import ComparisonEngine
from atlas.analysis.engine import AtlasInvestmentEngine
from atlas.analysis.memory import MemoryEngine, MemoryStore
from atlas.analysis.portfolio import Portfolio, PortfolioIntelligenceEngine, PortfolioPosition
from atlas.providers import (
    CompanyDataProvider,
    MockCompanyAnalysisProvider,
    YahooFinanceProvider,
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


def test_yahoo_provider_exposes_interface_without_live_mapping():
    provider: CompanyDataProvider = YahooFinanceProvider()

    with pytest.raises(NotImplementedError):
        provider.get_company_analysis("NVDA")

    with pytest.raises(NotImplementedError):
        provider.get_portfolio_profile("NVDA")


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

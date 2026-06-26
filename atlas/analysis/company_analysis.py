from dataclasses import dataclass, replace
from typing import Protocol

from atlas.analysis.growth import GrowthAnalysis, placeholder_growth_analysis
from atlas.analysis.macro import MacroAnalysis, placeholder_macro_analysis
from atlas.analysis.moat import MoatAnalysis, placeholder_moat_analysis
from atlas.analysis.quality import QualityAnalysis, placeholder_quality_analysis
from atlas.analysis.sentiment import SentimentAnalysis, placeholder_sentiment_analysis
from atlas.analysis.technicals import TechnicalAnalysis, placeholder_technical_analysis
from atlas.analysis.valuation import ValuationAnalysis, placeholder_valuation_analysis


@dataclass(frozen=True)
class CompanyAnalysis:
    company: str
    valuation: ValuationAnalysis
    quality: QualityAnalysis
    growth: GrowthAnalysis
    moat: MoatAnalysis
    macro: MacroAnalysis
    technicals: TechnicalAnalysis
    sentiment: SentimentAnalysis


class CompanyAnalysisProvider(Protocol):
    def get_company_analysis(self, ticker: str) -> CompanyAnalysis:
        """Return module-level analysis for a ticker."""


class MockCompanyAnalysisProvider:
    def __init__(self) -> None:
        self._companies = {
            ticker: _create_mock_company_analysis(ticker, company)
            for ticker, company in {
                "NVDA": "NVIDIA (NVDA)",
                "AMD": "Advanced Micro Devices (AMD)",
                "AAPL": "Apple (AAPL)",
                "MSFT": "Microsoft (MSFT)",
                "EVO": "Evolution (EVO)",
            }.items()
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


def create_placeholder_company_analysis(company: str) -> CompanyAnalysis:
    return CompanyAnalysis(
        company=company,
        valuation=placeholder_valuation_analysis(company),
        quality=placeholder_quality_analysis(company),
        growth=placeholder_growth_analysis(company),
        moat=placeholder_moat_analysis(company),
        macro=placeholder_macro_analysis(company),
        technicals=placeholder_technical_analysis(company),
        sentiment=placeholder_sentiment_analysis(company),
    )


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

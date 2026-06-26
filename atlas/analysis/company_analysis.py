from dataclasses import dataclass
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
            ticker: create_placeholder_company_analysis(company)
            for ticker, company in {
                "NVDA": "NVIDIA (NVDA)",
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

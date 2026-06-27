from dataclasses import dataclass

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


from atlas.providers.base import CompanyDataProvider as CompanyAnalysisProvider  # noqa: E402


def __getattr__(name: str):
    if name == "MockCompanyAnalysisProvider":
        from atlas.providers.mock import MockCompanyAnalysisProvider

        return MockCompanyAnalysisProvider
    raise AttributeError(f"module 'atlas.analysis.company_analysis' has no attribute {name!r}")

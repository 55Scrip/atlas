import pytest

from atlas.analysis.company_analysis import CompanyAnalysis, MockCompanyAnalysisProvider
from atlas.analysis.growth import GrowthAnalysis
from atlas.analysis.macro import MacroAnalysis
from atlas.analysis.moat import MoatAnalysis
from atlas.analysis.quality import QualityAnalysis
from atlas.analysis.sentiment import SentimentAnalysis
from atlas.analysis.technicals import TechnicalAnalysis
from atlas.analysis.valuation import ValuationAnalysis


def test_company_analysis_aggregates_module_dataclasses():
    analysis = CompanyAnalysis(
        company="NVIDIA (NVDA)",
        valuation=ValuationAnalysis(72, "Valuation summary", ("Premium supported",), ("Expensive",)),
        quality=QualityAnalysis(92, "Quality summary", ("High margins",), ("High bar",)),
        growth=GrowthAnalysis(95, "Growth summary", ("Strong demand",), ("May normalize",)),
        moat=MoatAnalysis(90, "Moat summary", ("Ecosystem",), ("Competition",)),
        macro=MacroAnalysis(78, "Macro summary", ("AI spend",), ("Cyclical",)),
        technicals=TechnicalAnalysis(82, "Technicals summary", ("Trend",), ("Crowded",)),
        sentiment=SentimentAnalysis(80, "Sentiment summary", ("Positive",), ("Demanding",)),
    )

    assert analysis.company == "NVIDIA (NVDA)"
    assert analysis.valuation.score == 72
    assert analysis.quality.strengths == ("High margins",)


def test_mock_provider_returns_supported_companies():
    provider = MockCompanyAnalysisProvider()

    assert provider.get_company_analysis("nvda").company == "NVIDIA (NVDA)"
    assert provider.get_company_analysis("AAPL").company == "Apple (AAPL)"
    assert provider.get_company_analysis("MSFT").company == "Microsoft (MSFT)"
    assert provider.get_company_analysis("EVO").company == "Evolution (EVO)"


def test_mock_provider_rejects_unknown_ticker():
    provider = MockCompanyAnalysisProvider()

    with pytest.raises(LookupError, match="No mock company analysis available"):
        provider.get_company_analysis("TSM")

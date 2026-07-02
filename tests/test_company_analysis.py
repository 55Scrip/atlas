import pytest

from atlas.analysis.company_analysis import (
    CompanyAnalysis,
    GrowthAnalysis,
    MacroAnalysis,
    MoatAnalysis,
    MockCompanyAnalysisProvider,
    QualityAnalysis,
    SentimentAnalysis,
    TechnicalAnalysis,
    ValuationAnalysis,
)


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
    assert provider.get_company_analysis("AMD").company == "Advanced Micro Devices (AMD)"
    assert provider.get_company_analysis("AAPL").company == "Apple (AAPL)"
    assert provider.get_company_analysis("MSFT").company == "Microsoft (MSFT)"
    assert provider.get_company_analysis("EVO").company == "Evolution (EVO)"


def test_mock_provider_rejects_unknown_ticker():
    provider = MockCompanyAnalysisProvider()

    with pytest.raises(LookupError, match="No mock company analysis available"):
        provider.get_company_analysis("TSM")


# ── Sprint 139: placeholder submodules consolidated into company_analysis.py ──

def test_sprint139_placeholder_types_importable_from_company_analysis() -> None:
    """Sprint 139: all 7 placeholder types now live in atlas.analysis.company_analysis."""
    from atlas.analysis.company_analysis import (  # noqa: F401
        GrowthAnalysis,
        MacroAnalysis,
        MoatAnalysis,
        QualityAnalysis,
        SentimentAnalysis,
        TechnicalAnalysis,
        ValuationAnalysis,
    )
    assert True


def test_sprint139_placeholder_factories_importable_from_company_analysis() -> None:
    """Sprint 139: all 7 placeholder factories live in atlas.analysis.company_analysis."""
    from atlas.analysis.company_analysis import (  # noqa: F401
        placeholder_growth_analysis,
        placeholder_macro_analysis,
        placeholder_moat_analysis,
        placeholder_quality_analysis,
        placeholder_sentiment_analysis,
        placeholder_technical_analysis,
        placeholder_valuation_analysis,
    )
    assert True


def test_sprint139_deleted_placeholder_modules_not_importable() -> None:
    """Sprint 139: the 7 source files must be deleted and not importable."""
    import importlib
    deleted = [
        "atlas.analysis.growth",
        "atlas.analysis.macro",
        "atlas.analysis.moat",
        "atlas.analysis.quality",
        "atlas.analysis.sentiment",
        "atlas.analysis.technicals",
        "atlas.analysis.valuation",
    ]
    for mod in deleted:
        try:
            importlib.import_module(mod)
            assert False, f"{mod} must not be importable after Sprint 139"
        except ModuleNotFoundError:
            pass


def test_sprint139_placeholder_values_unchanged() -> None:
    """Sprint 139: consolidation must not alter placeholder values."""
    from atlas.analysis.company_analysis import (
        placeholder_growth_analysis,
        placeholder_macro_analysis,
        placeholder_moat_analysis,
        placeholder_quality_analysis,
        placeholder_sentiment_analysis,
        placeholder_technical_analysis,
        placeholder_valuation_analysis,
    )
    assert placeholder_growth_analysis("X").score == 95
    assert placeholder_macro_analysis("X").score == 78
    assert placeholder_moat_analysis("X").score == 90
    assert placeholder_quality_analysis("X").score == 92
    assert placeholder_sentiment_analysis("X").score == 80
    assert placeholder_technical_analysis("X").score == 82
    assert placeholder_valuation_analysis("X").score == 72

import pytest

from atlas.analysis.company_analysis import MockCompanyAnalysisProvider, create_placeholder_company_analysis
from atlas.analysis.report import build_investment_report
from atlas.analysis.scoring import RecommendationEngine, ScoringEngine, score_company


def test_scoring_engine_calculates_weighted_score_for_nvda():
    analysis = MockCompanyAnalysisProvider().get_company_analysis("NVDA")

    score = score_company(analysis)

    assert score == 86


def test_scoring_engine_uses_configurable_weights():
    analysis = create_placeholder_company_analysis("Test Co")
    engine = ScoringEngine(
        weights={
            "quality": 0.0,
            "growth": 0.0,
            "valuation": 1.0,
            "financial_strength": 0.0,
            "risk": 0.0,
        }
    )

    assert engine.score(analysis) == analysis.valuation.score


def test_scoring_engine_rejects_unknown_weights():
    with pytest.raises(ValueError, match="Unknown scoring module"):
        ScoringEngine(weights={"valuation": 1.0, "unknown": 1.0})


def test_recommendation_engine_default_thresholds():
    engine = RecommendationEngine()

    assert engine.recommend(90) == "Strong Buy"
    assert engine.recommend(75) == "Buy"
    assert engine.recommend(60) == "Hold"
    assert engine.recommend(40) == "Sell"
    assert engine.recommend(39) == "Strong Sell"


def test_build_investment_report_contains_required_fields():
    analysis = MockCompanyAnalysisProvider().get_company_analysis("NVDA")
    report = build_investment_report(analysis)

    assert report.company == "NVIDIA (NVDA)"
    assert report.overall_score == 86
    assert 0 <= report.confidence <= 100
    assert report.recommendation == "Buy"
    assert report.valuation.score == 72
    assert report.financial_strength.score == 91
    assert report.risk.confidence == 70

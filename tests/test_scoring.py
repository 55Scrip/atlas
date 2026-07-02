from atlas.analysis.company_analysis import MockCompanyAnalysisProvider
from atlas.analysis.engine import ThresholdRecommendationPolicy
from atlas.analysis.report import build_investment_report


def test_threshold_recommendation_policy_default_thresholds():
    policy = ThresholdRecommendationPolicy()

    assert policy.recommend(90) == "Strong Buy"
    assert policy.recommend(75) == "Buy"
    assert policy.recommend(60) == "Hold"
    assert policy.recommend(40) == "Sell"
    assert policy.recommend(39) == "Strong Sell"


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

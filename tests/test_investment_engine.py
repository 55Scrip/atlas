from atlas.analysis.company_analysis import MockCompanyAnalysisProvider
from atlas.analysis.engine import (
    AtlasInvestmentEngine,
    ScoreCategory,
    ThresholdRecommendationPolicy,
)


class FixedScorer:
    def __init__(self, score: int, confidence: int = 90) -> None:
        self._result = ScoreCategory(
            score=score,
            reasoning=f"Fixed score {score}",
            confidence=confidence,
        )

    def score(self, analysis):
        return self._result


def test_atlas_investment_engine_builds_report_from_required_categories():
    analysis = MockCompanyAnalysisProvider().get_company_analysis("NVDA")

    report = AtlasInvestmentEngine().analyze(analysis)

    assert report.company == "NVIDIA (NVDA)"
    assert report.atlas_score == 86
    assert report.overall_recommendation == "Buy"
    assert report.confidence == 80
    assert report.quality.score == 92
    assert report.growth.reasoning
    assert report.valuation.confidence == 74
    assert report.financial_strength.score == 91
    assert report.risk.score == 77


def test_atlas_investment_engine_accepts_replaceable_scoring_logic():
    analysis = MockCompanyAnalysisProvider().get_company_analysis("NVDA")
    scorers = {
        "quality": FixedScorer(100),
        "growth": FixedScorer(80),
        "valuation": FixedScorer(60),
        "financial_strength": FixedScorer(40),
        "risk": FixedScorer(20),
    }
    weights = {
        "quality": 1.0,
        "growth": 0.0,
        "valuation": 0.0,
        "financial_strength": 0.0,
        "risk": 0.0,
    }

    report = AtlasInvestmentEngine(category_scorers=scorers, weights=weights).analyze(analysis)

    assert report.atlas_score == 100
    assert report.quality.reasoning == "Fixed score 100"


def test_threshold_recommendation_policy_bands():
    policy = ThresholdRecommendationPolicy()

    assert policy.recommend(90) == "Strong Buy"
    assert policy.recommend(75) == "Buy"
    assert policy.recommend(60) == "Hold"
    assert policy.recommend(40) == "Sell"
    assert policy.recommend(39) == "Strong Sell"

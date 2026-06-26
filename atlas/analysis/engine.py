from dataclasses import dataclass
from typing import Protocol

from atlas.analysis.company_analysis import CompanyAnalysis


@dataclass(frozen=True)
class ScoreCategory:
    score: int
    reasoning: str
    confidence: int


@dataclass(frozen=True)
class InvestmentReport:
    company: str
    atlas_score: int
    overall_recommendation: str
    confidence: int
    quality: ScoreCategory
    growth: ScoreCategory
    valuation: ScoreCategory
    financial_strength: ScoreCategory
    risk: ScoreCategory

    @property
    def overall_score(self) -> int:
        return self.atlas_score

    @property
    def recommendation(self) -> str:
        return self.overall_recommendation


class CategoryScorer(Protocol):
    def score(self, analysis: CompanyAnalysis) -> ScoreCategory:
        """Return a deterministic score category for a company analysis."""


class RecommendationPolicy(Protocol):
    def recommend(self, atlas_score: int) -> str:
        """Return the overall recommendation for an Atlas Score."""


class QualityScorer:
    def score(self, analysis: CompanyAnalysis) -> ScoreCategory:
        return ScoreCategory(
            score=_clamp_score(analysis.quality.score),
            reasoning=analysis.quality.summary,
            confidence=88,
        )


class GrowthScorer:
    def score(self, analysis: CompanyAnalysis) -> ScoreCategory:
        return ScoreCategory(
            score=_clamp_score(analysis.growth.score),
            reasoning=analysis.growth.summary,
            confidence=86,
        )


class ValuationScorer:
    def score(self, analysis: CompanyAnalysis) -> ScoreCategory:
        return ScoreCategory(
            score=_clamp_score(analysis.valuation.score),
            reasoning=analysis.valuation.summary,
            confidence=74,
        )


class FinancialStrengthScorer:
    def score(self, analysis: CompanyAnalysis) -> ScoreCategory:
        score = round((analysis.quality.score * 0.65) + (analysis.moat.score * 0.35))
        return ScoreCategory(
            score=_clamp_score(score),
            reasoning=(
                "Financial strength is inferred from business quality and durability "
                "until balance sheet data is connected."
            ),
            confidence=72,
        )


class RiskScorer:
    def score(self, analysis: CompanyAnalysis) -> ScoreCategory:
        score = round(
            analysis.valuation.score * 0.35
            + analysis.macro.score * 0.25
            + analysis.technicals.score * 0.20
            + analysis.sentiment.score * 0.20
        )
        return ScoreCategory(
            score=_clamp_score(score),
            reasoning=(
                "Risk score blends valuation, macro, technical, and sentiment signals. "
                "Higher scores indicate a more favorable risk profile."
            ),
            confidence=70,
        )


class ThresholdRecommendationPolicy:
    def __init__(
        self,
        strong_buy_threshold: int = 90,
        buy_threshold: int = 75,
        hold_threshold: int = 60,
        sell_threshold: int = 40,
    ) -> None:
        if not 0 <= sell_threshold <= hold_threshold <= buy_threshold <= strong_buy_threshold <= 100:
            raise ValueError(
                "Thresholds must satisfy 0 <= sell <= hold <= buy <= strong_buy <= 100."
            )
        self.strong_buy_threshold = strong_buy_threshold
        self.buy_threshold = buy_threshold
        self.hold_threshold = hold_threshold
        self.sell_threshold = sell_threshold

    def recommend(self, atlas_score: int) -> str:
        score = _clamp_score(atlas_score)
        if score >= self.strong_buy_threshold:
            return "Strong Buy"
        if score >= self.buy_threshold:
            return "Buy"
        if score >= self.hold_threshold:
            return "Hold"
        if score >= self.sell_threshold:
            return "Sell"
        return "Strong Sell"


DEFAULT_CATEGORY_WEIGHTS: dict[str, float] = {
    "quality": 0.25,
    "growth": 0.25,
    "valuation": 0.20,
    "financial_strength": 0.15,
    "risk": 0.15,
}

DEFAULT_CATEGORY_SCORERS: dict[str, CategoryScorer] = {
    "quality": QualityScorer(),
    "growth": GrowthScorer(),
    "valuation": ValuationScorer(),
    "financial_strength": FinancialStrengthScorer(),
    "risk": RiskScorer(),
}


class AtlasInvestmentEngine:
    def __init__(
        self,
        category_scorers: dict[str, CategoryScorer] | None = None,
        weights: dict[str, float] | None = None,
        recommendation_policy: RecommendationPolicy | None = None,
    ) -> None:
        self.category_scorers = category_scorers or DEFAULT_CATEGORY_SCORERS.copy()
        self.weights = weights or DEFAULT_CATEGORY_WEIGHTS.copy()
        self.recommendation_policy = recommendation_policy or ThresholdRecommendationPolicy()
        self._validate_configuration()

    def analyze(self, analysis: CompanyAnalysis) -> InvestmentReport:
        categories = {
            category_name: scorer.score(analysis)
            for category_name, scorer in self.category_scorers.items()
        }
        atlas_score = self._aggregate_score(categories)
        confidence = self._aggregate_confidence(categories)
        return InvestmentReport(
            company=analysis.company,
            atlas_score=atlas_score,
            overall_recommendation=self.recommendation_policy.recommend(atlas_score),
            confidence=confidence,
            quality=categories["quality"],
            growth=categories["growth"],
            valuation=categories["valuation"],
            financial_strength=categories["financial_strength"],
            risk=categories["risk"],
        )

    def _aggregate_score(self, categories: dict[str, ScoreCategory]) -> int:
        total_weight = sum(self.weights.values())
        score = sum(categories[name].score * weight for name, weight in self.weights.items())
        return _clamp_score(round(score / total_weight))

    def _aggregate_confidence(self, categories: dict[str, ScoreCategory]) -> int:
        total_weight = sum(self.weights.values())
        confidence = sum(
            categories[name].confidence * weight for name, weight in self.weights.items()
        )
        return _clamp_score(round(confidence / total_weight))

    def _validate_configuration(self) -> None:
        required_categories = set(DEFAULT_CATEGORY_WEIGHTS)
        scorer_categories = set(self.category_scorers)
        weight_categories = set(self.weights)
        if scorer_categories != required_categories:
            missing = ", ".join(sorted(required_categories - scorer_categories))
            extra = ", ".join(sorted(scorer_categories - required_categories))
            raise ValueError(f"Invalid category scorers. Missing: {missing or '-'}; extra: {extra or '-'}.")
        if weight_categories != required_categories:
            missing = ", ".join(sorted(required_categories - weight_categories))
            extra = ", ".join(sorted(weight_categories - required_categories))
            raise ValueError(f"Invalid category weights. Missing: {missing or '-'}; extra: {extra or '-'}.")
        if any(weight < 0 for weight in self.weights.values()):
            raise ValueError("Category weights must be non-negative.")
        if sum(self.weights.values()) <= 0:
            raise ValueError("At least one category weight must be greater than zero.")


def _clamp_score(score: int) -> int:
    return max(0, min(100, score))

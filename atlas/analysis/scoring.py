from atlas.analysis.company_analysis import CompanyAnalysis
from atlas.analysis.engine import (
    DEFAULT_CATEGORY_WEIGHTS,
    AtlasInvestmentEngine,
    ThresholdRecommendationPolicy,
)


DEFAULT_WEIGHTS = DEFAULT_CATEGORY_WEIGHTS
MODULE_NAMES = tuple(DEFAULT_WEIGHTS.keys())


class ScoringEngine:
    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.weights = weights or DEFAULT_WEIGHTS.copy()
        self._validate_weights(self.weights)

    def score(self, analysis: CompanyAnalysis) -> int:
        return AtlasInvestmentEngine(weights=self.weights).analyze(analysis).atlas_score

    def confidence(self, analysis: CompanyAnalysis) -> int:
        return AtlasInvestmentEngine(weights=self.weights).analyze(analysis).confidence

    @staticmethod
    def _validate_weights(weights: dict[str, float]) -> None:
        if not weights:
            raise ValueError("At least one scoring weight is required.")
        unknown_modules = set(weights) - set(MODULE_NAMES)
        if unknown_modules:
            unknown = ", ".join(sorted(unknown_modules))
            raise ValueError(f"Unknown scoring module weights: {unknown}")
        if any(weight < 0 for weight in weights.values()):
            raise ValueError("Scoring weights must be non-negative.")
        if sum(weights.values()) <= 0:
            raise ValueError("At least one scoring weight must be greater than zero.")


class RecommendationEngine:
    def __init__(
        self,
        strong_buy_threshold: int = 90,
        buy_threshold: int = 75,
        hold_threshold: int = 60,
        sell_threshold: int = 40,
    ) -> None:
        self.policy = ThresholdRecommendationPolicy(
            strong_buy_threshold=strong_buy_threshold,
            buy_threshold=buy_threshold,
            hold_threshold=hold_threshold,
            sell_threshold=sell_threshold,
        )

    def recommend(self, overall_score: int) -> str:
        return self.policy.recommend(overall_score)


def score_company(analysis: CompanyAnalysis, weights: dict[str, float] | None = None) -> int:
    return ScoringEngine(weights=weights).score(analysis)


def _clamp_score(score: int) -> int:
    return max(0, min(100, score))

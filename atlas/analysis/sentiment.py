from dataclasses import dataclass


@dataclass(frozen=True)
class SentimentAnalysis:
    score: int
    summary: str
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]


def placeholder_sentiment_analysis(company: str) -> SentimentAnalysis:
    return SentimentAnalysis(
        score=80,
        summary=f"{company} has positive market sentiment with some crowding risk.",
        strengths=("Investor interest is strong", "Analyst narrative is supportive"),
        weaknesses=("Expectations are demanding",),
    )

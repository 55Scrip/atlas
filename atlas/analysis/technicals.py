from dataclasses import dataclass


@dataclass(frozen=True)
class TechnicalAnalysis:
    score: int
    summary: str
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]


def placeholder_technical_analysis(company: str) -> TechnicalAnalysis:
    return TechnicalAnalysis(
        score=82,
        summary=f"{company} shows constructive placeholder price action.",
        strengths=("Trend remains positive", "Relative strength is favorable"),
        weaknesses=("Momentum can reverse quickly after crowded moves",),
    )

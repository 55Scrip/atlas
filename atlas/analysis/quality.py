from dataclasses import dataclass


@dataclass(frozen=True)
class QualityAnalysis:
    score: int
    summary: str
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]


def placeholder_quality_analysis(company: str) -> QualityAnalysis:
    return QualityAnalysis(
        score=92,
        summary=f"{company} has excellent profitability and operating discipline.",
        strengths=("High gross margins", "Strong returns on invested capital"),
        weaknesses=("Execution expectations are elevated",),
    )

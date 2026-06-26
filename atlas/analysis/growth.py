from dataclasses import dataclass


@dataclass(frozen=True)
class GrowthAnalysis:
    score: int
    summary: str
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]


def placeholder_growth_analysis(company: str) -> GrowthAnalysis:
    return GrowthAnalysis(
        score=95,
        summary=f"{company} has a strong near-term growth profile.",
        strengths=("Revenue momentum remains high", "Large addressable market"),
        weaknesses=("Growth may normalize from exceptional levels",),
    )

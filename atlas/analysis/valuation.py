from dataclasses import dataclass


@dataclass(frozen=True)
class ValuationAnalysis:
    score: int
    summary: str
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]


def placeholder_valuation_analysis(company: str) -> ValuationAnalysis:
    return ValuationAnalysis(
        score=72,
        summary=f"{company} screens expensive, but the premium is partly supported by growth.",
        strengths=("Scale supports premium multiples", "Strong earnings power"),
        weaknesses=("Limited margin of safety", "Multiple compression risk"),
    )

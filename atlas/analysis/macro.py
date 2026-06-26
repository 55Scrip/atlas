from dataclasses import dataclass


@dataclass(frozen=True)
class MacroAnalysis:
    score: int
    summary: str
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]


def placeholder_macro_analysis(company: str) -> MacroAnalysis:
    return MacroAnalysis(
        score=78,
        summary=f"{company} is exposed to supportive secular demand, with cyclical risk.",
        strengths=("AI infrastructure spending is supportive", "Enterprise demand remains broad"),
        weaknesses=("Rate sensitivity can pressure long-duration equities", "Supply cycles can turn"),
    )

from dataclasses import dataclass


@dataclass(frozen=True)
class MoatAnalysis:
    score: int
    summary: str
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]


def placeholder_moat_analysis(company: str) -> MoatAnalysis:
    return MoatAnalysis(
        score=90,
        summary=f"{company} benefits from strong competitive positioning.",
        strengths=("Ecosystem advantages", "Customer switching costs"),
        weaknesses=("Competition is intensifying",),
    )

from dataclasses import dataclass


# ── Placeholder analysis submodules (consolidated Sprint 139) ─────────────────
# Formerly in: growth.py, macro.py, moat.py, quality.py, sentiment.py,
#              technicals.py, valuation.py — each 18 lines, zero external callers.

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


# ── Company Analysis aggregate ────────────────────────────────────────────────

@dataclass(frozen=True)
class CompanyAnalysis:
    company: str
    valuation: ValuationAnalysis
    quality: QualityAnalysis
    growth: GrowthAnalysis
    moat: MoatAnalysis
    macro: MacroAnalysis
    technicals: TechnicalAnalysis
    sentiment: SentimentAnalysis


def create_placeholder_company_analysis(company: str) -> CompanyAnalysis:
    return CompanyAnalysis(
        company=company,
        valuation=placeholder_valuation_analysis(company),
        quality=placeholder_quality_analysis(company),
        growth=placeholder_growth_analysis(company),
        moat=placeholder_moat_analysis(company),
        macro=placeholder_macro_analysis(company),
        technicals=placeholder_technical_analysis(company),
        sentiment=placeholder_sentiment_analysis(company),
    )


from atlas.providers.base import CompanyDataProvider as CompanyAnalysisProvider  # noqa: E402


def __getattr__(name: str):
    if name == "MockCompanyAnalysisProvider":
        from atlas.providers.mock import MockCompanyAnalysisProvider

        return MockCompanyAnalysisProvider
    raise AttributeError(f"module 'atlas.analysis.company_analysis' has no attribute {name!r}")

from atlas.analysis.company_analysis import CompanyAnalysis
from atlas.analysis.engine import AtlasInvestmentEngine, InvestmentReport


def build_investment_report(
    analysis: CompanyAnalysis,
    engine: AtlasInvestmentEngine | None = None,
) -> InvestmentReport:
    investment_engine = engine or AtlasInvestmentEngine()
    return investment_engine.analyze(analysis)


def render_investment_report(report: InvestmentReport) -> str:
    sections = [
        "Investment Report",
        "",
        f"Company: {report.company}",
        _score_line("Atlas Score", report.atlas_score),
        _score_line("Confidence", report.confidence),
        f"Overall Recommendation: {report.overall_recommendation}",
        "",
    ]
    for label, module in (
        ("Quality", report.quality),
        ("Growth", report.growth),
        ("Valuation", report.valuation),
        ("Financial Strength", report.financial_strength),
        ("Risk", report.risk),
    ):
        sections.extend(
            [
                f"{label} ({module.score}/100)",
                f"Reasoning: {module.reasoning}",
                _score_line("Confidence", module.confidence),
                "",
            ]
        )
    return "\n".join(sections).strip()


def render_company_analysis_report(analysis: CompanyAnalysis) -> str:
    report = build_investment_report(analysis)
    return render_investment_report(report)


def _score_line(label: str, score: int) -> str:
    return f"{label}: {score}/100"


def render_legacy_company_analysis_report(analysis: CompanyAnalysis) -> str:
    return "\n".join(
        [
            f"Company: {analysis.company}",
            "",
            render_company_analysis_report(analysis),
        ]
    )

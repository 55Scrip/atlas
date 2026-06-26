from atlas.analysis.company_analysis import MockCompanyAnalysisProvider
from atlas.analysis.explanation import (
    explain_investment_report,
    render_investment_explanation,
)
from atlas.analysis.report import build_investment_report


def test_explanation_engine_generates_deterministic_sections():
    analysis = MockCompanyAnalysisProvider().get_company_analysis("NVDA")
    report = build_investment_report(analysis)

    explanation = explain_investment_report(report)

    assert "NVIDIA (NVDA)" in explanation.bull_case
    assert "86/100" in explanation.bull_case
    assert "valuation" in explanation.bear_case.lower()
    assert len(explanation.key_strengths) == 3
    assert len(explanation.key_risks) == 3
    assert "Valuation is a moderate concern" in explanation.valuation_concern
    assert len(explanation.mind_changers) == 3
    assert "80/100" in explanation.confidence_explanation


def test_render_investment_explanation_includes_required_sections():
    analysis = MockCompanyAnalysisProvider().get_company_analysis("NVDA")
    report = build_investment_report(analysis)
    explanation = explain_investment_report(report)

    rendered = render_investment_explanation(explanation)

    assert "Bull Case" in rendered
    assert "Bear Case" in rendered
    assert "Key Strengths" in rendered
    assert "Key Risks" in rendered
    assert "Valuation Concern" in rendered
    assert "What Could Change Atlas' Mind" in rendered
    assert "Confidence Explanation" in rendered

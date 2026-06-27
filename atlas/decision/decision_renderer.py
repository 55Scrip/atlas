from atlas.decision.decision_result import DecisionResult


def render_decision_result(result: DecisionResult) -> str:
    lines = [
        "Atlas Decision",
        "",
        f"Ticker: {result.ticker}",
        f"Decision: {result.action.value}",
        f"Has Enough Information: {'Yes' if result.has_enough_information else 'No'}",
        _score_line("Decision Quality", result.decision_quality),
        _score_line("Portfolio Fit", result.portfolio_fit),
        _score_line("Capital Allocation Quality", result.capital_allocation_quality),
        _score_line("Confidence", result.confidence),
        "",
        "Reasoning",
        result.reasoning,
        "",
        "Next Best Action",
        result.next_best_action,
        "",
        "What Could Change My Mind",
        result.what_could_change_my_mind,
        "",
        "Uncertainty",
        result.uncertainty,
    ]
    return "\n".join(lines)


def _score_line(label: str, score: int) -> str:
    return f"{label}: {score}/100"

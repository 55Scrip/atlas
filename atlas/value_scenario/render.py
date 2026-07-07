"""Read-only summary renderer for ValueScenarioReview.

No calculations. No forecasts. No recommendations. No persistence.
Renders only information already present in a validated ValueScenarioReview.
"""

from __future__ import annotations

from typing import List

from atlas.value_scenario.schema import (
    HoldingScenario,
    PortfolioScenario,
    ScenarioSafetyBoundary,
    ValueScenarioReview,
)

_SAFETY_LABELS = [
    ("no_single_point_targets", "No single-point targets"),
    ("no_action_calls", "No action calls"),
    ("no_execution_instructions", "No execution instructions"),
    ("no_prediction_certainty", "No prediction certainty"),
    ("assumptions_required", "Assumptions required"),
    ("evidence_quality_required", "Evidence quality required"),
    ("uncertainty_required", "Uncertainty required"),
    ("change_triggers_required", "Change triggers required"),
]

_REMINDER = (
    "Atlas helps structure judgment.\n"
    "It does not predict future returns."
)


def _section(title: str, lines: List[str]) -> str:
    return title + "\n" + "\n".join(lines)


def _format_range(lower: float, upper: float) -> str:
    def _fmt(v: float) -> str:
        s = f"{v:+.0f}%" if v == int(v) else f"{v:+.1f}%"
        return s.replace("+", "").replace("+-", "-") if v < 0 else s.lstrip("+")

    lo = f"{lower:+.0f}%" if lower == int(lower) else f"{lower:+.1f}%"
    hi = f"{upper:+.0f}%" if upper == int(upper) else f"{upper:+.1f}%"
    # strip leading + for display
    lo = lo.lstrip("+") if lo.startswith("+") else lo
    hi = hi.lstrip("+") if hi.startswith("+") else hi
    return f"{lo} to {hi}"


def _render_holding_scenarios(holding_scenarios: List[HoldingScenario]) -> List[str]:
    lines: List[str] = []
    for hs in holding_scenarios:
        if len(holding_scenarios) > 1:
            subj = hs.subject.display_name
            if hs.subject.ticker:
                subj += f" ({hs.subject.ticker})"
            lines.append(subj)
        for rng in hs.ranges:
            horizon_label = f" ({rng.horizon})" if len(hs.ranges) > 3 else ""
            case = rng.case_type.title()
            lines.append(f"{case}{horizon_label}".rstrip())
            lines.append(_format_range(rng.lower_percent, rng.upper_percent))
            lines.append("")
        if hs.evidence_quality:
            lines.append(f"Evidence Quality\n{hs.evidence_quality}")
            lines.append("")
        if hs.confidence:
            lines.append(f"Confidence\n{hs.confidence}")
            lines.append("")
    return lines


def _render_portfolio_scenario(ps: PortfolioScenario) -> List[str]:
    lines: List[str] = []
    for rng in ps.ranges:
        case = rng.case_type.title()
        lines.append(case)
        lines.append(_format_range(rng.lower_percent, rng.upper_percent))
        lines.append("")
    if ps.evidence_quality:
        lines.append(f"Evidence Quality\n{ps.evidence_quality}")
        lines.append("")
    if ps.confidence:
        lines.append(f"Confidence\n{ps.confidence}")
        lines.append("")
    if ps.weighted_contributions:
        lines.append("Portfolio Contributions")
        for c in ps.weighted_contributions:
            weight_pct = f"{c.portfolio_weight * 100:.0f}%"
            ticker = f" ({c.ticker})" if c.ticker else ""
            lines.append(f"• {c.display_name}{ticker} — {weight_pct} — {c.range_impact_level}")
        lines.append("")
    if ps.concentration_sensitivity:
        lines.append(f"Concentration Note\n{ps.concentration_sensitivity}")
        lines.append("")
    return lines


def _render_safety_boundary(sb: ScenarioSafetyBoundary) -> List[str]:
    lines: List[str] = []
    for field, label in _SAFETY_LABELS:
        val = getattr(sb, field)
        mark = "✓" if val else "✗"
        lines.append(f"{mark} {label}")
    return lines


def render_value_scenario_summary(review: ValueScenarioReview) -> str:
    """Render a read-only neutral summary of a ValueScenarioReview.

    Only renders information present in the review. No calculations.
    No recommendations. No forecasts.
    """
    parts: List[str] = []

    parts.append("Value Scenario Review")
    parts.append("")

    # Review type
    parts.append("Review Type")
    parts.append(review.review_type)
    parts.append("")

    # Subject
    subj = review.subject.display_name.strip()
    if review.subject.ticker:
        subj += f" ({review.subject.ticker})"
    elif review.subject.portfolio_id:
        subj += f" [{review.subject.portfolio_id}]"
    parts.append("Subject")
    parts.append(subj)
    parts.append("")

    # Time horizons
    if review.time_horizons:
        parts.append("Time Horizons")
        for h in review.time_horizons:
            parts.append(f"• {h}")
        parts.append("")

    # Scenario ranges
    parts.append("Scenario Ranges")
    parts.append("")

    if review.holding_scenarios:
        parts.extend(_render_holding_scenarios(review.holding_scenarios))
    elif review.portfolio_scenario is not None:
        parts.extend(_render_portfolio_scenario(review.portfolio_scenario))

    # Counts
    parts.append(f"Assumptions\n{len(review.assumptions)}")
    parts.append("")
    parts.append(f"Evidence Items\n{len(review.evidence_items)}")
    parts.append("")
    parts.append(f"Change Triggers\n{len(review.change_triggers)}")
    parts.append("")

    # Safety boundary
    parts.append("Safety Boundary")
    parts.append("")
    parts.extend(_render_safety_boundary(review.safety_boundary))
    parts.append("")

    # Reminder
    parts.append("Reminder")
    parts.append("")
    parts.append(_REMINDER)

    return "\n".join(parts)

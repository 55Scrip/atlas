from dataclasses import dataclass

from atlas.analysis.scores import clamp_score


@dataclass(frozen=True)
class MarketSignal:
    name: str
    status: str
    value: str
    interpretation: str


@dataclass(frozen=True)
class MarketSignalGroup:
    name: str
    status: str
    score: int
    key_signals: tuple[MarketSignal, ...]
    interpretation: str
    monitoring_items: tuple[str, ...]
    what_would_improve: tuple[str, ...]
    what_would_worsen: tuple[str, ...]


@dataclass(frozen=True)
class MarketHealthReport:
    overall_market_health: str
    overall_risk_level: str
    overall_score: int
    signal_groups: tuple[MarketSignalGroup, ...]
    atlas_view: str
    what_could_change_view: tuple[str, ...]


class MarketHealthEngine:
    def analyze(
        self,
        signal_groups: tuple[MarketSignalGroup, ...] | None = None,
    ) -> MarketHealthReport:
        groups = signal_groups or _default_signal_groups()
        overall_score = _overall_score(groups)
        return MarketHealthReport(
            overall_market_health=_market_health(overall_score),
            overall_risk_level=_risk_level(overall_score),
            overall_score=overall_score,
            signal_groups=groups,
            atlas_view=_atlas_view(overall_score, groups),
            what_could_change_view=_what_could_change_view(groups),
        )


def render_market_health(report: MarketHealthReport) -> str:
    lines = [
        "Market Health Report",
        "",
        f"Overall Market Health: {report.overall_market_health}",
        f"Overall Risk Level: {report.overall_risk_level}",
        f"Overall Score: {report.overall_score}/100",
        "",
    ]
    section_titles = {
        "Credit": "Credit Conditions",
        "Liquidity": "Liquidity Conditions",
        "Macro": "Macro Conditions",
        "Volatility": "Volatility",
        "Market Breadth": "Market Breadth",
    }
    for group in report.signal_groups:
        lines.extend(_render_group(group, section_titles.get(group.name, group.name)))
    lines.extend(
        [
            "Atlas View",
            report.atlas_view,
            "",
            "What Could Change Atlas' View",
            *_render_list(report.what_could_change_view),
            "",
            "Research Framing",
            "This is market context, not investment advice or a market prediction.",
        ]
    )
    return "\n".join(lines)


def _default_signal_groups() -> tuple[MarketSignalGroup, ...]:
    return (
        MarketSignalGroup(
            name="Credit",
            status="Watchful",
            score=68,
            key_signals=(
                MarketSignal(
                    name="High yield spreads",
                    status="Contained",
                    value="Placeholder: moderately above calm-market levels",
                    interpretation="Lower-quality borrowers are not signaling severe stress.",
                ),
                MarketSignal(
                    name="Investment grade spreads",
                    status="Stable",
                    value="Placeholder: near normal range",
                    interpretation="Higher-quality corporate funding remains available.",
                ),
                MarketSignal(
                    name="Default rates",
                    status="Contained",
                    value="Placeholder: not yet recessionary",
                    interpretation="Credit losses are visible but not broadly disruptive.",
                ),
                MarketSignal(
                    name="Bank lending standards",
                    status="Tight",
                    value="Placeholder: restrictive lending posture",
                    interpretation="Credit availability is a constraint for weaker borrowers.",
                ),
            ),
            interpretation=(
                "Credit conditions look usable but no longer effortless. Atlas treats "
                "this as a watch area because lending standards can tighten before "
                "equity markets fully price the impact."
            ),
            monitoring_items=(
                "High yield option-adjusted spreads",
                "Investment grade spreads",
                "Default rate trend",
                "Senior loan officer lending standards",
            ),
            what_would_improve=(
                "High yield spreads narrow without a rise in default risk.",
                "Bank lending standards ease.",
                "Default rates stabilize or fall.",
            ),
            what_would_worsen=(
                "High yield spreads widen quickly.",
                "Investment grade spreads begin to gap wider.",
                "Default rates rise across more sectors.",
            ),
        ),
        MarketSignalGroup(
            name="Liquidity",
            status="Adequate",
            score=62,
            key_signals=(
                MarketSignal(
                    name="Cash availability",
                    status="Adequate",
                    value="Placeholder: liquidity present but selective",
                    interpretation="Strong issuers can still access capital.",
                ),
                MarketSignal(
                    name="Funding markets",
                    status="Orderly",
                    value="Placeholder: no broad funding freeze",
                    interpretation="Market plumbing does not currently suggest crisis.",
                ),
                MarketSignal(
                    name="Central bank posture",
                    status="Restrictive",
                    value="Placeholder: policy still cautious",
                    interpretation="Liquidity is not being aggressively added yet.",
                ),
            ),
            interpretation=(
                "Liquidity looks functional, but not abundant. Atlas would avoid "
                "assuming easy money conditions until funding signals broaden."
            ),
            monitoring_items=(
                "Funding stress indicators",
                "Central bank balance sheet direction",
                "Treasury market functioning",
                "Capital issuance windows",
            ),
            what_would_improve=(
                "Funding stress stays low.",
                "Capital markets remain open for a wider set of issuers.",
                "Policy becomes less restrictive without reigniting inflation.",
            ),
            what_would_worsen=(
                "Funding markets become disorderly.",
                "Issuance windows close for lower-quality borrowers.",
                "Liquidity drains accelerate.",
            ),
        ),
        MarketSignalGroup(
            name="Macro",
            status="Mixed",
            score=58,
            key_signals=(
                MarketSignal(
                    name="Growth trend",
                    status="Slowing but positive",
                    value="Placeholder: uneven growth",
                    interpretation="Economic momentum is not collapsing but is uneven.",
                ),
                MarketSignal(
                    name="Inflation trend",
                    status="Cooling slowly",
                    value="Placeholder: improving but sticky",
                    interpretation="Inflation relief helps, but stickiness limits confidence.",
                ),
                MarketSignal(
                    name="Rate environment",
                    status="Restrictive",
                    value="Placeholder: rates remain a valuation headwind",
                    interpretation="Discount rates can still pressure long-duration assets.",
                ),
            ),
            interpretation=(
                "Macro conditions are mixed. Atlas sees enough resilience for normal "
                "research activity, but not enough clarity to ignore downside risk."
            ),
            monitoring_items=(
                "Inflation trend",
                "Employment resilience",
                "Earnings revisions",
                "Interest rate path",
            ),
            what_would_improve=(
                "Inflation falls while growth remains durable.",
                "Earnings revisions turn positive across more sectors.",
                "Rates decline for healthy reasons.",
            ),
            what_would_worsen=(
                "Inflation reaccelerates.",
                "Employment weakens sharply.",
                "Earnings revisions deteriorate broadly.",
            ),
        ),
        MarketSignalGroup(
            name="Volatility",
            status="Normalizing",
            score=64,
            key_signals=(
                MarketSignal(
                    name="Equity volatility",
                    status="Contained",
                    value="Placeholder: below stress levels",
                    interpretation="Volatility is not signaling broad panic.",
                ),
                MarketSignal(
                    name="Rate volatility",
                    status="Elevated",
                    value="Placeholder: still choppy",
                    interpretation="Rates can continue to disturb equity valuations.",
                ),
                MarketSignal(
                    name="Drawdown behavior",
                    status="Manageable",
                    value="Placeholder: pullbacks remain orderly",
                    interpretation="Price action suggests stress is present but contained.",
                ),
            ),
            interpretation=(
                "Volatility is manageable, though not fully calm. Atlas would still "
                "favor staged decisions over abrupt allocation changes."
            ),
            monitoring_items=(
                "VIX trend",
                "Rate volatility",
                "Index drawdowns",
                "Cross-asset correlation spikes",
            ),
            what_would_improve=(
                "Volatility falls while breadth improves.",
                "Rate volatility stabilizes.",
                "Drawdowns remain shallow and sector rotation stays orderly.",
            ),
            what_would_worsen=(
                "Volatility rises with widening credit spreads.",
                "Rate volatility shocks equity valuations.",
                "Multiple asset classes sell off together.",
            ),
        ),
        MarketSignalGroup(
            name="Market Breadth",
            status="Narrow",
            score=55,
            key_signals=(
                MarketSignal(
                    name="Leadership breadth",
                    status="Concentrated",
                    value="Placeholder: gains led by fewer large companies",
                    interpretation="Narrow leadership can make index strength fragile.",
                ),
                MarketSignal(
                    name="Sector participation",
                    status="Uneven",
                    value="Placeholder: mixed sector confirmation",
                    interpretation="A healthier market would show broader participation.",
                ),
                MarketSignal(
                    name="Advance-decline behavior",
                    status="Soft",
                    value="Placeholder: breadth not confirming strongly",
                    interpretation="Weak breadth can hide risk below headline indexes.",
                ),
            ),
            interpretation=(
                "Market breadth is the weakest group. Atlas treats narrow leadership "
                "as a fragility signal because index gains may depend on fewer stocks."
            ),
            monitoring_items=(
                "Equal-weight versus cap-weight index performance",
                "Sector participation",
                "Advance-decline lines",
                "Percentage of stocks above moving averages",
            ),
            what_would_improve=(
                "Equal-weight indexes begin outperforming.",
                "More sectors participate in uptrends.",
                "Advance-decline lines confirm index strength.",
            ),
            what_would_worsen=(
                "Leadership narrows further.",
                "Equal-weight indexes lag sharply.",
                "More stocks break below key moving averages.",
            ),
        ),
    )


def _render_group(group: MarketSignalGroup, title: str) -> list[str]:
    lines = [
        title,
        f"Status: {group.status}",
        f"Score: {group.score}/100",
        "Key Signals",
    ]
    for signal in group.key_signals:
        lines.append(
            (
                f"- {signal.name}: {signal.status}; {signal.value}. "
                f"{signal.interpretation}"
            )
        )
    lines.extend(
        [
            "Interpretation",
            group.interpretation,
            "What Atlas Is Monitoring",
            *_render_list(group.monitoring_items),
            "What Would Improve The Signal",
            *_render_list(group.what_would_improve),
            "What Would Worsen The Signal",
            *_render_list(group.what_would_worsen),
            "",
        ]
    )
    return lines


def _overall_score(groups: tuple[MarketSignalGroup, ...]) -> int:
    if not groups:
        return 0
    average = sum(group.score for group in groups) / len(groups)
    return clamp_score(round(average))


def _market_health(score: int) -> str:
    if score >= 80:
        return "Healthy"
    if score >= 65:
        return "Improving"
    if score >= 50:
        return "Fragile"
    return "Stressed"


def _risk_level(score: int) -> str:
    if score >= 80:
        return "Low"
    if score >= 65:
        return "Moderate"
    if score >= 50:
        return "Elevated"
    return "High"


def _atlas_view(score: int, groups: tuple[MarketSignalGroup, ...]) -> str:
    weakest_group = min(groups, key=lambda group: group.score, default=None)
    if score >= 80:
        base = "Market health looks healthy, with broad support across signal groups."
    elif score >= 65:
        base = "Market health looks improving, but Atlas would still monitor confirmation."
    elif score >= 50:
        base = (
            "Market health looks fragile: conditions are functional, but several "
            "signals need confirmation."
        )
    else:
        base = (
            "Market health looks stressed, so Atlas would emphasize liquidity and "
            "balance sheet quality."
        )
    if weakest_group is None:
        return base
    return f"{base} The weakest current signal group is {weakest_group.name}."


def _what_could_change_view(groups: tuple[MarketSignalGroup, ...]) -> tuple[str, ...]:
    weakest_groups = tuple(sorted(groups, key=lambda group: group.score)[:2])
    improvements = tuple(
        item for group in weakest_groups for item in group.what_would_improve[:1]
    )
    worsenings = tuple(item for group in groups for item in group.what_would_worsen[:1])
    return (
        *improvements,
        (
            "A simultaneous deterioration in credit, liquidity, and breadth would "
            "make Atlas more cautious."
        ),
        *worsenings[:2],
    )


def _render_list(items: tuple[str, ...]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]

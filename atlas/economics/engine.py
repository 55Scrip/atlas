from dataclasses import dataclass

from atlas.analysis.scores import clamp_score


@dataclass(frozen=True)
class EconomicSignal:
    name: str
    current_state: str
    direction: str
    importance: int
    confidence: int
    why_it_matters: str
    score: int


@dataclass(frozen=True)
class EconomicSignalGroup:
    name: str
    score: int
    status: str
    signals: tuple[EconomicSignal, ...]
    interpretation: str


@dataclass(frozen=True)
class EconomicSignalAnalysis:
    overall_economic_health: str
    overall_risk_score: int
    signal_groups: tuple[EconomicSignalGroup, ...]
    strongest_positive_signals: tuple[EconomicSignal, ...]
    strongest_negative_signals: tuple[EconomicSignal, ...]
    watching_most_closely: tuple[str, ...]
    what_would_improve_outlook: tuple[str, ...]
    what_would_worsen_outlook: tuple[str, ...]
    conclusion: str


class EconomicSignalsEngine:
    def analyze(
        self,
        signal_groups: tuple[EconomicSignalGroup, ...] | None = None,
    ) -> EconomicSignalAnalysis:
        groups = signal_groups or _default_signal_groups()
        risk_score = _overall_risk_score(groups)
        health = _overall_health(risk_score)
        positive = _strongest_positive_signals(groups)
        negative = _strongest_negative_signals(groups)
        return EconomicSignalAnalysis(
            overall_economic_health=health,
            overall_risk_score=risk_score,
            signal_groups=groups,
            strongest_positive_signals=positive,
            strongest_negative_signals=negative,
            watching_most_closely=_watching_most_closely(groups, negative),
            what_would_improve_outlook=_what_would_improve_outlook(groups),
            what_would_worsen_outlook=_what_would_worsen_outlook(groups),
            conclusion=_conclusion(health, risk_score, groups, positive, negative),
        )


def render_economic_signal_analysis(analysis: EconomicSignalAnalysis) -> str:
    lines = [
        "Economic Signals Analysis",
        "",
        f"Overall Economic Health: {analysis.overall_economic_health}",
        f"Overall Risk Score: {analysis.overall_risk_score}/100",
        "",
        "Conclusion",
        analysis.conclusion,
        "",
        "Signal Groups",
    ]
    for group in analysis.signal_groups:
        lines.extend(_render_group(group))
    lines.extend(
        [
            "Strongest Positive Signals",
            *_render_signal_list(analysis.strongest_positive_signals),
            "",
            "Strongest Negative Signals",
            *_render_signal_list(analysis.strongest_negative_signals),
            "",
            "What Atlas Is Watching Most Closely",
            *_render_list(analysis.watching_most_closely),
            "",
            "What Would Improve The Outlook",
            *_render_list(analysis.what_would_improve_outlook),
            "",
            "What Would Worsen The Outlook",
            *_render_list(analysis.what_would_worsen_outlook),
            "",
            "Research Framing",
            "This is deterministic economic context, not forecasting or buy/sell advice.",
        ]
    )
    return "\n".join(lines)


def _default_signal_groups() -> tuple[EconomicSignalGroup, ...]:
    raw_groups = (
        (
            "Credit Markets",
            (
                EconomicSignal(
                    "High Yield spreads",
                    "Moderately above calm-market levels",
                    "Stable",
                    92,
                    78,
                    "High yield spreads show stress in lower-quality corporate credit.",
                    62,
                ),
                EconomicSignal(
                    "Investment Grade spreads",
                    "Near normal range",
                    "Stable",
                    82,
                    80,
                    "Investment grade spreads show access to capital for stronger issuers.",
                    72,
                ),
                EconomicSignal(
                    "Default rates",
                    "Contained but rising slowly",
                    "Worsening",
                    88,
                    74,
                    "Default rates show whether credit losses are becoming systemic.",
                    58,
                ),
                EconomicSignal(
                    "Bank lending standards",
                    "Restrictive",
                    "Tightening",
                    90,
                    76,
                    "Lending standards affect credit availability for households and firms.",
                    46,
                ),
            ),
            (
                "Credit is usable but watchful. Tight lending standards are the main "
                "constraint despite contained spreads."
            ),
        ),
        (
            "Liquidity",
            (
                EconomicSignal(
                    "Central bank balance sheets",
                    "Restrictive posture",
                    "Contracting",
                    84,
                    72,
                    "Central bank liquidity influences funding conditions and risk appetite.",
                    52,
                ),
                EconomicSignal(
                    "Money supply",
                    "Stabilizing after weakness",
                    "Improving",
                    76,
                    70,
                    "Money supply can indicate whether liquidity is expanding or contracting.",
                    60,
                ),
                EconomicSignal(
                    "Repo stress",
                    "Orderly",
                    "Stable",
                    86,
                    78,
                    "Repo stress can reveal pressure in short-term funding markets.",
                    76,
                ),
                EconomicSignal(
                    "Dollar liquidity",
                    "Adequate but selective",
                    "Stable",
                    82,
                    74,
                    "Dollar liquidity affects global funding and cross-border financial stress.",
                    66,
                ),
            ),
            (
                "Liquidity looks functional rather than abundant. Funding markets are "
                "orderly, but central bank posture remains a headwind."
            ),
        ),
        (
            "Interest Rates",
            (
                EconomicSignal(
                    "Yield curve",
                    "Still restrictive",
                    "Stable",
                    88,
                    76,
                    "The yield curve reflects growth expectations and policy tightness.",
                    48,
                ),
                EconomicSignal(
                    "Real rates",
                    "Elevated",
                    "Stable",
                    84,
                    74,
                    "Real rates influence valuation multiples and borrowing costs.",
                    50,
                ),
                EconomicSignal(
                    "Policy rate trend",
                    "Restrictive but no longer accelerating",
                    "Improving",
                    86,
                    76,
                    "Policy rate direction shapes financial conditions and discount rates.",
                    58,
                ),
            ),
            (
                "Rates remain restrictive. Atlas sees less acceleration risk, but real "
                "rates and the curve still pressure long-duration assets."
            ),
        ),
        (
            "Volatility",
            (
                EconomicSignal(
                    "VIX",
                    "Contained",
                    "Stable",
                    78,
                    80,
                    "VIX captures equity market volatility and stress expectations.",
                    72,
                ),
                EconomicSignal(
                    "MOVE Index",
                    "Elevated",
                    "Worsening",
                    82,
                    70,
                    "MOVE captures bond market volatility, which can spill into equities.",
                    54,
                ),
                EconomicSignal(
                    "Cross-asset volatility",
                    "Mixed",
                    "Stable",
                    80,
                    70,
                    "Cross-asset volatility shows whether stress is spreading across markets.",
                    60,
                ),
            ),
            (
                "Equity volatility is contained, but rate volatility remains a key "
                "source of fragility."
            ),
        ),
        (
            "Macro",
            (
                EconomicSignal(
                    "PMI",
                    "Near expansion threshold",
                    "Improving",
                    82,
                    72,
                    "PMI indicates whether business activity is expanding or contracting.",
                    62,
                ),
                EconomicSignal(
                    "Unemployment trend",
                    "Low but softening",
                    "Worsening",
                    88,
                    76,
                    "Unemployment trend signals labor market durability or deterioration.",
                    58,
                ),
                EconomicSignal(
                    "Inflation trend",
                    "Cooling slowly",
                    "Improving",
                    90,
                    78,
                    "Inflation affects policy rates, margins, and consumer purchasing power.",
                    64,
                ),
                EconomicSignal(
                    "GDP trend",
                    "Positive but uneven",
                    "Stable",
                    80,
                    72,
                    "GDP trend shows the broad pace of economic growth.",
                    60,
                ),
            ),
            (
                "Macro signals are mixed. Inflation improvement helps, while labor "
                "softening keeps the outlook from being clearly healthy."
            ),
        ),
        (
            "Market Breadth",
            (
                EconomicSignal(
                    "Advance/Decline",
                    "Soft confirmation",
                    "Stable",
                    76,
                    68,
                    "Advance/decline breadth shows whether index moves are broadly supported.",
                    54,
                ),
                EconomicSignal(
                    "New highs vs lows",
                    "Narrow leadership",
                    "Worsening",
                    78,
                    68,
                    "New highs versus lows shows whether participation is expanding.",
                    50,
                ),
                EconomicSignal(
                    "Sector participation",
                    "Uneven",
                    "Stable",
                    74,
                    70,
                    "Sector participation shows whether gains depend on too few areas.",
                    55,
                ),
            ),
            (
                "Market breadth remains the weakest confirmation signal. Atlas treats "
                "narrow participation as a fragility warning."
            ),
        ),
    )
    return tuple(
        _group_from_raw(name, signals, interpretation)
        for name, signals, interpretation in raw_groups
    )


def _group_from_raw(
    name: str,
    signals: tuple[EconomicSignal, ...],
    interpretation: str,
) -> EconomicSignalGroup:
    score = _group_score(signals)
    return EconomicSignalGroup(
        name=name,
        score=score,
        status=_group_status(score),
        signals=signals,
        interpretation=interpretation,
    )


def _group_score(signals: tuple[EconomicSignal, ...]) -> int:
    total_importance = sum(signal.importance for signal in signals)
    weighted_score = sum(signal.score * signal.importance for signal in signals)
    return clamp_score(round(weighted_score / total_importance))


def _overall_risk_score(groups: tuple[EconomicSignalGroup, ...]) -> int:
    if not groups:
        return 100
    average_health = round(sum(group.score for group in groups) / len(groups))
    return clamp_score(100 - average_health)


def _overall_health(risk_score: int) -> str:
    if risk_score <= 25:
        return "Healthy"
    if risk_score <= 40:
        return "Mixed but resilient"
    if risk_score <= 60:
        return "Fragile"
    return "Stressed"


def _group_status(score: int) -> str:
    if score >= 75:
        return "Supportive"
    if score >= 60:
        return "Neutral"
    if score >= 45:
        return "Watchful"
    return "Stressed"


def _strongest_positive_signals(
    groups: tuple[EconomicSignalGroup, ...],
) -> tuple[EconomicSignal, ...]:
    return tuple(
        sorted(
            _all_signals(groups),
            key=lambda signal: (-signal.score, -signal.importance, signal.name),
        )[:4]
    )


def _strongest_negative_signals(
    groups: tuple[EconomicSignalGroup, ...],
) -> tuple[EconomicSignal, ...]:
    return tuple(
        sorted(
            _all_signals(groups),
            key=lambda signal: (signal.score, -signal.importance, signal.name),
        )[:4]
    )


def _watching_most_closely(
    groups: tuple[EconomicSignalGroup, ...],
    negative_signals: tuple[EconomicSignal, ...],
) -> tuple[str, ...]:
    weakest_group = min(groups, key=lambda group: group.score)
    return (
        f"{weakest_group.name}: {weakest_group.interpretation}",
        *(
            f"{signal.name}: {signal.why_it_matters}"
            for signal in negative_signals[:3]
        ),
    )


def _what_would_improve_outlook(
    groups: tuple[EconomicSignalGroup, ...],
) -> tuple[str, ...]:
    return (
        "Credit spreads narrow while default rates remain contained.",
        "Bank lending standards ease without reigniting inflation.",
        "Rate volatility declines and real rates become less restrictive.",
        "Market breadth improves across sectors and new highs broaden.",
    )


def _what_would_worsen_outlook(
    groups: tuple[EconomicSignalGroup, ...],
) -> tuple[str, ...]:
    return (
        "High yield spreads widen alongside rising default rates.",
        "Repo or dollar liquidity stress appears in funding markets.",
        "Inflation reaccelerates while growth and employment weaken.",
        "Market breadth deteriorates while volatility rises across assets.",
    )


def _conclusion(
    health: str,
    risk_score: int,
    groups: tuple[EconomicSignalGroup, ...],
    positive: tuple[EconomicSignal, ...],
    negative: tuple[EconomicSignal, ...],
) -> str:
    weakest_group = min(groups, key=lambda group: group.score)
    strongest_group = max(groups, key=lambda group: group.score)
    return (
        f"Atlas classifies economic conditions as {health} with an overall risk "
        f"score of {risk_score}/100. The strongest group is {strongest_group.name}, "
        f"while the weakest group is {weakest_group.name}. Positive support comes "
        f"from {positive[0].name}; pressure comes from {negative[0].name}. "
        "This is context for research, not a forecast or allocation instruction."
    )


def _all_signals(groups: tuple[EconomicSignalGroup, ...]) -> tuple[EconomicSignal, ...]:
    return tuple(signal for group in groups for signal in group.signals)


def _render_group(group: EconomicSignalGroup) -> list[str]:
    lines = [
        "",
        group.name,
        f"Status: {group.status}",
        f"Score: {group.score}/100",
        "Interpretation",
        group.interpretation,
        "Signals",
    ]
    for signal in group.signals:
        lines.append(
            (
                f"- {signal.name}: {signal.current_state}; direction {signal.direction}; "
                f"importance {signal.importance}/100; confidence {signal.confidence}/100. "
                f"{signal.why_it_matters}"
            )
        )
    lines.append("")
    return lines


def _render_signal_list(signals: tuple[EconomicSignal, ...]) -> list[str]:
    if not signals:
        return ["- None"]
    return [
        (
            f"- {signal.name}: score {signal.score}/100, direction "
            f"{signal.direction}, confidence {signal.confidence}/100."
        )
        for signal in signals
    ]


def _render_list(items: tuple[str, ...]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]

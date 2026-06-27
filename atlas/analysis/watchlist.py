import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from atlas.analysis.engine import AtlasInvestmentEngine, InvestmentReport
from atlas.providers.base import CompanyDataProvider


@dataclass(frozen=True)
class WatchlistItem:
    ticker: str


@dataclass(frozen=True)
class Watchlist:
    name: str
    items: tuple[WatchlistItem, ...]

    @classmethod
    def from_json_file(cls, path: Path) -> "Watchlist":
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        return cls.from_mapping(payload)

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "Watchlist":
        name = str(payload.get("name", "Watchlist")).strip() or "Watchlist"
        tickers = payload.get("tickers")
        if not isinstance(tickers, list) or not tickers:
            raise ValueError("Watchlist JSON must contain a non-empty tickers list.")
        return cls(
            name=name,
            items=tuple(WatchlistItem(ticker=str(ticker).upper()) for ticker in tickers),
        )


@dataclass(frozen=True)
class WatchlistSignal:
    label: str
    ticker: str
    reasoning: str


class WatchlistRecommendation(str, Enum):
    PRIORITIZE = "Prioritize"
    WATCH = "Watch"
    AVOID = "Avoid"


@dataclass(frozen=True)
class WatchlistAnalysis:
    name: str
    ranked_opportunities: tuple[WatchlistItem, ...]
    reports: dict[str, InvestmentReport]
    strongest_opportunity: WatchlistSignal
    highest_quality_company: WatchlistSignal
    cheapest_valuation: WatchlistSignal
    highest_risk_company: WatchlistSignal
    companies_to_watch: tuple[WatchlistSignal, ...]
    companies_to_avoid: tuple[WatchlistSignal, ...]
    final_atlas_view: str

    @property
    def best_overall(self) -> WatchlistSignal:
        return self.strongest_opportunity


class WatchlistEngine:
    def __init__(self, investment_engine: AtlasInvestmentEngine | None = None) -> None:
        self.investment_engine = investment_engine or AtlasInvestmentEngine()

    def analyze(
        self,
        watchlist: Watchlist,
        provider: CompanyDataProvider,
    ) -> WatchlistAnalysis:
        reports = {
            item.ticker: self.investment_engine.analyze_ticker(item.ticker, provider)
            for item in watchlist.items
        }
        ranked_items = tuple(
            sorted(
                watchlist.items,
                key=lambda item: _ranking_key(item.ticker, reports[item.ticker]),
            )
        )
        strongest = ranked_items[0]
        highest_quality = _best_by_score(ranked_items, reports, lambda report: report.quality.score)
        cheapest = _best_by_score(ranked_items, reports, lambda report: report.valuation.score)
        highest_risk = _highest_risk_item(ranked_items, reports)
        companies_to_avoid = tuple(
            _watchlist_signal("Avoid", item.ticker, reports[item.ticker])
            for item in ranked_items
            if _recommendation_for_report(reports[item.ticker]) == WatchlistRecommendation.AVOID
        )
        companies_to_watch = tuple(
            _watchlist_signal("Watch", item.ticker, reports[item.ticker])
            for item in ranked_items
            if _recommendation_for_report(reports[item.ticker]) == WatchlistRecommendation.WATCH
        )
        return WatchlistAnalysis(
            name=watchlist.name,
            ranked_opportunities=ranked_items,
            reports=reports,
            strongest_opportunity=_watchlist_signal(
                "Strongest Opportunity",
                strongest.ticker,
                reports[strongest.ticker],
            ),
            highest_quality_company=_watchlist_signal(
                "Highest Quality",
                highest_quality.ticker,
                reports[highest_quality.ticker],
            ),
            cheapest_valuation=_watchlist_signal(
                "Best Valuation",
                cheapest.ticker,
                reports[cheapest.ticker],
            ),
            highest_risk_company=_highest_risk_signal(
                highest_risk.ticker,
                reports[highest_risk.ticker],
            ),
            companies_to_watch=companies_to_watch,
            companies_to_avoid=companies_to_avoid,
            final_atlas_view=_final_atlas_view(
                watchlist.name,
                strongest.ticker,
                reports[strongest.ticker],
            ),
        )


def render_watchlist_analysis(analysis: WatchlistAnalysis) -> str:
    lines = [
        "Watchlist Analysis",
        "",
        f"Watchlist name: {analysis.name}",
        "",
        "Ranked Opportunities",
    ]
    for index, item in enumerate(analysis.ranked_opportunities, start=1):
        report = analysis.reports[item.ticker]
        lines.append(
            (
                f"{index}. {item.ticker}: Atlas Score {report.atlas_score}/100, "
                f"{report.overall_recommendation}, confidence {report.confidence}/100, "
                f"valuation {report.valuation.score}/100, quality {report.quality.score}/100, "
                f"growth {report.growth.score}/100, risk {report.risk.score}/100"
            )
        )
    lines.extend(
        [
            "",
            "Best Overall",
            _render_signal(analysis.strongest_opportunity),
            "",
            "Best Valuation",
            _render_signal(analysis.cheapest_valuation),
            "",
            "Highest Quality",
            _render_signal(analysis.highest_quality_company),
            "",
            "Highest Risk",
            _render_signal(analysis.highest_risk_company),
            "",
            "Companies to Watch",
            *_render_signal_list(analysis.companies_to_watch),
            "",
            "Companies to Avoid",
            *_render_signal_list(analysis.companies_to_avoid),
            "",
            "Final Atlas View",
            analysis.final_atlas_view,
        ]
    )
    return "\n".join(lines)


def _ranking_key(ticker: str, report: InvestmentReport) -> tuple[int, int, int, int, int, int, str]:
    return (
        -report.atlas_score,
        -_recommendation_rank(report.overall_recommendation),
        -report.confidence,
        -report.valuation.score,
        -report.quality.score,
        -report.growth.score,
        ticker,
    )


def _best_by_score(
    ranked_items: tuple[WatchlistItem, ...],
    reports: dict[str, InvestmentReport],
    score_getter,
) -> WatchlistItem:
    return sorted(
        ranked_items,
        key=lambda item: (-score_getter(reports[item.ticker]), item.ticker),
    )[0]


def _highest_risk_item(
    ranked_items: tuple[WatchlistItem, ...],
    reports: dict[str, InvestmentReport],
) -> WatchlistItem:
    return sorted(
        ranked_items,
        key=lambda item: (reports[item.ticker].risk.score, item.ticker),
    )[0]


def _recommendation_for_report(report: InvestmentReport) -> WatchlistRecommendation:
    if report.atlas_score >= 80 and report.confidence >= 70:
        return WatchlistRecommendation.PRIORITIZE
    if report.atlas_score >= 60:
        return WatchlistRecommendation.WATCH
    return WatchlistRecommendation.AVOID


def _recommendation_rank(recommendation: str) -> int:
    ranks = {
        "Strong Buy": 5,
        "Buy": 4,
        "Hold": 3,
        "Sell": 2,
        "Strong Sell": 1,
    }
    return ranks.get(recommendation, 0)


def _watchlist_signal(label: str, ticker: str, report: InvestmentReport) -> WatchlistSignal:
    return WatchlistSignal(
        label=label,
        ticker=ticker,
        reasoning=(
            f"{ticker} has an Atlas Score of {report.atlas_score}/100, "
            f"{report.overall_recommendation} recommendation, confidence "
            f"{report.confidence}/100, valuation {report.valuation.score}/100, "
            f"quality {report.quality.score}/100, growth {report.growth.score}/100, "
            f"and risk profile {report.risk.score}/100."
        ),
    )


def _highest_risk_signal(ticker: str, report: InvestmentReport) -> WatchlistSignal:
    return WatchlistSignal(
        label="Highest Risk",
        ticker=ticker,
        reasoning=(
            f"{ticker} has the weakest risk profile in this watchlist at "
            f"{report.risk.score}/100."
        ),
    )


def _final_atlas_view(name: str, ticker: str, report: InvestmentReport) -> str:
    return (
        f"For {name}, Atlas would focus first on {ticker}. It has the strongest current "
        f"combination of Atlas Score ({report.atlas_score}/100), recommendation "
        f"({report.overall_recommendation}), confidence ({report.confidence}/100), "
        f"valuation ({report.valuation.score}/100), quality ({report.quality.score}/100), "
        f"growth ({report.growth.score}/100), and risk profile ({report.risk.score}/100)."
    )


def _render_signal(signal: WatchlistSignal) -> str:
    return f"{signal.ticker}: {signal.reasoning}"


def _render_signal_list(signals: tuple[WatchlistSignal, ...]) -> list[str]:
    if not signals:
        return ["- None"]
    return [f"- {_render_signal(signal)}" for signal in signals]

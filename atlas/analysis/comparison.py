from dataclasses import dataclass
from typing import Callable

from atlas.analysis.company_analysis import CompanyAnalysis
from atlas.analysis.engine import AtlasInvestmentEngine, InvestmentReport


@dataclass(frozen=True)
class ComparisonCandidate:
    ticker: str
    report: InvestmentReport


@dataclass(frozen=True)
class ComparisonRanking:
    category: str
    winner: ComparisonCandidate
    ordered_candidates: tuple[ComparisonCandidate, ...]
    reasoning: str


@dataclass(frozen=True)
class ComparisonResult:
    candidates: tuple[ComparisonCandidate, ...]
    best_overall: ComparisonRanking
    best_quality: ComparisonRanking
    best_valuation: ComparisonRanking
    best_growth: ComparisonRanking
    lowest_risk: ComparisonRanking
    final_conclusion: str


class ComparisonEngine:
    def __init__(self, investment_engine: AtlasInvestmentEngine | None = None) -> None:
        self.investment_engine = investment_engine or AtlasInvestmentEngine()

    def compare(self, analyses: dict[str, CompanyAnalysis]) -> ComparisonResult:
        if len(analyses) < 2:
            raise ValueError("Comparison requires at least two companies.")
        candidates = tuple(
            ComparisonCandidate(
                ticker=ticker.upper(),
                report=self.investment_engine.analyze(analysis),
            )
            for ticker, analysis in analyses.items()
        )
        best_overall = _ranking(
            category="Best Overall",
            candidates=candidates,
            score_getter=lambda candidate: candidate.report.atlas_score,
            metric_label="Atlas Score",
        )
        best_quality = _ranking(
            category="Best Quality",
            candidates=candidates,
            score_getter=lambda candidate: candidate.report.quality.score,
            metric_label="quality score",
        )
        best_valuation = _ranking(
            category="Best Valuation",
            candidates=candidates,
            score_getter=lambda candidate: candidate.report.valuation.score,
            metric_label="valuation score",
        )
        best_growth = _ranking(
            category="Best Growth",
            candidates=candidates,
            score_getter=lambda candidate: candidate.report.growth.score,
            metric_label="growth score",
        )
        lowest_risk = _ranking(
            category="Lowest Risk",
            candidates=candidates,
            score_getter=lambda candidate: candidate.report.risk.score,
            metric_label="risk profile score",
        )
        return ComparisonResult(
            candidates=candidates,
            best_overall=best_overall,
            best_quality=best_quality,
            best_valuation=best_valuation,
            best_growth=best_growth,
            lowest_risk=lowest_risk,
            final_conclusion=_final_conclusion(best_overall.winner),
        )


def render_comparison_result(result: ComparisonResult) -> str:
    lines = [
        "Company Comparison",
        "",
        "Candidates",
    ]
    for candidate in result.candidates:
        report = candidate.report
        lines.append(
            (
                f"- {candidate.ticker}: Atlas Score {report.atlas_score}/100, "
                f"{report.overall_recommendation}, confidence {report.confidence}/100, "
                f"valuation {report.valuation.score}/100, quality {report.quality.score}/100, "
                f"growth {report.growth.score}/100, financial strength "
                f"{report.financial_strength.score}/100, risk {report.risk.score}/100"
            )
        )
    lines.extend(
        [
            "",
            "Rankings",
            _render_ranking(result.best_overall),
            _render_ranking(result.best_quality),
            _render_ranking(result.best_valuation),
            _render_ranking(result.best_growth),
            _render_ranking(result.lowest_risk),
            "",
            "Final Conclusion",
            result.final_conclusion,
        ]
    )
    return "\n".join(lines)


def _ranking(
    category: str,
    candidates: tuple[ComparisonCandidate, ...],
    score_getter: Callable[[ComparisonCandidate], int],
    metric_label: str,
) -> ComparisonRanking:
    ordered_candidates = tuple(
        sorted(
            candidates,
            key=lambda candidate: (
                -score_getter(candidate),
                -candidate.report.confidence,
                candidate.ticker,
            ),
        )
    )
    winner = ordered_candidates[0]
    winning_score = score_getter(winner)
    return ComparisonRanking(
        category=category,
        winner=winner,
        ordered_candidates=ordered_candidates,
        reasoning=(
            f"{winner.ticker} ranks first for {category.lower()} with "
            f"{_article_for(metric_label)} {metric_label} of {winning_score}/100."
        ),
    )


def _render_ranking(ranking: ComparisonRanking) -> str:
    ordered = ", ".join(
        f"{candidate.ticker} ({_ranking_score(ranking.category, candidate)}/100)"
        for candidate in ranking.ordered_candidates
    )
    return f"- {ranking.category}: {ranking.winner.ticker}. {ranking.reasoning} Ranking: {ordered}."


def _ranking_score(category: str, candidate: ComparisonCandidate) -> int:
    if category == "Best Overall":
        return candidate.report.atlas_score
    if category == "Best Quality":
        return candidate.report.quality.score
    if category == "Best Valuation":
        return candidate.report.valuation.score
    if category == "Best Growth":
        return candidate.report.growth.score
    if category == "Lowest Risk":
        return candidate.report.risk.score
    raise ValueError(f"Unknown ranking category: {category}")


def _final_conclusion(winner: ComparisonCandidate) -> str:
    report = winner.report
    return (
        f"If Atlas could choose only one, it would choose {winner.ticker} because it has "
        f"the strongest overall combination of Atlas Score ({report.atlas_score}/100), "
        f"recommendation ({report.overall_recommendation}), confidence "
        f"({report.confidence}/100), quality ({report.quality.score}/100), growth "
        f"({report.growth.score}/100), valuation ({report.valuation.score}/100), "
        f"financial strength ({report.financial_strength.score}/100), and risk profile "
        f"({report.risk.score}/100)."
    )


def _article_for(label: str) -> str:
    return "an" if label[0].lower() in {"a", "e", "i", "o", "u"} else "a"

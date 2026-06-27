import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from atlas.analysis.engine import AtlasInvestmentEngine, InvestmentReport, iter_score_categories
from atlas.analysis.explanation import explain_investment_report
from atlas.providers.base import CompanyDataProvider


@dataclass(frozen=True)
class MemoryEntry:
    ticker: str
    timestamp: str
    atlas_score: int
    recommendation: str
    confidence: int
    category_scores: dict[str, int]
    explanation_summary: str

    @classmethod
    def from_report(
        cls,
        ticker: str,
        report: InvestmentReport,
        timestamp: datetime | None = None,
    ) -> "MemoryEntry":
        explanation = explain_investment_report(report)
        created_at = timestamp or datetime.now(UTC)
        return cls(
            ticker=ticker.upper(),
            timestamp=created_at.isoformat(),
            atlas_score=report.atlas_score,
            recommendation=report.overall_recommendation,
            confidence=report.confidence,
            category_scores={
                _category_key(label): category.score
                for label, category in iter_score_categories(report)
            },
            explanation_summary=explanation.bull_case,
        )

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "MemoryEntry":
        return cls(
            ticker=str(payload["ticker"]).upper(),
            timestamp=str(payload["timestamp"]),
            atlas_score=int(payload["atlas_score"]),
            recommendation=str(payload["recommendation"]),
            confidence=int(payload["confidence"]),
            category_scores={
                str(category): int(score)
                for category, score in dict(payload["category_scores"]).items()
            },
            explanation_summary=str(payload["explanation_summary"]),
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker,
            "timestamp": self.timestamp,
            "atlas_score": self.atlas_score,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "category_scores": self.category_scores,
            "explanation_summary": self.explanation_summary,
        }


@dataclass(frozen=True)
class MemoryComparison:
    ticker: str
    previous: MemoryEntry
    current: MemoryEntry
    score_change: int
    recommendation_change: str
    confidence_change: int
    strongest_improving_category: str
    weakest_category: str
    explanation: str


class MemoryStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> tuple[MemoryEntry, ...]:
        if not self.path.exists():
            return ()
        with self.path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        raw_entries = payload.get("entries", [])
        if not isinstance(raw_entries, list):
            raise ValueError("Memory JSON must contain an entries list.")
        entries = tuple(MemoryEntry.from_mapping(entry) for entry in raw_entries)
        return tuple(sorted(entries, key=lambda entry: (entry.ticker, entry.timestamp)))

    def save(self, entry: MemoryEntry) -> tuple[MemoryEntry, ...]:
        entries = (*self.load(), entry)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(
                {"entries": [saved_entry.to_mapping() for saved_entry in entries]},
                file,
                indent=2,
                sort_keys=True,
            )
            file.write("\n")
        return entries

    def load_ticker(self, ticker: str) -> tuple[MemoryEntry, ...]:
        normalized_ticker = ticker.upper()
        return tuple(entry for entry in self.load() if entry.ticker == normalized_ticker)


class MemoryEngine:
    def save(
        self,
        store: MemoryStore,
        ticker: str,
        report: InvestmentReport,
        timestamp: datetime | None = None,
    ) -> MemoryEntry:
        entry = MemoryEntry.from_report(ticker=ticker, report=report, timestamp=timestamp)
        store.save(entry)
        return entry

    def save_ticker(
        self,
        store: MemoryStore,
        ticker: str,
        provider: CompanyDataProvider,
        investment_engine: AtlasInvestmentEngine | None = None,
        timestamp: datetime | None = None,
    ) -> MemoryEntry:
        engine = investment_engine or AtlasInvestmentEngine()
        return self.save(
            store=store,
            ticker=ticker,
            report=engine.analyze_ticker(ticker, provider),
            timestamp=timestamp,
        )

    def load(self, store: MemoryStore) -> tuple[MemoryEntry, ...]:
        return store.load()

    def compare(self, store: MemoryStore, ticker: str) -> MemoryComparison:
        entries = store.load_ticker(ticker)
        if len(entries) < 2:
            raise ValueError(
                f"At least two memory entries are required to compare {ticker.upper()}."
            )
        previous, current = entries[-2], entries[-1]
        category_changes = {
            category: current.category_scores.get(category, 0)
            - previous.category_scores.get(category, 0)
            for category in sorted(set(previous.category_scores) | set(current.category_scores))
        }
        strongest_category = max(
            category_changes,
            key=lambda category: (category_changes[category], category),
        )
        weakest_category = min(
            current.category_scores,
            key=lambda category: (current.category_scores[category], category),
        )
        score_change = current.atlas_score - previous.atlas_score
        confidence_change = current.confidence - previous.confidence
        recommendation_change = _change_label(previous.recommendation, current.recommendation)
        return MemoryComparison(
            ticker=current.ticker,
            previous=previous,
            current=current,
            score_change=score_change,
            recommendation_change=recommendation_change,
            confidence_change=confidence_change,
            strongest_improving_category=strongest_category,
            weakest_category=weakest_category,
            explanation=_comparison_explanation(
                ticker=current.ticker,
                score_change=score_change,
                recommendation_change=recommendation_change,
                confidence_change=confidence_change,
                strongest_category=strongest_category,
                weakest_category=weakest_category,
            ),
        )


def render_memory_entries(entries: tuple[MemoryEntry, ...]) -> str:
    lines = ["Memory Entries"]
    if not entries:
        return "\n".join([*lines, "", "- None"])
    for entry in entries:
        lines.append(
            (
                f"- {entry.ticker} at {entry.timestamp}: Atlas Score "
                f"{entry.atlas_score}/100, {entry.recommendation}, confidence "
                f"{entry.confidence}/100"
            )
        )
    return "\n".join(lines)


def render_memory_comparison(comparison: MemoryComparison) -> str:
    return "\n".join(
        [
            "Memory Comparison",
            "",
            f"Ticker: {comparison.ticker}",
            f"Previous timestamp: {comparison.previous.timestamp}",
            f"Current timestamp: {comparison.current.timestamp}",
            f"Score Change: {_format_change(comparison.score_change)}",
            f"Recommendation Change: {comparison.recommendation_change}",
            f"Confidence Change: {_format_change(comparison.confidence_change)}",
            f"Strongest Improving Category: {comparison.strongest_improving_category}",
            f"Weakest Category: {comparison.weakest_category}",
            "",
            "What Changed",
            comparison.explanation,
        ]
    )


def _category_key(label: str) -> str:
    return label.lower().replace(" ", "_")


def _change_label(previous: str, current: str) -> str:
    if previous == current:
        return f"unchanged ({current})"
    return f"{previous} -> {current}"


def _comparison_explanation(
    ticker: str,
    score_change: int,
    recommendation_change: str,
    confidence_change: int,
    strongest_category: str,
    weakest_category: str,
) -> str:
    return (
        f"{ticker} changed by {_format_change(score_change)} points in Atlas Score. "
        f"The recommendation is {recommendation_change}, confidence changed by "
        f"{_format_change(confidence_change)} points, the strongest improving category "
        f"was {strongest_category}, and the current weakest category is {weakest_category}."
    )


def _format_change(change: int) -> str:
    if change > 0:
        return f"+{change}"
    return str(change)

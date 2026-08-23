"""HTTP response schemas for the Stance API. Wire format is camelCase
via the shared Core `CamelModel` (ADR-004), matching every other Alpha
schema module. Every enum is sent as its `.value` string -- the
frontend owns localized labels via its own key map, the same
convention every other categorical field in this codebase already
follows.
"""
from __future__ import annotations

from atlas.alpha.stance.models import Stance, StanceComparison, StanceComparisonReason, StanceReason
from atlas.core.infrastructure.api.serialization import CamelModel


class StanceReasonView(CamelModel):
    code: str

    @classmethod
    def from_domain(cls, reason: StanceReason) -> "StanceReasonView":
        return cls(code=reason.code.value)


class StanceView(CamelModel):
    level: str
    reasoning: list[StanceReasonView]
    supporting_signals: list[StanceReasonView]
    limiting_signals: list[StanceReasonView]
    confidence: str
    missing_information: list[str]

    @classmethod
    def from_domain(cls, stance: Stance) -> "StanceView":
        return cls(
            level=stance.level.value,
            reasoning=[StanceReasonView.from_domain(r) for r in stance.reasoning],
            supporting_signals=[StanceReasonView.from_domain(r) for r in stance.supporting_signals],
            limiting_signals=[StanceReasonView.from_domain(r) for r in stance.limiting_signals],
            confidence=stance.confidence.value,
            missing_information=list(stance.missing_information),
        )


class StanceComparisonReasonView(CamelModel):
    code: str
    ticker: str | None

    @classmethod
    def from_domain(cls, reason: StanceComparisonReason) -> "StanceComparisonReasonView":
        return cls(code=reason.code.value, ticker=reason.ticker)


class StanceComparisonView(CamelModel):
    ticker_a: str
    stance_a: StanceView
    ticker_b: str
    stance_b: StanceView
    preferred_ticker: str | None
    reasoning: list[StanceComparisonReasonView]

    @classmethod
    def from_domain(cls, comparison: StanceComparison) -> "StanceComparisonView":
        return cls(
            ticker_a=comparison.ticker_a,
            stance_a=StanceView.from_domain(comparison.stance_a),
            ticker_b=comparison.ticker_b,
            stance_b=StanceView.from_domain(comparison.stance_b),
            preferred_ticker=comparison.preferred_ticker,
            reasoning=[StanceComparisonReasonView.from_domain(r) for r in comparison.reasoning],
        )


class TickerStanceView(CamelModel):
    """Deliverables 6/7 -- a `Stance` paired with the ticker it was
    looked up under (`Stance` itself carries no ticker; see `models.py`
    docstring)."""

    ticker: str
    stance: StanceView

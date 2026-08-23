"""HTTP response schemas for the Daily Brief Agenda API. Wire format is
camelCase via the shared Core `CamelModel` (ADR-004). Every enum is
sent as its `.value` string -- the frontend owns localized labels via
its own key map, the same convention `atlas.alpha.portfolio_fit.api
.schemas` already established.
"""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.daily_brief_agenda.models import AgendaItem, DailyBriefAgenda, PortfolioSummary
from atlas.core.infrastructure.api.serialization import CamelModel


class AgendaItemView(CamelModel):
    id: str
    priority: str
    kind: str
    group: str
    source: str
    headline: str
    reason: list[str]
    nature: str
    """Fix Sprint 4 (Daily Brief Signal Quality) -- `"change_event"` or
    `"persistent_condition"`, the nature of the signal that decided
    this item's own `headline`/`kind`/`priority`."""
    reason_nature: list[str]
    """Parallel to `reason` -- same length, same order, one `nature`
    per contributing fact, so a reason folded in from a different
    source than the winner is never mislabeled as sharing its nature."""
    since: datetime | None
    """When the winning signal's own condition began, only populated
    for the two sources that carry a real timestamp for it (Case
    Condition, Assumption); `null` is an honest absence everywhere
    else, never a fabricated stand-in."""
    ticker: str | None
    case_id: str | None
    portfolio_context: str | None
    generated_at: datetime

    @classmethod
    def from_domain(cls, item: AgendaItem) -> "AgendaItemView":
        return cls(
            id=item.id,
            priority=item.priority.value,
            kind=item.kind.value,
            group=item.group.value,
            source=item.source.value,
            headline=item.headline,
            reason=list(item.reason),
            nature=item.nature.value,
            reason_nature=[n.value for n in item.reason_nature],
            since=item.since,
            ticker=item.ticker,
            case_id=item.case_id,
            portfolio_context=item.portfolio_context,
            generated_at=item.generated_at,
        )


class PortfolioSummaryView(CamelModel):
    holdings_count: int
    critical_count: int
    high_count: int
    watchlist_opportunity_count: int
    cash_weight_percent: float | None
    concentration_level: str | None

    @classmethod
    def from_domain(cls, summary: PortfolioSummary) -> "PortfolioSummaryView":
        return cls(
            holdings_count=summary.holdings_count,
            critical_count=summary.critical_count,
            high_count=summary.high_count,
            watchlist_opportunity_count=summary.watchlist_opportunity_count,
            cash_weight_percent=summary.cash_weight_percent,
            concentration_level=summary.concentration_level,
        )


class DailyBriefAgendaView(CamelModel):
    generated_at: datetime
    summary: PortfolioSummaryView
    items: list[AgendaItemView]

    @classmethod
    def from_domain(cls, agenda: DailyBriefAgenda) -> "DailyBriefAgendaView":
        return cls(
            generated_at=agenda.generated_at,
            summary=PortfolioSummaryView.from_domain(agenda.summary),
            items=[AgendaItemView.from_domain(item) for item in agenda.items],
        )

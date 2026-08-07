"""REST controller for Discovery Intelligence v1.

POST /discovery/chat - one conversational exchange, portfolio context
                        resolved server-side; never requires the
                        frontend to call a provider directly.

This is the one deliberate composition point between `atlas/ai/`'s
provider-agnostic core logic and `atlas/alpha/`'s real portfolio state
— mirroring exactly the same pattern
`atlas/core/infrastructure/api/app.py`'s own module comment already
documents for the Alpha portfolio router. `atlas/ai/discovery_chat.py`
itself never imports `atlas.alpha` (enforced by
`tests/test_architecture_boundaries.py`); only this router does, here,
to convert real portfolio state into the small, provider-agnostic
`PortfolioContextInput` shape that module defines, and — Discovery Tool
Calling v1 — to *resolve* a `tool_call_requested` outcome into a real
result.

Tool resolution is deliberately server-controlled and narrow: the
model's `ToolCallRequest.ticker` is matched by exact, case-insensitive
string equality against the investor's own real holdings — the same
technique `DiscoveryPage.tsx`'s pre-existing "Review a company" flow
already uses — never fuzzy matching, never entity recognition. The
model never calls the Case API itself; this router does, using exactly
the same two real calls (`CaseService.create`,
`AlphaPortfolioService.link_case_to_holding`) Portfolio's own "Open
Investment Case" button already uses. No holding, weight, or any other
portfolio state is ever mutated by this tool — it can only create a
bare Case and link it to an *existing* holding, never create or alter
a holding itself.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from atlas.ai.api.dependencies import get_discovery_provider
from atlas.ai.api.schemas import DiscoveryChatRequest, DiscoveryChatResponse, ToolResultBody
from atlas.ai.discovery_chat import (
    ChatMessage,
    ConversationProvider,
    HoldingContextInput,
    PortfolioContextInput,
    run_discovery_chat,
)
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_service
from atlas.alpha.portfolio.api.schemas import HoldingView, PortfolioView
from atlas.alpha.portfolio.projection import derive_portfolio_view
from atlas.alpha.portfolio.service import AlphaPortfolioService
from atlas.core.application.case.create_case import CaseService
from atlas.core.infrastructure.api.case.dependencies import get_case_service

router = APIRouter(prefix="/discovery", tags=["discovery"])


def _portfolio_context(view: PortfolioView) -> PortfolioContextInput | None:
    if not view.exists or len(view.holdings) == 0:
        return None
    return PortfolioContextInput(
        holdings=tuple(
            HoldingContextInput(
                ticker=h.ticker,
                weight_percent=h.weight_percent,
                value_absolute=h.value_absolute,
                reconciliation_status=h.reconciliation_status,
            )
            for h in view.holdings
        ),
        cash_weight_percent=view.cash_weight_percent,
        has_absolute_values=view.has_absolute_values,
        concentration_level=view.concentration_level,
    )


def _find_holding(view: PortfolioView, ticker: str) -> HoldingView | None:
    normalized = ticker.strip().lower()
    for holding in view.holdings:
        if holding.ticker.strip().lower() == normalized:
            return holding
    return None


def _resolve_create_or_open_investment_case(
    ticker: str,
    portfolio_view: PortfolioView,
    case_service: CaseService,
    alpha_service: AlphaPortfolioService,
) -> ToolResultBody:
    holding = _find_holding(portfolio_view, ticker)
    if holding is None:
        return ToolResultBody(
            tool="create_or_open_investment_case", outcome="unresolved", ticker=ticker, case_id=None
        )

    if holding.case_id is not None:
        return ToolResultBody(
            tool="create_or_open_investment_case",
            outcome="opened",
            ticker=holding.ticker,
            case_id=holding.case_id,
        )

    try:
        case = case_service.create()
        case_id = alpha_service.link_case_to_holding(holding.ticker, str(case.id.value))
    except Exception:
        return ToolResultBody(
            tool="create_or_open_investment_case", outcome="failed", ticker=ticker, case_id=None
        )
    return ToolResultBody(
        tool="create_or_open_investment_case", outcome="created", ticker=holding.ticker, case_id=case_id
    )


@router.post("/chat", response_model=DiscoveryChatResponse)
def post_discovery_chat(
    body: DiscoveryChatRequest,
    service: AlphaPortfolioService = Depends(get_alpha_portfolio_service),
    case_service: CaseService = Depends(get_case_service),
    provider: ConversationProvider | None = Depends(get_discovery_provider),
) -> DiscoveryChatResponse:
    state = service.get_state()
    portfolio_view = (
        PortfolioView.from_domain(state, derive_portfolio_view(state))
        if state is not None
        else PortfolioView.empty()
    )

    outcome = run_discovery_chat(
        messages=tuple(ChatMessage(role=m.role, content=m.content) for m in body.messages),
        language=body.language,
        portfolio=_portfolio_context(portfolio_view),
        provider=provider,
    )

    if outcome.mode == "tool_call_requested" and outcome.tool_call_request is not None:
        tool_result = _resolve_create_or_open_investment_case(
            outcome.tool_call_request.ticker, portfolio_view, case_service, service
        )
        return DiscoveryChatResponse(message=None, mode="tool_call", tool_result=tool_result)

    return DiscoveryChatResponse(message=outcome.message, mode=outcome.mode)

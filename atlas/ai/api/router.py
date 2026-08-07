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
`PortfolioContextInput` shape that module defines.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from atlas.ai.api.dependencies import get_discovery_provider
from atlas.ai.api.schemas import DiscoveryChatRequest, DiscoveryChatResponse
from atlas.ai.discovery_chat import (
    ChatMessage,
    ConversationProvider,
    HoldingContextInput,
    PortfolioContextInput,
    run_discovery_chat,
)
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_service
from atlas.alpha.portfolio.api.schemas import PortfolioView
from atlas.alpha.portfolio.projection import derive_portfolio_view
from atlas.alpha.portfolio.service import AlphaPortfolioService

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


@router.post("/chat", response_model=DiscoveryChatResponse)
def post_discovery_chat(
    body: DiscoveryChatRequest,
    service: AlphaPortfolioService = Depends(get_alpha_portfolio_service),
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
    return DiscoveryChatResponse(message=outcome.message, mode=outcome.mode)

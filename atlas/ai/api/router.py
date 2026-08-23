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
    CaseContextInput,
    ChatMessage,
    ConsiderContextInput,
    ConversationProvider,
    HoldingContextInput,
    KeyFindingContextInput,
    PortfolioContextInput,
    RiskSignalContextInput,
    run_discovery_chat,
)
from atlas.alpha.discovery_context.dependencies import get_discovery_context_service
from atlas.alpha.discovery_context.models import DiscoveryContext, IdentityResolutionStatus
from atlas.alpha.discovery_context.service import DiscoveryContextService
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_service
from atlas.alpha.portfolio.api.schemas import HoldingView, PortfolioView
from atlas.alpha.portfolio.projection import derive_portfolio_view
from atlas.alpha.portfolio.service import AlphaPortfolioService
from atlas.core.application.case.create_case import CaseService
from atlas.core.infrastructure.api.case.dependencies import get_case_service

router = APIRouter(prefix="/discovery", tags=["discovery"])


def _case_context(context: DiscoveryContext) -> CaseContextInput | None:
    """ATLAS-030: Discovery consumes the exact same canonical
    `DiscoveryCaseContext` -- built from `InvestmentCaseCompositionService
    .build()`, the same composition Portfolio Cockpit and the Investment
    Case page's own API route consume -- never a second reconstruction.
    `None` unless identity resolution (`atlas.alpha.discovery_context`)
    actually succeeded."""
    case = context.case
    if case is None:
        return None
    return CaseContextInput(
        ticker=case.ticker,
        held=case.held,
        current_thesis_reason=case.current_thesis_reason,
        confidence=case.confidence.value,
        conviction_level=case.conviction_level.value,
        is_stale=case.is_stale,
        missing_evidence_kinds=tuple(kind.value for kind in case.missing_evidence_kinds),
        open_questions=tuple(kind.value for kind in case.open_questions),
        key_risks=tuple(kind.value for kind in case.key_risks),
        consider_kinds=tuple(kind.value for kind in case.consider_kinds),
        portfolio_context_facts=tuple(fact.value for fact in case.portfolio_context_facts),
        monitoring_pending=case.monitoring_pending,
    )


def _portfolio_context(view: PortfolioView, context: DiscoveryContext) -> PortfolioContextInput | None:
    """ATLAS-016/017/018: raw holdings/cash come from the Alpha
    portfolio's own state (`view`) -- primary source data, not
    "reasoning," and `PortfolioIntelligenceReport` deliberately does not
    re-expose it (see that type's own docstring). Every *reasoning* fact
    -- Key Findings, Consider, Risk Signals, and Case Intelligence --
    comes from the single canonical `DiscoveryContext`
    (`atlas.alpha.discovery_context.DiscoveryContextService`), never
    reconstructed here. An `UNRESOLVED` identity is real content even
    when the portfolio itself is empty (Phase 3: never silently drop a
    failed identity resolution)."""
    intelligence = context.portfolio
    case_context = _case_context(context)
    unresolved_case_id = (
        context.identity.case_id
        if context.identity.status is IdentityResolutionStatus.UNRESOLVED
        else None
    )
    if (not view.exists or len(view.holdings) == 0) and case_context is None and unresolved_case_id is None:
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
        key_findings=tuple(
            KeyFindingContextInput(kind=f.kind.value, count=f.count, tickers=f.tickers)
            for f in intelligence.key_findings
        ),
        consider_items=tuple(
            ConsiderContextInput(kind=c.kind.value, ticker=c.ticker, confidence=c.confidence.value)
            for c in intelligence.consider_items
        ),
        risk_signals=tuple(
            RiskSignalContextInput(kind=s.kind.value, ticker=s.ticker) for s in intelligence.risk_signals
        ),
        case_context=case_context,
        unresolved_case_id=unresolved_case_id,
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
    discovery_context_service: DiscoveryContextService = Depends(get_discovery_context_service),
    provider: ConversationProvider | None = Depends(get_discovery_provider),
) -> DiscoveryChatResponse:
    state = service.get_state()
    portfolio_view = (
        PortfolioView.from_domain(state, derive_portfolio_view(state))
        if state is not None
        else PortfolioView.empty()
    )
    # ATLAS-018: the one canonical context assembly call -- Portfolio
    # Intelligence, Case Intelligence, and deterministic identity
    # resolution all happen inside this single service, never separately
    # composed here.
    context = discovery_context_service.build(body.case_id)

    outcome = run_discovery_chat(
        messages=tuple(ChatMessage(role=m.role, content=m.content) for m in body.messages),
        language=body.language,
        portfolio=_portfolio_context(portfolio_view, context),
        provider=provider,
    )

    if outcome.mode == "tool_call_requested" and outcome.tool_call_request is not None:
        tool_result = _resolve_create_or_open_investment_case(
            outcome.tool_call_request.ticker, portfolio_view, case_service, service
        )
        return DiscoveryChatResponse(message=None, mode="tool_call", tool_result=tool_result)

    return DiscoveryChatResponse(message=outcome.message, mode=outcome.mode)

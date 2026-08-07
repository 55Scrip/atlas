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
from atlas.alpha.case_intelligence.api.dependencies import get_case_intelligence_service
from atlas.alpha.case_intelligence.models import CaseIntelligenceReport
from atlas.alpha.case_intelligence.service import CaseIntelligenceService
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_service
from atlas.alpha.portfolio.api.schemas import HoldingView, PortfolioView
from atlas.alpha.portfolio.projection import derive_portfolio_view
from atlas.alpha.portfolio.service import AlphaPortfolioService
from atlas.alpha.portfolio_intelligence.api.dependencies import get_portfolio_intelligence_service
from atlas.alpha.portfolio_intelligence.models import PortfolioIntelligenceReport
from atlas.alpha.portfolio_intelligence.service import PortfolioIntelligenceService
from atlas.core.application.case.create_case import CaseService
from atlas.core.infrastructure.api.case.dependencies import get_case_service

router = APIRouter(prefix="/discovery", tags=["discovery"])


def _case_context(report: CaseIntelligenceReport | None) -> CaseContextInput | None:
    """ATLAS-017: Discovery consumes the exact same `CaseIntelligenceReport`
    the Investment Case page's own API route returns -- never a second
    reconstruction. `None` when no `caseId` was resolved on the request,
    or the Case itself does not exist."""
    if report is None:
        return None
    return CaseContextInput(
        ticker=report.current_view.ticker,
        held=report.current_view.held,
        current_thesis_reason=report.current_thesis.latest_decision_reason,
        confidence=report.confidence.value,
        is_stale=report.review_status.is_stale,
        missing_evidence_kinds=tuple(gap.kind.value for gap in report.missing_evidence),
        key_risks=tuple(risk.kind.value for risk in report.key_risks),
        consider_kinds=tuple(item.kind.value for item in report.consider_items),
    )


def _portfolio_context(
    view: PortfolioView,
    intelligence: PortfolioIntelligenceReport | None,
    case_context: CaseContextInput | None,
) -> PortfolioContextInput | None:
    """ATLAS-016: Discovery consumes the same Key Findings/Consider/Risk
    Signals the Portfolio page shows (`intelligence`), rather than
    reconstructing any of its own -- both are built from the identical
    `PortfolioIntelligenceService.build_report()` call. ATLAS-017 adds
    `case_context` the same way. `case_context` alone (a brand-new,
    unheld Investment Case) is enough to return real content even when
    the portfolio itself is empty."""
    if (not view.exists or len(view.holdings) == 0) and case_context is None:
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
            for f in (intelligence.key_findings if intelligence else ())
        ),
        consider_items=tuple(
            ConsiderContextInput(kind=c.kind.value, ticker=c.ticker, confidence=c.confidence.value)
            for c in (intelligence.consider_items if intelligence else ())
        ),
        risk_signals=tuple(
            RiskSignalContextInput(kind=s.kind.value, ticker=s.ticker)
            for s in (intelligence.risk_signals if intelligence else ())
        ),
        case_context=case_context,
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
    intelligence_service: PortfolioIntelligenceService = Depends(get_portfolio_intelligence_service),
    case_intelligence_service: CaseIntelligenceService = Depends(get_case_intelligence_service),
    provider: ConversationProvider | None = Depends(get_discovery_provider),
) -> DiscoveryChatResponse:
    state = service.get_state()
    portfolio_view = (
        PortfolioView.from_domain(state, derive_portfolio_view(state))
        if state is not None
        else PortfolioView.empty()
    )
    intelligence_report = intelligence_service.build_report()
    case_report = case_intelligence_service.build_report(body.case_id) if body.case_id else None

    outcome = run_discovery_chat(
        messages=tuple(ChatMessage(role=m.role, content=m.content) for m in body.messages),
        language=body.language,
        portfolio=_portfolio_context(portfolio_view, intelligence_report, _case_context(case_report)),
        provider=provider,
    )

    if outcome.mode == "tool_call_requested" and outcome.tool_call_request is not None:
        tool_result = _resolve_create_or_open_investment_case(
            outcome.tool_call_request.ticker, portfolio_view, case_service, service
        )
        return DiscoveryChatResponse(message=None, mode="tool_call", tool_result=tool_result)

    return DiscoveryChatResponse(message=outcome.message, mode=outcome.mode)

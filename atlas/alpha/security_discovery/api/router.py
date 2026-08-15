"""REST controller for Security Discovery (Sprint 21).

GET /security-discovery?query=... -- the only endpoint. Deliberately
not called from any other backend module's own request path (Pattern
Recognition, History, Decision Review, Observed Decision Properties) --
only a frontend's own explicit "Find security" action should ever hit
this route (Sprint 21 Phase 3/9). An empty or whitespace-only query
returns `[]` rather than erroring, matching
`discover_security_candidates`'s own behavior; `max_length` on the
query parameter is a plain input-size guard, not an attempt at
sophisticated abuse protection (Sprint 21 Phase 30: "do not overbuild
abuse protection").
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from atlas.alpha.security_discovery.api.dependencies import get_security_discovery_indexes
from atlas.alpha.security_discovery.api.schemas import SecurityCandidateView
from atlas.alpha.security_discovery.service import TickerIndex, TitleIndex, discover_security_candidates

router = APIRouter(prefix="/security-discovery", tags=["security-discovery"])


@router.get("", response_model=list[SecurityCandidateView])
def discover_security(
    query: str = Query(default="", max_length=200),
    indexes: tuple[TitleIndex, TickerIndex] = Depends(get_security_discovery_indexes),
) -> list[SecurityCandidateView]:
    title_index, ticker_index = indexes
    candidates = discover_security_candidates(query, title_index=title_index, ticker_index=ticker_index)
    return [SecurityCandidateView.from_domain(c) for c in candidates]

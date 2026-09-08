"""REST controller for the Discovery candidate universe.

GET /discovery-candidates -- securities Atlas knows about that the
investor is not already following.

A read, and only a read. It creates no Case, adds no membership and
calls no provider; opening Discovery must not mutate anything. Cases
for analysed securities are adopted deliberately, by an operator,
through `atlas.dev.adopt_analysed_securities`.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from atlas.alpha.discovery_candidates.api.dependencies import get_discovery_candidate_service
from atlas.alpha.discovery_candidates.api.schemas import DiscoveryCandidateView
from atlas.alpha.discovery_candidates.service import DiscoveryCandidateService

router = APIRouter(prefix="/discovery-candidates", tags=["discovery-candidates"])


@router.get("", response_model=list[DiscoveryCandidateView])
def list_discovery_candidates(
    service: DiscoveryCandidateService = Depends(get_discovery_candidate_service),
) -> list[DiscoveryCandidateView]:
    return [DiscoveryCandidateView.from_domain(c) for c in service.build().candidates]

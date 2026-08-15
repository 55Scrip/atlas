"""REST controller for Observed Decision Properties v1 (Sprint 13).

GET /observed-decision-properties -- the smallest read-only boundary
around the existing, unmodified Pattern Recognition subsystem. Depends
directly on the real `get_decision_repository` (the same dependency the
live `/decisions` endpoint already uses) -- no intermediate service
class, since `build_observed_decision_properties` is already a single
pure function; adding a wrapper class here would be an abstraction this
endpoint does not need.

No request body, no query parameters, no pagination (Sprint 12 Phase
22's own "current real dataset" scale finding), no write path of any
kind. Never computes or serializes a Strategy Signature -- see
`service.py`'s own docstring for why.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from atlas.alpha.observed_decision_properties.api.schemas import ObservedDecisionPropertiesView
from atlas.alpha.observed_decision_properties.service import build_observed_decision_properties
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.infrastructure.api.decision.dependencies import get_decision_repository

router = APIRouter(prefix="/observed-decision-properties", tags=["observed-decision-properties"])


@router.get("", response_model=ObservedDecisionPropertiesView)
def get_observed_decision_properties(
    repository: DecisionRepository = Depends(get_decision_repository),
) -> ObservedDecisionPropertiesView:
    properties = build_observed_decision_properties(repository)
    return ObservedDecisionPropertiesView.from_domain(properties)

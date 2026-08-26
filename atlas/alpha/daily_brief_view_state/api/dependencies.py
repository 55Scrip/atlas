"""Composition wiring for the Daily Brief View State API."""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.daily_brief_view_state.store import DailyBriefViewStateStore
from atlas.alpha.daily_brief_view_state.table import create_daily_brief_view_state_table
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine


def get_daily_brief_view_state_store(
    engine: Engine = Depends(get_decision_engine),
) -> DailyBriefViewStateStore:
    create_daily_brief_view_state_table(engine)
    return DailyBriefViewStateStore(engine)

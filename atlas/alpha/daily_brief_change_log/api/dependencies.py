"""Composition wiring for the Daily Brief Change Log API."""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.daily_brief_change_log.store import DailyBriefChangeLogStore
from atlas.alpha.daily_brief_change_log.table import create_daily_brief_change_log_table
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine


def get_daily_brief_change_log_store(
    engine: Engine = Depends(get_decision_engine),
) -> DailyBriefChangeLogStore:
    create_daily_brief_change_log_table(engine)
    return DailyBriefChangeLogStore(engine)

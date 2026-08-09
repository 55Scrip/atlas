"""Composition wiring for the `BusinessRecord` store (ATLAS-031).

Same shared-engine pattern every other repository's dependencies
module uses -- one physical `atlas.db` file, reused via `decision`'s
own `get_decision_engine`.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine


def get_business_record_repository(
    engine: Engine = Depends(get_decision_engine),
) -> SqlAlchemyBusinessRecordRepository:
    create_business_record_table(engine)
    return SqlAlchemyBusinessRecordRepository(engine)

"""Composition wiring for the Investment Case snapshot store.

Same shared-engine pattern every other repository's dependencies module
uses -- one physical `atlas.db` file, reused via `decision`'s own
`get_decision_engine`, mirroring
`atlas.alpha.business_data_refresh.api.dependencies
.get_business_record_repository` exactly.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.investment_case_change.repository import SqlAlchemyInvestmentCaseSnapshotRepository
from atlas.alpha.investment_case_change.table import create_investment_case_snapshot_table
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine


def get_investment_case_snapshot_repository(
    engine: Engine = Depends(get_decision_engine),
) -> SqlAlchemyInvestmentCaseSnapshotRepository:
    create_investment_case_snapshot_table(engine)
    return SqlAlchemyInvestmentCaseSnapshotRepository(engine)

"""Composition wiring for the Ingestion API. Reuses every sibling
package's own existing provider directly -- `business_data_refresh`'s
own `get_business_record_repository`/`get_canonical_security_identity_gate`/
`get_default_business_data_providers`, never a second provider-
construction path. Never imports `atlas.business_data_providers`
directly (that boundary is confined to `business_data_refresh` alone,
enforced by `tests/test_architecture_boundaries.py`).
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.business_data_refresh.api.dependencies import (
    get_business_record_repository,
    get_canonical_security_identity_gate,
    get_default_business_data_providers,
)
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.canonical_security_gate.gate import CanonicalSecurityIdentityGate
from atlas.alpha.ingestion.repository import SqlAlchemyIngestionResultRepository
from atlas.alpha.ingestion.service import IngestionService
from atlas.alpha.ingestion.table import create_ingestion_result_table
from atlas.analysis_engine.business_data.providers import BusinessDataProvider
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine

__all__ = ["get_ingestion_result_repository", "get_ingestion_service"]


def get_ingestion_result_repository(engine: Engine = Depends(get_decision_engine)) -> SqlAlchemyIngestionResultRepository:
    create_ingestion_result_table(engine)
    return SqlAlchemyIngestionResultRepository(engine)


def get_ingestion_service(
    providers: tuple[BusinessDataProvider, ...] = Depends(get_default_business_data_providers),
    business_record_repository: SqlAlchemyBusinessRecordRepository = Depends(get_business_record_repository),
    identity_gate: CanonicalSecurityIdentityGate = Depends(get_canonical_security_identity_gate),
    ingestion_result_repository: SqlAlchemyIngestionResultRepository = Depends(get_ingestion_result_repository),
) -> IngestionService:
    return IngestionService(
        providers=providers,
        business_record_repository=business_record_repository,
        identity_gate=identity_gate,
        ingestion_result_repository=ingestion_result_repository,
    )

"""SQLAlchemy-backed store for `SecurityIdentityEvidence`. Insert-only
-- see `table.py`'s own docstring. `get_latest` mirrors
`security_confirmation.repository.get_latest_event`'s own
`ORDER BY ... DESC, id DESC LIMIT 1` idiom exactly, for the same
deterministic-tiebreak reason documented there.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from sqlalchemy import desc, insert, select
from sqlalchemy.engine import Engine

from atlas.alpha.security_identity_evidence.models import SecurityIdentityEvidence, SecurityVerificationStatus
from atlas.alpha.security_identity_evidence.table import security_identity_evidence_table

__all__ = ["SqlAlchemySecurityIdentityEvidenceRepository"]


class SqlAlchemySecurityIdentityEvidenceRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, evidence: SecurityIdentityEvidence) -> None:
        with self._engine.begin() as connection:
            connection.execute(insert(security_identity_evidence_table).values(**_to_row(evidence)))

    def get_latest(self, confirmation_id: str) -> SecurityIdentityEvidence | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(security_identity_evidence_table)
                    .where(security_identity_evidence_table.c.confirmation_id == confirmation_id)
                    .order_by(
                        desc(security_identity_evidence_table.c.verified_at),
                        desc(security_identity_evidence_table.c.id),
                    )
                    .limit(1)
                )
                .mappings()
                .first()
            )
        return _to_evidence(row) if row is not None else None


def _to_row(evidence: SecurityIdentityEvidence) -> dict[str, Any]:
    return {
        "id": evidence.id,
        "confirmation_id": evidence.confirmation_id,
        "provider": evidence.provider,
        "status": evidence.status,
        "provider_identifier": evidence.provider_identifier,
        "verified_ticker": evidence.verified_ticker,
        "verified_name": evidence.verified_name,
        "exchange": evidence.exchange,
        "provider_response_json": evidence.provider_response_json,
        "verified_at": evidence.verified_at.isoformat(),
    }


def _to_evidence(row: Mapping[str, Any]) -> SecurityIdentityEvidence:
    status: SecurityVerificationStatus = row["status"]
    return SecurityIdentityEvidence(
        id=row["id"],
        confirmation_id=row["confirmation_id"],
        provider=row["provider"],
        status=status,
        provider_identifier=row["provider_identifier"],
        verified_ticker=row["verified_ticker"],
        verified_name=row["verified_name"],
        exchange=row["exchange"],
        provider_response_json=row["provider_response_json"],
        verified_at=datetime.fromisoformat(row["verified_at"]),
    )

"""SQLAlchemy-backed store for Resolution shadow persistence -- Sprint N
Phase 9/10/14.

`save` persists a full `ResolutionResult` in one transaction: one row
in `resolution_records_table`, and one row per candidate considered in
`resolution_evidence_table` -- every candidate, not only the accepted
one (Phase 10's own "never discard candidates" requirement). `load`
and `find_latest_resolution` reconstruct a `StoredResolution` -- enough
to feed `replay.py` a faithful `ResolutionRequest` -- without needing
the original in-memory `ResolutionResult` object at all.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from sqlalchemy import desc, insert, select
from sqlalchemy.engine import Engine

from atlas.alpha.canonical_security.value_objects import IdentityConfidence, MicCode, TradingCurrency
from atlas.alpha.canonical_security_resolution.candidates import ProviderCandidate
from atlas.alpha.canonical_security_resolution.comparison import FieldComparison
from atlas.alpha.canonical_security_resolution.serialization import (
    comparisons_from_json,
    comparisons_to_json,
)
from atlas.alpha.canonical_security_resolution.service import ResolutionResult
from atlas.alpha.canonical_security_resolution.table import (
    resolution_evidence_table,
    resolution_records_table,
)

__all__ = ["SqlAlchemyResolutionRepository", "StoredResolution", "StoredEvidence"]

_SEQUENCE_WIDTH = 6


@dataclass(frozen=True)
class StoredEvidence:
    candidate: ProviderCandidate
    confidence: IdentityConfidence
    comparisons_against_existing: tuple[FieldComparison, ...]
    accepted: bool


@dataclass(frozen=True)
class StoredResolution:
    id: str
    resolution_version: str
    investor_company_text: str | None
    investor_ticker: str
    normalized_company_text: str
    normalized_ticker: str
    outcome: str
    existing_canonical_security_id: str | None
    resulting_canonical_security_id: str | None
    resolved_at: datetime
    evidence: tuple[StoredEvidence, ...]


class SqlAlchemyResolutionRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def save(
        self,
        result: ResolutionResult,
        *,
        investor_ticker: str,
        investor_company_text: str | None,
        existing_canonical_security_id: str | None,
    ) -> str:
        record_id = str(uuid.uuid4())
        with self._engine.begin() as connection:
            connection.execute(
                insert(resolution_records_table).values(
                    id=record_id,
                    resolution_version=result.resolution_version,
                    investor_company_text=investor_company_text,
                    investor_ticker=investor_ticker,
                    normalized_company_text=result.normalized_company_text,
                    normalized_ticker=result.normalized_ticker,
                    outcome=result.outcome,
                    existing_canonical_security_id=existing_canonical_security_id,
                    resulting_canonical_security_id=(
                        str(result.canonical_security.id) if result.canonical_security else None
                    ),
                    resolved_at=result.resolved_at.isoformat(),
                )
            )
            for index, item in enumerate(result.evidence):
                connection.execute(
                    insert(resolution_evidence_table).values(
                        **_evidence_to_row(record_id, index, item.candidate, item.confidence,
                                            item.comparisons_against_existing, item.accepted)
                    )
                )
        return record_id

    def load(self, record_id: str) -> StoredResolution | None:
        with self._engine.connect() as connection:
            record_row = (
                connection.execute(
                    select(resolution_records_table).where(resolution_records_table.c.id == record_id)
                )
                .mappings()
                .first()
            )
            if record_row is None:
                return None
            evidence_rows = (
                connection.execute(
                    select(resolution_evidence_table)
                    .where(resolution_evidence_table.c.resolution_record_id == record_id)
                    .order_by(resolution_evidence_table.c.sequence)
                )
                .mappings()
                .all()
            )
        return _row_to_stored_resolution(record_row, evidence_rows)

    def find_latest_resolution(self, investor_ticker: str) -> StoredResolution | None:
        with self._engine.connect() as connection:
            record_row = (
                connection.execute(
                    select(resolution_records_table)
                    .where(resolution_records_table.c.investor_ticker == investor_ticker)
                    .order_by(desc(resolution_records_table.c.resolved_at), desc(resolution_records_table.c.id))
                    .limit(1)
                )
                .mappings()
                .first()
            )
            if record_row is None:
                return None
            evidence_rows = (
                connection.execute(
                    select(resolution_evidence_table)
                    .where(resolution_evidence_table.c.resolution_record_id == record_row["id"])
                    .order_by(resolution_evidence_table.c.sequence)
                )
                .mappings()
                .all()
            )
        return _row_to_stored_resolution(record_row, evidence_rows)


def _evidence_to_row(
    record_id: str,
    sequence: int,
    candidate: ProviderCandidate,
    confidence: IdentityConfidence,
    comparisons: tuple[FieldComparison, ...],
    accepted: bool,
) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "resolution_record_id": record_id,
        "sequence": str(sequence).zfill(_SEQUENCE_WIDTH),
        "provider_name": candidate.provider_name,
        "symbol": candidate.symbol,
        "provider_security_id": candidate.provider_security_id,
        "exchange_mic": candidate.exchange_mic.value if candidate.exchange_mic else None,
        "exchange_display_name": candidate.exchange_display_name,
        "country": candidate.country,
        "currency": candidate.currency.value if candidate.currency else None,
        "company_name": candidate.company_name,
        "security_type": candidate.security_type,
        "listing_relationship": candidate.listing_relationship,
        "isin": candidate.isin,
        "figi": candidate.figi,
        "cusip": candidate.cusip,
        "sedol": candidate.sedol,
        "provider_confidence": candidate.provider_confidence,
        "raw_metadata_json": json.dumps(dict(sorted(candidate.raw_metadata.items()))),
        "confidence": confidence,
        "accepted": accepted,
        "comparisons_json": comparisons_to_json(comparisons),
    }


def _row_to_candidate(row: Mapping[str, Any]) -> ProviderCandidate:
    return ProviderCandidate(
        provider_name=row["provider_name"],
        symbol=row["symbol"],
        provider_security_id=row["provider_security_id"],
        exchange_mic=MicCode(row["exchange_mic"]) if row["exchange_mic"] else None,
        exchange_display_name=row["exchange_display_name"],
        country=row["country"],
        currency=TradingCurrency(row["currency"]) if row["currency"] else None,
        company_name=row["company_name"],
        security_type=row["security_type"],
        listing_relationship=row["listing_relationship"],
        isin=row["isin"],
        figi=row["figi"],
        cusip=row["cusip"],
        sedol=row["sedol"],
        provider_confidence=row["provider_confidence"],
        raw_metadata=json.loads(row["raw_metadata_json"]),
    )


def _row_to_stored_resolution(
    record_row: Mapping[str, Any], evidence_rows: list[Mapping[str, Any]]
) -> StoredResolution:
    evidence = tuple(
        StoredEvidence(
            candidate=_row_to_candidate(row),
            confidence=row["confidence"],
            comparisons_against_existing=comparisons_from_json(row["comparisons_json"]),
            accepted=bool(row["accepted"]),
        )
        for row in evidence_rows
    )
    return StoredResolution(
        id=record_row["id"],
        resolution_version=record_row["resolution_version"],
        investor_company_text=record_row["investor_company_text"],
        investor_ticker=record_row["investor_ticker"],
        normalized_company_text=record_row["normalized_company_text"],
        normalized_ticker=record_row["normalized_ticker"],
        outcome=record_row["outcome"],
        existing_canonical_security_id=record_row["existing_canonical_security_id"],
        resulting_canonical_security_id=record_row["resulting_canonical_security_id"],
        resolved_at=datetime.fromisoformat(record_row["resolved_at"]),
        evidence=evidence,
    )

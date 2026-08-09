"""SQLAlchemy-backed `BusinessRecordRepository` (ATLAS-031, Phase 16).

`add` is the only write and is always an INSERT -- a `BusinessRecord`
is immutable and its `id` already encodes its own version
(`{lineage_id}:v{n}`), so there is nothing to update, mirroring
`evidence`'s own repository shape exactly. `get_by_company` and the
batched `get_by_companies` are the only reads real callers need: a
single Case lookup (`InvestmentCaseCompositionService.build`) and a
batched multi-Case lookup (`build_many`, Phase 19 -- one query
regardless of how many companies are requested, not one query per
company).
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import date, datetime
from typing import Any

from sqlalchemy import insert, select
from sqlalchemy.engine import Engine

from atlas.analysis_engine.business_data.contracts import ValidationStatus
from atlas.analysis_engine.business_data.models import BusinessRecord, RecordVersion
from atlas.analysis_engine.business_data.sources import SourceKind as DocumentSourceKind
from atlas.analysis_engine.provenance import Consumer, Provenance, SourceKind as ProvenanceSourceKind, UpdateTrigger
from atlas.alpha.business_data_refresh.table import business_record_table

__all__ = ["SqlAlchemyBusinessRecordRepository"]


class SqlAlchemyBusinessRecordRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, record: BusinessRecord) -> None:
        with self._engine.begin() as connection:
            connection.execute(insert(business_record_table).values(**_to_row(record)))

    def exists(self, record_id: str) -> bool:
        with self._engine.connect() as connection:
            row = connection.execute(
                select(business_record_table.c.id).where(business_record_table.c.id == record_id)
            ).first()
        return row is not None

    def get_by_company(self, company: str) -> tuple[BusinessRecord, ...]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(business_record_table).where(business_record_table.c.company == company)
                )
                .mappings()
                .all()
            )
        return tuple(_to_record(row) for row in rows)

    def get_by_companies(self, companies: tuple[str, ...]) -> dict[str, tuple[BusinessRecord, ...]]:
        """One query for any number of companies -- companies with no
        stored records are still present in the result, mapped to an
        empty tuple, the same honest-absence contract `get_by_company`
        expresses by simply returning `()`."""
        if not companies:
            return {}
        wanted = set(companies)
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(business_record_table).where(business_record_table.c.company.in_(wanted))
                )
                .mappings()
                .all()
            )
        grouped: dict[str, list[BusinessRecord]] = {company: [] for company in companies}
        for row in rows:
            record = _to_record(row)
            grouped.setdefault(record.company, []).append(record)
        return {company: tuple(records) for company, records in grouped.items()}


def _to_row(record: BusinessRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "lineage_id": record.lineage_id,
        "identifier": record.identifier,
        "company": record.company,
        "document_type": record.document_type.value,
        "published_at": record.published_at.isoformat(),
        "provider_id": record.provider_id,
        "source_reference": record.source_reference,
        "content_hash": record.content_hash,
        "version_number": record.version.version_number,
        "version_created_at": record.version.created_at.isoformat(),
        "version_supersedes": record.version.supersedes,
        "version_provider_revision": record.version.provider_revision,
        "validation_status": record.validation_status.value,
        "period_start": record.period_start.isoformat() if record.period_start else None,
        "period_end": record.period_end.isoformat() if record.period_end else None,
        "language": record.language,
        "metadata_json": json.dumps(dict(record.metadata), sort_keys=True),
        "provenance_json": json.dumps(
            {
                "source_kind": record.provenance.source_kind.value,
                "source_references": list(record.provenance.source_references),
                "dependencies": list(record.provenance.dependencies),
                "update_trigger": record.provenance.update_trigger.value,
                "consumers": [consumer.value for consumer in record.provenance.consumers],
                "computed_at": record.provenance.computed_at.isoformat(),
            }
        ),
    }


def _to_record(row: Mapping[str, Any]) -> BusinessRecord:
    provenance_data = json.loads(row["provenance_json"])
    return BusinessRecord(
        id=row["id"],
        lineage_id=row["lineage_id"],
        identifier=row["identifier"],
        company=row["company"],
        document_type=DocumentSourceKind(row["document_type"]),
        published_at=datetime.fromisoformat(row["published_at"]),
        provider_id=row["provider_id"],
        source_reference=row["source_reference"],
        content_hash=row["content_hash"],
        version=RecordVersion(
            version_number=row["version_number"],
            created_at=datetime.fromisoformat(row["version_created_at"]),
            content_hash=row["content_hash"],
            supersedes=row["version_supersedes"],
            provider_revision=row["version_provider_revision"],
        ),
        provenance=Provenance(
            source_kind=ProvenanceSourceKind(provenance_data["source_kind"]),
            source_references=tuple(provenance_data["source_references"]),
            dependencies=tuple(provenance_data["dependencies"]),
            update_trigger=UpdateTrigger(provenance_data["update_trigger"]),
            consumers=tuple(Consumer(value) for value in provenance_data["consumers"]),
            computed_at=datetime.fromisoformat(provenance_data["computed_at"]),
        ),
        validation_status=ValidationStatus(row["validation_status"]),
        period_start=date.fromisoformat(row["period_start"]) if row["period_start"] else None,
        period_end=date.fromisoformat(row["period_end"]) if row["period_end"] else None,
        language=row["language"],
        metadata=json.loads(row["metadata_json"]),
    )

"""Persistence for class economic-rights evidence. Append-only: one
transaction per filing and parser version; a filing already recorded under
that version is left exactly as it is. Nothing is updated or deleted."""
from __future__ import annotations

import json
from datetime import date, datetime

from sqlalchemy import insert, select
from sqlalchemy.engine import Engine
from sqlalchemy.inspection import inspect as sa_inspect

from atlas.alpha.class_rights_evidence.models import (
    CLASS_ECONOMIC_RIGHTS,
    ClassRightsFiling,
    ClassRightsObservation,
    EvidenceStrength,
    RightKind,
)
from atlas.alpha.class_rights_evidence.table import class_rights_filings_table, class_rights_observations_table

__all__ = ["SqlAlchemyClassRightsEvidenceRepository"]

_filings = class_rights_filings_table
_observations = class_rights_observations_table


def _to_observation(row) -> ClassRightsObservation:
    return ClassRightsObservation(
        issuer_cik=row["issuer_cik"], accession=row["accession"], form=row["form"],
        filing_date=date.fromisoformat(row["filing_date"]), observation_key=row["observation_key"],
        kind=RightKind(row["kind"]), strength=EvidenceStrength(row["strength"]),
        subject_member=row["subject_member"], subject_label=row["subject_label"],
        target_member=row["target_member"], target_label=row["target_label"],
        related_members=tuple(json.loads(row["related_members"])), related_labels=tuple(json.loads(row["related_labels"])),
        value=row["value"], value_low=row["value_low"], value_high=row["value_high"], unit=row["unit"],
        decimals=row["decimals"], equity_kind=row["equity_kind"],
        effective_from=date.fromisoformat(row["effective_from"]), effective_to=date.fromisoformat(row["effective_to"]),
        concept=row["concept"], context_id=row["context_id"], excerpt=row["excerpt"],
        parser_version=row["parser_version"], retrieved_at=datetime.fromisoformat(row["retrieved_at"]),
        recorded_at=datetime.fromisoformat(row["recorded_at"]),
    )


class SqlAlchemyClassRightsEvidenceRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def _has_tables(self) -> bool:
        inspector = sa_inspect(self._engine)
        return inspector.has_table(_filings.name) and inspector.has_table(_observations.name)

    def processed(self, accessions: tuple[str, ...]) -> dict[str, frozenset[str]]:
        """Accession -> the parser versions it was already recorded under."""
        if not accessions or not self._has_tables():
            return {}
        out: dict[str, set[str]] = {}
        with self._engine.connect() as connection:
            for accession, version in connection.execute(
                select(_filings.c.accession, _filings.c.parser_version).where(_filings.c.accession.in_(accessions))
            ).all():
                out.setdefault(accession, set()).add(version)
        return {k: frozenset(v) for k, v in out.items()}

    def record_filing(self, filing: ClassRightsFiling, observations: tuple[ClassRightsObservation, ...]) -> bool:
        if any(o.accession != filing.accession or o.issuer_cik != filing.issuer_cik
               or o.parser_version != filing.parser_version for o in observations):
            raise ValueError("every observation must belong to the filing it is recorded with")
        if len({o.observation_key for o in observations}) != len(observations):
            raise ValueError("observation keys must be unique within a filing")
        if filing.parser_version in self.processed((filing.accession,)).get(filing.accession, frozenset()):
            return False
        with self._engine.begin() as connection:
            connection.execute(insert(_filings).values(
                accession=filing.accession, parser_version=filing.parser_version, issuer_cik=filing.issuer_cik,
                form=filing.form, filing_date=filing.filing_date.isoformat(),
                document_period_end=filing.document_period_end.isoformat() if filing.document_period_end else None,
                presented_from=filing.presented_from.isoformat() if filing.presented_from else None,
                instance_url=filing.instance_url, observations=filing.observations,
                retrieved_at=filing.retrieved_at.isoformat(), recorded_at=filing.recorded_at.isoformat(),
            ))
            for o in observations:
                connection.execute(insert(_observations).values(
                    accession=o.accession, observation_key=o.observation_key, parser_version=o.parser_version,
                    evidence_type=CLASS_ECONOMIC_RIGHTS, issuer_cik=o.issuer_cik, form=o.form,
                    filing_date=o.filing_date.isoformat(), kind=o.kind.value, strength=o.strength.value,
                    subject_member=o.subject_member, subject_label=o.subject_label, target_member=o.target_member,
                    target_label=o.target_label, related_members=json.dumps(list(o.related_members)),
                    related_labels=json.dumps(list(o.related_labels)), value=o.value, value_low=o.value_low,
                    value_high=o.value_high, unit=o.unit, decimals=o.decimals, equity_kind=o.equity_kind,
                    effective_from=o.effective_from.isoformat(), effective_to=o.effective_to.isoformat(),
                    concept=o.concept, context_id=o.context_id, excerpt=o.excerpt,
                    retrieved_at=o.retrieved_at.isoformat(), recorded_at=o.recorded_at.isoformat(),
                ))
        return True

    def observations_for_issuers(self, issuer_ciks: frozenset[str], *, filed_by: date | None = None
                                 ) -> dict[str, tuple[ClassRightsObservation, ...]]:
        """Every recorded observation of each issuer, optionally only from
        filings filed by `filed_by`."""
        out: dict[str, tuple[ClassRightsObservation, ...]] = {cik: () for cik in issuer_ciks}
        if not issuer_ciks or not self._has_tables():
            return out
        with self._engine.connect() as connection:
            rows = connection.execute(select(_observations).where(_observations.c.issuer_cik.in_(tuple(issuer_ciks)))).mappings().all()
        found: dict[str, list[ClassRightsObservation]] = {}
        for row in rows:
            o = _to_observation(row)
            if filed_by is None or o.filing_date <= filed_by:
                found.setdefault(o.issuer_cik, []).append(o)
        for cik, obs in found.items():
            out[cik] = tuple(sorted(obs, key=lambda o: (o.filing_date, o.accession, o.observation_key)))
        return out

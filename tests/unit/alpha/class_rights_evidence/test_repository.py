"""Class economic-rights evidence persistence: append-only, idempotent,
filed-by reads, no table created on read, one vocabulary with the adapter."""
from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.class_rights_evidence import (
    RightsFilingRefused,
    RightsFilingSource,
    rights_evidence_from_instance,
)
from atlas.alpha.class_rights_evidence.models import CLASS_ECONOMIC_RIGHTS, EvidenceStrength, RightKind
from atlas.alpha.class_rights_evidence.repository import SqlAlchemyClassRightsEvidenceRepository
from atlas.alpha.class_rights_evidence.table import create_class_rights_evidence_tables
from atlas.business_data_providers import sec_edgar_class_rights as adapter

FIXTURES = Path(__file__).resolve().parents[2] / "business_data_providers" / "fixtures" / "class_rights"
NOW = datetime(2026, 9, 14, tzinfo=timezone.utc)
MA = RightsFilingSource("0001141391", "0001141391-26-000013", "10-K", date(2026, 2, 11), "https://www.sec.gov/Archives/edgar/data/1/x.xml")


def _engine(tables=True):
    e = create_engine("sqlite://", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False})
    if tables:
        create_class_rights_evidence_tables(e)
    return e


def _evidence(source=MA, text=None, **kw):
    xml = text if text is not None else (FIXTURES / f"{source.accession}.xml").read_text()
    return rights_evidence_from_instance(source, xml, retrieved_at=NOW, recorded_at=NOW, **kw)


def test_one_vocabulary_with_the_adapter():
    assert [k.value for k in RightKind] == [k.value for k in adapter.RightKind]
    assert [s.value for s in EvidenceStrength] == [s.value for s in adapter.EvidenceStrength]


def test_round_trip_keeps_strength_span_and_source():
    repo = SqlAlchemyClassRightsEvidenceRepository(_engine())
    filing, obs = _evidence()
    assert repo.record_filing(filing, obs) is True
    back = repo.observations_for_issuers(frozenset({MA.issuer_cik}))[MA.issuer_cik]
    assert set(back) == set(obs) and all(o.evidence_type == CLASS_ECONOMIC_RIGHTS for o in back)
    conversion = next(o for o in back if o.kind is RightKind.CONVERTIBLE_INTO)
    assert (conversion.strength, conversion.effective_from, conversion.effective_to) == (
        EvidenceStrength.FILING_STATEMENT, date(2023, 1, 1), date(2025, 12, 31))
    assert "one-for-one" in conversion.excerpt


def test_append_only_and_idempotent():
    engine = _engine()
    repo = SqlAlchemyClassRightsEvidenceRepository(engine)
    statements = []
    event.listen(engine, "before_cursor_execute", lambda *a: statements.append(a[2].split()[0].upper()))
    filing, obs = _evidence()
    assert repo.record_filing(filing, obs) is True
    assert repo.record_filing(filing, tuple(replace(o, value=999.0) for o in obs)) is False
    assert set(statements) <= {"SELECT", "INSERT", "PRAGMA"}
    assert set(repo.observations_for_issuers(frozenset({MA.issuer_cik}))[MA.issuer_cik]) == set(obs)


def test_reads_filter_by_filing_date_and_never_create_tables():
    repo = SqlAlchemyClassRightsEvidenceRepository(_engine())
    repo.record_filing(*_evidence())
    assert repo.observations_for_issuers(frozenset({MA.issuer_cik}), filed_by=date(2026, 2, 10))[MA.issuer_cik] == ()
    empty = _engine(tables=False)
    assert SqlAlchemyClassRightsEvidenceRepository(empty).observations_for_issuers(frozenset({"1"})) == {"1": ()}
    assert not sa_inspect(empty).get_table_names()


def test_observations_of_another_filing_are_refused_whole():
    repo = SqlAlchemyClassRightsEvidenceRepository(_engine())
    filing, obs = _evidence()
    with pytest.raises(ValueError):
        repo.record_filing(filing, obs + (replace(obs[0], accession="other"),))
    assert repo.processed((MA.accession,)) == {}


@pytest.mark.parametrize("source, change", [
    (replace(MA, issuer_cik="0001652044"), None),
    (replace(MA, form="10-Q"), None),
    (MA, (">false</dei:AmendmentFlag>", ">true</dei:AmendmentFlag>")),
])
def test_an_instance_that_is_not_the_located_filing_is_refused(source, change):
    text = (FIXTURES / f"{MA.accession}.xml").read_text()
    if change:
        assert change[0] in text
        text = text.replace(*change, 1)
    with pytest.raises(RightsFilingRefused):
        _evidence(source, text)

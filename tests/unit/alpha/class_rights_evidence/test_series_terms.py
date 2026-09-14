"""Preferred-series terms derived from persisted rights evidence -- over VST's
real (trimmed) 10-Q, parsed by the production rights parser."""
from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine

from atlas.alpha.business_data_refresh.class_rights_evidence import RightsFilingSource, rights_evidence_from_instance
from atlas.alpha.class_rights_evidence.models import EvidenceStrength, RightKind
from atlas.alpha.class_rights_evidence.repository import SqlAlchemyClassRightsEvidenceRepository
from atlas.alpha.class_rights_evidence.series_terms import SERIES_TERMS_VERSION, derive_series_terms, record_series_terms
from atlas.alpha.class_rights_evidence.table import create_class_rights_evidence_tables

FIXTURES = Path(__file__).resolve().parents[2] / "business_data_providers" / "fixtures" / "class_rights"
NOW = datetime(2026, 9, 11, tzinfo=timezone.utc)
VST, ACC = "0001692819", "0001692819-26-000019"
A, B, C = "us-gaap:SeriesAPreferredStockMember", "us-gaap:SeriesBPreferredStockMember", "us-gaap:SeriesCPreferredStockMember"


def _vst():
    src = RightsFilingSource(VST, ACC, "10-Q", date(2026, 8, 10), "https://www.sec.gov/Archives/edgar/data/1/x_htm.xml")
    return rights_evidence_from_instance(src, (FIXTURES / f"{ACC}.xml").read_text(), retrieved_at=NOW, recorded_at=NOW)


def _by(derived, kind):
    return {o.subject_member: o for o in derived if o.kind is kind}


class TestDerivation:
    def test_issuance_dates_rates_and_resets_come_from_the_tabulated_rows(self):
        _, observations = _vst()
        derived = derive_series_terms(observations, recorded_at=NOW)
        issued = _by(derived, RightKind.SERIES_ISSUED_ON)
        assert {m: o.effective_from for m, o in issued.items()} == {
            A: date(2021, 10, 15), B: date(2021, 12, 10), C: date(2023, 12, 29)}
        rates = _by(derived, RightKind.PREFERRED_DIVIDEND_RATE)
        assert {m: (o.value, o.effective_from, o.effective_to) for m, o in rates.items()} == {
            A: (0.08, date(2021, 10, 15), date(2026, 10, 14)),
            B: (0.07, date(2021, 12, 10), date(2026, 12, 14)),
            C: (0.08875, date(2023, 12, 29), date(2029, 1, 14))}
        assert {m: o.effective_from for m, o in _by(derived, RightKind.DIVIDEND_RATE_RESETS_ON).items()} == {
            A: date(2026, 10, 15), B: date(2026, 12, 15), C: date(2029, 1, 15)}
        assert {m: o.value for m, o in _by(derived, RightKind.PREFERRED_SHARES_OUTSTANDING).items()} == {
            A: 1_000_000, B: 1_000_000, C: 476_066}
        assert _by(derived, RightKind.PREFERRED_SHARES_ISSUED)[C].value == 476_081

    def test_every_derived_observation_keeps_its_source_and_its_own_version(self):
        _, observations = _vst()
        for o in derive_series_terms(observations, recorded_at=NOW):
            assert (o.accession, o.form, o.filing_date, o.issuer_cik) == (ACC, "10-Q", date(2026, 8, 10), VST)
            assert o.parser_version == SERIES_TERMS_VERSION and o.strength is EvidenceStrength.FILING_STATEMENT
            assert o.excerpt and "Series" in o.excerpt and o.concept

    def test_rows_without_their_tables_header_are_not_read(self):
        _, observations = _vst()
        headerless = tuple(replace(o, excerpt=o.excerpt.replace("Issuance Date", "Date")) if o.excerpt else o
                           for o in observations)
        assert derive_series_terms(headerless, recorded_at=NOW) == ()

    def test_order_never_matters(self):
        _, observations = _vst()
        assert derive_series_terms(observations, recorded_at=NOW) == derive_series_terms(
            tuple(reversed(observations)), recorded_at=NOW)


class TestRecording:
    def test_recorded_once_append_only_and_the_parsed_filing_untouched(self, tmp_path):
        engine = create_engine(f"sqlite:///{tmp_path / 'r.db'}", future=True)
        create_class_rights_evidence_tables(engine)
        repo = SqlAlchemyClassRightsEvidenceRepository(engine)
        filing, observations = _vst()
        repo.record_filing(filing, observations)
        before = repo.observations_for_issuers(frozenset({VST}))[VST]
        first = record_series_terms(repo, repo.issuer_ciks(), recorded_at=NOW)
        assert [(a, w) for a, _, w in first] == [(ACC, True)]
        second = record_series_terms(repo, repo.issuer_ciks(), recorded_at=NOW)
        assert [(a, w) for a, _, w in second] == [(ACC, False)]
        after = repo.observations_for_issuers(frozenset({VST}))[VST]
        assert [o for o in after if o.parser_version != SERIES_TERMS_VERSION] == list(before)
        assert sum(o.parser_version == SERIES_TERMS_VERSION for o in after) == first[0][1]

    def test_dry_run_writes_nothing(self, tmp_path):
        engine = create_engine(f"sqlite:///{tmp_path / 'r.db'}", future=True)
        create_class_rights_evidence_tables(engine)
        repo = SqlAlchemyClassRightsEvidenceRepository(engine)
        repo.record_filing(*_vst())
        assert all(not w for _, _, w in record_series_terms(repo, repo.issuer_ciks(), recorded_at=NOW, dry_run=True))
        assert not any(o.parser_version == SERIES_TERMS_VERSION for o in repo.observations_for_issuers(frozenset({VST}))[VST])

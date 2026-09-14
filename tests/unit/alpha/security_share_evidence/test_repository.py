"""Security-level share-class evidence persistence: one transaction per
filing, identity joined on read (CIK + symbol + MIC), and a read path that
never creates a table. In-memory SQLite."""
from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.pool import StaticPool

from atlas.alpha.security_share_evidence.models import (
    SecurityShareCountObservation,
    SecurityShareFiling,
    ShareClassLinkKind,
)
from atlas.alpha.security_share_evidence.repository import SqlAlchemySecurityShareEvidenceRepository
from atlas.alpha.security_share_evidence.table import create_security_share_evidence_tables

NOW = datetime(2026, 9, 14, tzinfo=timezone.utc)
CIK = "0000000001"
PROVEN = ShareClassLinkKind.PROVEN_BY_SHARED_DIMENSION


def _engine(*, tables=True):
    engine = create_engine("sqlite:///:memory:", future=True, poolclass=StaticPool,
                           connect_args={"check_same_thread": False})
    if tables:
        create_security_share_evidence_tables(engine)
    return engine


def listing_mics(listings=(("AAA", "XNAS"), ("BBB", "XNAS"))):
    """The security master as the Identity Gate's seam serves it."""
    def read(tickers):
        return {t: frozenset(m for lt, m in listings if lt == t) for t in tickers}
    return read


def _repository(*, tables=True, listings=(("AAA", "XNAS"), ("BBB", "XNAS"))):
    return SqlAlchemySecurityShareEvidenceRepository(
        _engine(tables=tables), listing_mics=listing_mics(listings) if listings is not None else None)


def observation(**overrides) -> SecurityShareCountObservation:
    base = dict(
        issuer_cik=CIK, accession="0000000001-26-000001", form="10-K", filing_date=date(2026, 2, 5),
        fiscal_period="FY2025", document_period_end=date(2025, 12, 31), period_end=date(2025, 12, 31),
        class_axis="us-gaap:StatementClassOfStockAxis", class_member="us-gaap:CommonClassAMember", shares=100.0,
        conflict=False, source_concept="us-gaap:CommonStockSharesOutstanding", context_id="c1", link_kind=PROVEN,
        cover_title="Class A", cover_symbol="AAA", cover_exchange="NASDAQ", cover_mic="XNAS",
        parser_version="share_class_links_v1", recorded_at=NOW,
    )
    base.update(overrides)
    return SecurityShareCountObservation(**base)


def filing(observations, **overrides) -> SecurityShareFiling:
    o = observations[0]
    base = dict(
        issuer_cik=o.issuer_cik, accession=o.accession, form="10-K", filing_date=o.filing_date, fiscal_period="FY2025",
        document_period_end=date(2025, 12, 31), instance_url="https://www.sec.gov/x_htm.xml", cover_rows=2,
        dimensioned_cover_rows=2, observations=len(observations), proven=1, ambiguous=0, no_link=1, conflicts=0,
        parser_version="share_class_links_v1", processed_at=NOW,
    )
    base.update(overrides)
    return SecurityShareFiling(**base)


class TestWritePath:
    def test_round_trip_and_completion(self):
        repo = _repository()
        a = observation()
        b = observation(class_member="abc:ClassBMember", link_kind=ShareClassLinkKind.NO_LINK, cover_title=None,
                        cover_symbol=None, cover_exchange=None, cover_mic=None, shares=7.0)
        repo.record_filing(filing([a, b]), (a, b))
        assert set(repo.observations_for_issuer(CIK)) == {a, b}
        assert repo.processed_parser_versions((a.accession, "other")) == {a.accession: "share_class_links_v1"}

    def test_re_recording_a_filing_replaces_it_whole(self):
        repo = _repository()
        a = observation()
        repo.record_filing(filing([a]), (a,))
        repo.record_filing(filing([a]), (a,))  # idempotent
        assert repo.observations_for_issuer(CIK) == (a,)
        revised = replace(a, shares=101.0, parser_version="share_class_links_v2")
        repo.record_filing(filing([revised], parser_version="share_class_links_v2"), (revised,))
        assert repo.observations_for_issuer(CIK) == (revised,)
        assert repo.processed_parser_versions((a.accession,)) == {a.accession: "share_class_links_v2"}

    def test_an_observation_of_another_filing_is_refused(self):
        repo = _repository()
        a = observation()
        try:
            repo.record_filing(filing([a]), (replace(a, accession="0000000001-26-000002"),))
        except ValueError:
            pass
        else:
            raise AssertionError("expected a refusal")
        assert repo.observations_for_issuer(CIK) == ()


class TestReadJoin:
    def _seeded(self, **kwargs):
        repo = _repository(**kwargs)
        rows = (
            observation(),
            observation(class_member="abc:ClassCMember", cover_symbol="BBB", context_id="c2"),
            observation(class_member="abc:ClassBMember", link_kind=ShareClassLinkKind.NO_LINK, cover_title=None,
                        cover_symbol=None, cover_exchange=None, cover_mic=None, context_id="c3"),
        )
        repo.record_filing(filing(list(rows)), rows)
        return repo, rows

    def test_each_listing_gets_only_its_own_class(self):
        repo, (a, c, _) = self._seeded()
        joined = repo.proven_for_securities({"AAA": CIK, "BBB": CIK})
        assert joined == {"AAA": (a,), "BBB": (c,)}

    def test_every_part_of_the_identity_must_match(self):
        repo, _ = self._seeded()
        assert repo.proven_for_securities({"AAA": "0000000002"}) == {"AAA": ()}  # another filer's CIK
        assert repo.proven_for_securities({"ZZZ": CIK}) == {"ZZZ": ()}  # no such symbol
        repo, _ = self._seeded(listings=(("AAA", "XNYS"),))
        assert repo.proven_for_securities({"AAA": CIK}) == {"AAA": ()}  # the listing trades elsewhere

    def test_non_proven_observations_are_never_returned(self):
        repo = _repository()
        ambiguous = observation(link_kind=ShareClassLinkKind.AMBIGUOUS)
        repo.record_filing(filing([ambiguous]), (ambiguous,))
        assert repo.proven_for_securities({"AAA": CIK}) == {"AAA": ()}

    def test_the_read_path_never_creates_a_table(self):
        engine = _engine(tables=False)
        repo = SqlAlchemySecurityShareEvidenceRepository(engine, listing_mics=listing_mics())
        assert repo.proven_for_securities({"AAA": CIK}) == {"AAA": ()}
        assert repo.observations_for_issuer(CIK) == () and repo.processed_parser_versions(("x",)) == {}
        assert not sa_inspect(engine).has_table("security_share_observations")
        assert not sa_inspect(engine).has_table("security_share_filings")

    def test_without_the_security_master_nothing_joins(self):
        repo, _ = self._seeded(listings=None)
        assert repo.proven_for_securities({"AAA": CIK}) == {"AAA": ()}

"""Persistence for security-level share-class evidence.

**Writes** come only from the operator's backfill command, one filing per
transaction: the filing's completion row and every observation it yields
land together or not at all, so an interrupted run resumes at the first
filing it did not finish.

**Reads join to Atlas by identity, never by name.** An observation belongs
to an Atlas security when the filing's issuer CIK is the CIK of that
security's own SEC statements, the filing's cover symbol is the listing's
ticker, and the cover exchange's MIC is the listing's MIC -- all three,
from the filing's own cover as of its filing date (a later symbol is never
mapped back). Only `PROVEN_BY_SHARED_DIMENSION` observations are ever
returned. The listing MICs come from the security master through the
Identity Gate's read-only seam (`canonical_security_gate.factory
.build_listing_mic_reader`), injected as `listing_mics` -- without it
nothing joins. The read path never creates a table: without the tables
there is simply no evidence.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime

from sqlalchemy import delete, insert, select
from sqlalchemy.engine import Engine
from sqlalchemy.inspection import inspect as sa_inspect

from atlas.alpha.security_share_evidence.models import (
    CURRENT_COVER_SHARE_COUNT,
    CurrentShareCountEvidence,
    CurrentShareFiling,
    CurrentShareScope,
    SecurityShareCountObservation,
    SecurityShareFiling,
    ShareClassLinkKind,
)
from atlas.alpha.security_share_evidence.table import (
    current_share_filings_table,
    current_share_observations_table,
    security_share_filings_table,
    security_share_observations_table,
)

__all__ = ["SqlAlchemySecurityShareEvidenceRepository"]

_filings = security_share_filings_table
_observations = security_share_observations_table
_current_filings = current_share_filings_table
_current = current_share_observations_table

#: `(tickers) -> {ticker: frozenset of the MICs Atlas lists it on}`.
ListingMics = Callable[[tuple[str, ...]], dict[str, frozenset[str]]]


def _iso(value) -> str | None:
    return value.isoformat() if value is not None else None


def _day(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _to_observation(row) -> SecurityShareCountObservation:
    return SecurityShareCountObservation(
        issuer_cik=row["issuer_cik"], accession=row["accession"], form=row["form"],
        filing_date=date.fromisoformat(row["filing_date"]), fiscal_period=row["fiscal_period"],
        document_period_end=_day(row["document_period_end"]), period_end=date.fromisoformat(row["period_end"]),
        class_axis=row["class_axis"], class_member=row["class_member"], shares=row["shares"],
        conflict=bool(row["conflict"]), source_concept=row["source_concept"], context_id=row["context_id"],
        link_kind=ShareClassLinkKind(row["link_kind"]), cover_title=row["cover_title"],
        cover_symbol=row["cover_symbol"], cover_exchange=row["cover_exchange"], cover_mic=row["cover_mic"],
        parser_version=row["parser_version"], recorded_at=datetime.fromisoformat(row["recorded_at"]),
    )


def _to_current(row) -> CurrentShareCountEvidence:
    return CurrentShareCountEvidence(
        issuer_cik=row["issuer_cik"], accession=row["accession"], form=row["form"],
        filing_date=date.fromisoformat(row["filing_date"]), document_period_end=_day(row["document_period_end"]),
        as_of=date.fromisoformat(row["as_of"]), scope=CurrentShareScope(row["scope"]), class_axis=row["class_axis"],
        class_member=row["class_member"], shares=row["shares"], unit=row["unit"], decimals=row["decimals"],
        conflict=bool(row["conflict"]),
        concept=row["concept"], context_id=row["context_id"], link_kind=ShareClassLinkKind(row["link_kind"]),
        cover_title=row["cover_title"], cover_symbol=row["cover_symbol"], cover_exchange=row["cover_exchange"],
        cover_mic=row["cover_mic"], parser_version=row["parser_version"],
        retrieved_at=datetime.fromisoformat(row["retrieved_at"]), recorded_at=datetime.fromisoformat(row["recorded_at"]),
    )


class SqlAlchemySecurityShareEvidenceRepository:
    def __init__(self, engine: Engine, *, listing_mics: ListingMics | None = None) -> None:
        self._engine = engine
        self._listing_mics = listing_mics

    def _has_tables(self, *names: str) -> bool:
        inspector = sa_inspect(self._engine)
        return all(inspector.has_table(name) for name in names)

    # -- write path (operator command only) ------------------------------------------------------------

    def processed_parser_versions(self, accessions: tuple[str, ...]) -> dict[str, str]:
        if not accessions or not self._has_tables(_filings.name):
            return {}
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(_filings.c.accession, _filings.c.parser_version).where(_filings.c.accession.in_(accessions))
            ).all()
        return {accession: version for accession, version in rows}

    def record_filing(self, filing: SecurityShareFiling, observations: tuple[SecurityShareCountObservation, ...]) -> None:
        """One transaction per filing. Re-recording a filing replaces
        what an earlier parser version stored for it -- never a partial mix."""
        if any(o.accession != filing.accession or o.issuer_cik != filing.issuer_cik for o in observations):
            raise ValueError("every observation must belong to the filing it is recorded with")
        with self._engine.begin() as connection:
            connection.execute(delete(_observations).where(_observations.c.accession == filing.accession))
            connection.execute(delete(_filings).where(_filings.c.accession == filing.accession))
            connection.execute(insert(_filings).values(
                accession=filing.accession, issuer_cik=filing.issuer_cik, form=filing.form,
                filing_date=filing.filing_date.isoformat(), fiscal_period=filing.fiscal_period,
                document_period_end=_iso(filing.document_period_end), instance_url=filing.instance_url,
                cover_rows=filing.cover_rows, dimensioned_cover_rows=filing.dimensioned_cover_rows,
                observations=filing.observations, proven=filing.proven, ambiguous=filing.ambiguous,
                no_link=filing.no_link, conflicts=filing.conflicts, parser_version=filing.parser_version,
                processed_at=filing.processed_at.isoformat(),
            ))
            for o in observations:
                connection.execute(insert(_observations).values(
                    accession=o.accession, class_member=o.class_member, period_end=o.period_end.isoformat(),
                    issuer_cik=o.issuer_cik, form=o.form, filing_date=o.filing_date.isoformat(),
                    fiscal_period=o.fiscal_period, document_period_end=_iso(o.document_period_end),
                    class_axis=o.class_axis, shares=o.shares, conflict=o.conflict, source_concept=o.source_concept,
                    context_id=o.context_id, link_kind=o.link_kind.value, cover_title=o.cover_title,
                    cover_symbol=o.cover_symbol, cover_exchange=o.cover_exchange, cover_mic=o.cover_mic,
                    parser_version=o.parser_version, recorded_at=o.recorded_at.isoformat(),
                ))

    def observations_for_issuer(self, issuer_cik: str) -> tuple[SecurityShareCountObservation, ...]:
        """Every stored observation of one filer, whatever its link kind
        (operator reporting)."""
        if not self._has_tables(_observations.name):
            return ()
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(_observations).where(_observations.c.issuer_cik == issuer_cik)
            ).mappings().all()
        return tuple(_to_observation(r) for r in rows)

    # -- read path (Investment Case composition) -------------------------------------------------------

    def proven_for_securities(self, cik_by_ticker: dict[str, str]) -> dict[str, tuple[SecurityShareCountObservation, ...]]:
        """For each Atlas ticker (with the CIK of its own SEC statements),
        the proven observations its identity joins -- one query for any
        number of tickers. A ticker with none maps to `()`."""
        out: dict[str, tuple[SecurityShareCountObservation, ...]] = {t: () for t in cik_by_ticker}
        if not cik_by_ticker or self._listing_mics is None or not self._has_tables(_observations.name):
            return out
        tickers = tuple(sorted(cik_by_ticker))
        listing_mics = self._listing_mics(tickers)
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(_observations).where(
                    _observations.c.cover_symbol.in_(tickers),
                    _observations.c.link_kind == ShareClassLinkKind.PROVEN_BY_SHARED_DIMENSION.value,
                )
            ).mappings().all()
        found: dict[str, list[SecurityShareCountObservation]] = {}
        for row in rows:
            ticker = row["cover_symbol"]
            if row["issuer_cik"] == cik_by_ticker.get(ticker) and row["cover_mic"] in listing_mics.get(ticker, ()):
                found.setdefault(ticker, []).append(_to_observation(row))
        for ticker, observations in found.items():
            out[ticker] = tuple(sorted(observations, key=lambda o: (o.period_end, o.filing_date, o.accession, o.class_member)))
        return out

    # -- current cover-page share counts (Current Share-Count Evidence v1) ----------------------------

    def current_processed(self, accessions: tuple[str, ...]) -> dict[str, frozenset[str]]:
        """Accession -> the parser versions it was already recorded under."""
        if not accessions or not self._has_tables(_current_filings.name):
            return {}
        out: dict[str, set[str]] = {}
        with self._engine.connect() as connection:
            for accession, version in connection.execute(
                select(_current_filings.c.accession, _current_filings.c.parser_version)
                .where(_current_filings.c.accession.in_(accessions))
            ).all():
                out.setdefault(accession, set()).add(version)
        return {k: frozenset(v) for k, v in out.items()}

    def record_current_filing(self, filing: CurrentShareFiling, evidence: tuple[CurrentShareCountEvidence, ...]) -> bool:
        """Append-only: one transaction per filing and parser version; a
        filing already recorded under this parser version is left exactly
        as it is (returns False). Nothing is ever updated or deleted."""
        if any(e.accession != filing.accession or e.issuer_cik != filing.issuer_cik
               or e.parser_version != filing.parser_version for e in evidence):
            raise ValueError("every observation must belong to the filing it is recorded with")
        if filing.parser_version in self.current_processed((filing.accession,)).get(filing.accession, frozenset()):
            return False
        with self._engine.begin() as connection:
            connection.execute(insert(_current_filings).values(
                accession=filing.accession, parser_version=filing.parser_version, issuer_cik=filing.issuer_cik,
                form=filing.form, filing_date=filing.filing_date.isoformat(),
                document_period_end=_iso(filing.document_period_end), fiscal_period=filing.fiscal_period,
                instance_url=filing.instance_url, cover_rows=filing.cover_rows,
                share_classes_reported=filing.share_classes_reported, counts=filing.counts, proven=filing.proven,
                ambiguous=filing.ambiguous, no_link=filing.no_link, conflicts=filing.conflicts,
                retrieved_at=filing.retrieved_at.isoformat(), recorded_at=filing.recorded_at.isoformat(),
            ))
            for e in evidence:
                connection.execute(insert(_current).values(
                    accession=e.accession, context_id=e.context_id, parser_version=e.parser_version,
                    evidence_type=CURRENT_COVER_SHARE_COUNT, issuer_cik=e.issuer_cik, form=e.form,
                    filing_date=e.filing_date.isoformat(), document_period_end=_iso(e.document_period_end),
                    as_of=e.as_of.isoformat(), scope=e.scope.value, class_axis=e.class_axis, class_member=e.class_member,
                    shares=e.shares, unit=e.unit, decimals=e.decimals, conflict=e.conflict, concept=e.concept,
                    link_kind=e.link_kind.value,
                    cover_title=e.cover_title, cover_symbol=e.cover_symbol, cover_exchange=e.cover_exchange,
                    cover_mic=e.cover_mic, retrieved_at=e.retrieved_at.isoformat(), recorded_at=e.recorded_at.isoformat(),
                ))
        return True

    def filing_locations(self, accessions: tuple[str, ...]) -> dict[str, tuple[str, str, date, str]]:
        """Accession -> (issuer CIK, form, filing date, instance URL) for any
        filing either share-evidence reader already fetched."""
        out: dict[str, tuple[str, str, date, str]] = {}
        if not accessions:
            return out
        with self._engine.connect() as connection:
            for table in (_filings, _current_filings):
                if not self._has_tables(table.name):
                    continue
                for row in connection.execute(
                    select(table.c.accession, table.c.issuer_cik, table.c.form, table.c.filing_date, table.c.instance_url)
                    .where(table.c.accession.in_(accessions))
                ).all():
                    out[row[0]] = (row[1], row[2], date.fromisoformat(row[3]), row[4])
        return out

    def current_classes_reported(self, accessions: tuple[str, ...]) -> dict[str, bool]:
        """Accession -> whether that current filing tags any class-axis member
        on a share fact (its issuer-level count may then span several classes)."""
        if not accessions or not self._has_tables(_current_filings.name):
            return {}
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(_current_filings.c.accession, _current_filings.c.share_classes_reported)
                .where(_current_filings.c.accession.in_(accessions))
            ).all()
        return {accession: bool(flag) for accession, flag in rows}

    def current_evidence_for_issuers(self, issuer_ciks: frozenset[str]) -> dict[str, tuple[CurrentShareCountEvidence, ...]]:
        """Every recorded current cover count of each filer, whatever its link."""
        out: dict[str, tuple[CurrentShareCountEvidence, ...]] = {cik: () for cik in issuer_ciks}
        if not issuer_ciks or not self._has_tables(_current.name):
            return out
        with self._engine.connect() as connection:
            rows = connection.execute(select(_current).where(_current.c.issuer_cik.in_(tuple(issuer_ciks)))).mappings().all()
        found: dict[str, list[CurrentShareCountEvidence]] = {}
        for row in rows:
            found.setdefault(row["issuer_cik"], []).append(_to_current(row))
        for cik, evidence in found.items():
            out[cik] = tuple(sorted(evidence, key=lambda e: (e.as_of, e.filing_date, e.accession, e.context_id)))
        return out

    def current_joined(self, cik_by_ticker: dict[str, str]) -> dict[str, tuple[CurrentShareCountEvidence, ...]]:
        """Per Atlas ticker, the current counts its identity joins: the
        filing's CIK is the ticker's own filer, and a proven link names the
        ticker's symbol on its listing's MIC -- the historical join, applied
        to a different evidence type. `()` without the security master."""
        out: dict[str, tuple[CurrentShareCountEvidence, ...]] = {t: () for t in cik_by_ticker}
        if not cik_by_ticker or self._listing_mics is None:
            return out
        mics = self._listing_mics(tuple(sorted(cik_by_ticker)))
        by_cik = self.current_evidence_for_issuers(frozenset(cik_by_ticker.values()))
        for ticker, cik in cik_by_ticker.items():
            out[ticker] = tuple(
                e for e in by_cik.get(cik, ())
                if e.link_kind is ShareClassLinkKind.PROVEN_BY_SHARED_DIMENSION
                and e.cover_symbol == ticker and e.cover_mic in mics.get(ticker, frozenset())
            )
        return out


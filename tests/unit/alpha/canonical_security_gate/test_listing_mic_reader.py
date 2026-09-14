"""`build_listing_mic_reader` -- the Identity Gate's read-only seam for a
listing's exchange (Security-Level Share-Class Evidence v1)."""
from __future__ import annotations

from sqlalchemy import create_engine, insert
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.pool import StaticPool

from atlas.alpha.canonical_security.table import canonical_security_listings_table, create_canonical_security_tables
from atlas.alpha.canonical_security_gate.factory import build_listing_mic_reader


def _engine():
    return create_engine("sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False})


def test_each_ticker_reads_its_own_listing_mics():
    engine = _engine()
    create_canonical_security_tables(engine)
    with engine.begin() as c:
        for i, (ticker, mic) in enumerate((("GOOG", "XNAS"), ("GOOGL", "XNAS"), ("V", "XNYS"))):
            c.execute(insert(canonical_security_listings_table).values(
                id=f"l{i}", canonical_security_id=f"s{i}", ticker=ticker, exchange_mic=mic, currency="USD",
                relationship="NATIVE", security_type="COMMON_STOCK"))
    read = build_listing_mic_reader(engine)
    assert read(("GOOG", "V", "ZZZ")) == {"GOOG": frozenset({"XNAS"}), "V": frozenset({"XNYS"}), "ZZZ": frozenset()}


def test_it_creates_nothing():
    engine = _engine()
    assert build_listing_mic_reader(engine)(("GOOG",)) == {"GOOG": frozenset()}
    assert not sa_inspect(engine).has_table(canonical_security_listings_table.name)

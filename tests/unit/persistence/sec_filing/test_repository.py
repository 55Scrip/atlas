"""Storing SEC filing provenance beside the facts it produced."""
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine

from atlas.business_data_providers.sec_filing.facts import SEC_FILING_READER_VERSION, filing_facts
from atlas.core.infrastructure.persistence.dimensional_fact.repository import DimensionalFactRepository
from atlas.core.infrastructure.persistence.sec_filing.repository import (
    SecFilingRepository,
    StoredFiling,
)
from tests.unit.business_data_providers.sec_filing.test_facts import (
    CTX_PLAIN,
    CTX_SEGMENT,
    F_DEI,
    F_SEGMENT,
    IDENTITY,
    instance,
)

AT = datetime(2026, 9, 18, tzinfo=UTC)


@pytest.fixture
def repositories(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path/'t.db'}", future=True)
    return DimensionalFactRepository(engine), SecFilingRepository(engine), engine


def a_filing(**overrides):
    base = dict(
        source_locator=IDENTITY.source_locator, cik="0001652044",
        accession=IDENTITY.accession, form_type="10-K", period_end="2025-12-31",
        filed_at="2026-02-05", primary_document=IDENTITY.primary_document,
        primary_document_url=IDENTITY.primary_document_url,
        primary_document_sha256="a" * 64, primary_document_bytes=2_616_499,
        instance_document=IDENTITY.instance_document, instance_url=IDENTITY.instance_url,
        instance_sha256="b" * 64, instance_bytes=2_880_903,
        fact_count=1858, dimensioned_fact_count=876,
        reader_version=SEC_FILING_READER_VERSION, observed_at="",
    )
    base.update(overrides)
    return StoredFiling(**base)


def test_a_filing_round_trips_with_its_provenance(repositories):
    _, filings, _ = repositories
    filings.store([a_filing()], observed_at=AT)
    (stored,) = filings.query()
    assert stored.accession == "0001652044-26-000018"
    assert stored.cik == "0001652044"
    assert stored.primary_document_url.startswith("https://www.sec.gov/Archives/")
    assert stored.instance_sha256 == "b" * 64
    assert stored.fact_count == 1858
    assert stored.observed_at


def test_facts_are_stored_under_the_sec_reader_not_the_esef_one(repositories):
    facts_repo, _, _ = repositories
    _, facts = filing_facts(instance(CTX_SEGMENT, CTX_PLAIN, F_DEI, F_SEGMENT), IDENTITY)
    facts_repo.store(facts, observed_at=AT, reader_version=SEC_FILING_READER_VERSION)
    assert {f.reader_version for f in facts_repo.query()} == {SEC_FILING_READER_VERSION}


def test_a_fact_carries_the_accession_that_filed_it(repositories):
    facts_repo, _, _ = repositories
    _, facts = filing_facts(instance(CTX_SEGMENT, CTX_PLAIN, F_DEI, F_SEGMENT), IDENTITY)
    facts_repo.store(facts, observed_at=AT, reader_version=SEC_FILING_READER_VERSION)
    assert {f.source_locator for f in facts_repo.query()} == {
        "0001652044-26-000018:goog-20251231.htm"}


def test_re_storing_one_filing_replaces_only_its_own_row(repositories):
    _, filings, _ = repositories
    other = a_filing(source_locator="0000006951-25-056742:amat-20251026.htm",
                     cik="0000006951", accession="0000006951-25-056742")
    filings.store([a_filing(), other], observed_at=AT)
    filings.store([a_filing(fact_count=99)], observed_at=AT)
    rows = {f.source_locator: f for f in filings.query()}
    assert len(rows) == 2
    assert rows[IDENTITY.source_locator].fact_count == 99
    assert rows[other.source_locator].fact_count == 1858


def test_the_filing_query_is_generic(repositories):
    _, filings, _ = repositories
    filings.store([a_filing()], observed_at=AT)
    assert len(filings.query(cik="0001652044")) == 1
    assert len(filings.query(form_type="10-K")) == 1
    assert len(filings.query(period_end="2025-12-31")) == 1
    assert len(filings.query(cik="0000000000")) == 0
    # and there is deliberately no strategy-shaped question on it
    assert not hasattr(filings, "filings_for_strategy")


def test_a_long_text_block_is_elided_with_a_provable_digest(repositories):
    # 190 of 7,915 facts in four filings are 91.3% of all their value
    # bytes, the largest 291 KB of embedded HTML. Storing those inline
    # would grow the database by roughly a gigabyte for the corpus.
    import hashlib

    facts_repo, _, engine = repositories
    # SEC files a text block as ESCAPED html, so it is text content
    # rather than child elements -- which is why it survives the reader
    # at full length.
    note = "&lt;p&gt;" + ("segment disclosure " * 2000) + "&lt;/p&gt;"
    block = (f'<us-gaap:SegmentReportingDisclosureTextBlock contextRef="c-1" id="f-50">'
             f'{note}</us-gaap:SegmentReportingDisclosureTextBlock>')
    _, facts = filing_facts(instance(CTX_PLAIN, F_DEI, block), IDENTITY)
    facts_repo.store(facts, observed_at=AT, reader_version=SEC_FILING_READER_VERSION)
    stored = next(f for f in facts_repo.query() if f.concept.endswith("TextBlock"))
    assert stored.value_text.startswith("(value elided:")
    unescaped = note.replace("&lt;", "<").replace("&gt;", ">")
    assert stored.value_bytes == len(unescaped.encode())
    assert stored.value_digest == hashlib.sha256(unescaped.encode()).hexdigest()


def test_a_short_value_is_stored_verbatim(repositories):
    facts_repo, _, _ = repositories
    _, facts = filing_facts(instance(CTX_SEGMENT, CTX_PLAIN, F_DEI, F_SEGMENT), IDENTITY)
    facts_repo.store(facts, observed_at=AT, reader_version=SEC_FILING_READER_VERSION)
    revenue = next(f for f in facts_repo.query() if "Revenue" in f.concept)
    assert revenue.value_text == "175033000000"
    assert revenue.value_bytes == len("175033000000")


def test_the_esef_reader_still_stores_under_its_own_version(repositories, tmp_path):
    # The store is shared now. An ESEF caller that passes no version
    # must still be recorded as ESEF, not as SEC.
    from atlas.business_data_providers.esef.dimensions import (
        DIMENSION_READER_VERSION, dimensional_facts,
    )

    facts_repo, _, _ = repositories
    document = {"facts": {"f-1": {"value": "1", "decimals": -6, "dimensions": {
        "concept": "ifrs-full:Equity", "entity": "e", "period": "2021-01-01T00:00:00",
        "ifrs-full:ComponentsOfEquityAxis": "ifrs-full:IssuedCapitalMember",
        "unit": "iso4217:SEK"}}}}
    facts_repo.store(dimensional_facts(document, source_locator="r.json"), observed_at=AT)
    assert {f.reader_version for f in facts_repo.query()} == {DIMENSION_READER_VERSION}

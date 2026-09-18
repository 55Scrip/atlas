"""Storing dimensional evidence without disturbing anything that exists."""
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, inspect

from atlas.business_data_providers.esef.dimensions import AxisClass, dimensional_facts
from atlas.core.infrastructure.persistence.dimensional_fact.repository import (
    DimensionalFactRepository,
)
from tests.unit.business_data_providers.esef.test_dimensions import (
    CONSOLIDATED_REVENUE,
    TRANSFORM_ERROR,
    EQUITY,
    MULTI,
    SEGMENT_CAPEX,
    SEGMENT_RND,
    TYPO,
    document,
)

AT = datetime(2026, 9, 18, tzinfo=UTC)


@pytest.fixture
def repository(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path/'t.db'}", future=True)
    return DimensionalFactRepository(engine), engine


def ingest(repository, *facts, source_locator="r.json"):
    repo, _ = repository
    return repo.store(
        dimensional_facts(document(*facts), source_locator=source_locator), observed_at=AT
    )


def test_a_later_report_restating_a_figure_does_not_overwrite_the_original(repository):
    # An annual report restates the prior year beside the current one,
    # so the same coordinates recur across consecutive filings. In this
    # corpus 25 such pairs disagree. If the report were not part of the
    # identity, whichever filing was ingested last would win and Atlas
    # could not see that a restatement had happened at all.
    repo, _ = repository
    restated = {**EQUITY, "value": "999000000.0"}
    ingest(repository, EQUITY, source_locator="2023.json")
    ingest(repository, restated, source_locator="2024.json")
    stored = repo.query()
    assert len(stored) == 2
    assert {s.value_text for s in stored} == {EQUITY["value"], "999000000.0"}
    assert {s.source_locator for s in stored} == {"2023.json", "2024.json"}


def test_re_ingesting_one_report_still_replaces_only_its_own_facts(repository):
    # The other half of the same property: the report being part of the
    # identity must not cost idempotence for a single report.
    repo, _ = repository
    ingest(repository, EQUITY, source_locator="2023.json")
    ingest(repository, SEGMENT_RND, source_locator="2024.json")
    before = {(s.source_locator, s.value_text) for s in repo.query()}
    ingest(repository, EQUITY, source_locator="2023.json")
    assert {(s.source_locator, s.value_text) for s in repo.query()} == before


def test_a_transform_error_survives_storage_marked_unusable(repository):
    # It must still be there after a round trip -- dropping it would
    # erase the evidence that the filing was broken here -- and it must
    # still be marked, so a consumer reading the table alone cannot
    # take the sentinel for a quantity.
    repo, _ = repository
    ingest(repository, TRANSFORM_ERROR)
    (stored,) = repo.query()
    assert stored.value_text == "(ixTransformValueError)"
    assert stored.value_status == "unparsable"


def test_a_real_figure_survives_storage_marked_numeric(repository):
    repo, _ = repository
    ingest(repository, SEGMENT_RND)
    (stored,) = repo.query()
    assert stored.value_status == "numeric"


def test_storing_a_fact_with_no_source_locator_is_refused(repository):
    repo, _ = repository
    with pytest.raises(ValueError, match="source_locator"):
        repo.store(dimensional_facts(document(EQUITY)), observed_at=AT)


# ----------------------------------------------------------------- 17,18
def test_a_fact_round_trips_with_its_axes_and_provenance(repository):
    repo, _ = repository
    ingest(repository, SEGMENT_RND)
    (stored,) = repo.query()
    assert stored.concept == "ifrs-full:ResearchAndDevelopmentExpense"
    assert stored.value_text == "30957000000.0"
    assert stored.unit == "iso4217:SEK"
    assert stored.period_end == "2024-12-31"
    assert stored.period_kind == "duration"
    assert stored.entity == "scheme:549300HGV012CNC8JD22"
    assert stored.source_locator == "r.json"
    assert stored.reader_version
    assert stored.observed_at
    assert {d.axis_qname for d in stored.dimensions} == {
        "ifrs-full:SegmentConsolidationItemsAxis", "ifrs-full:SegmentsAxis"}


def test_a_multi_axis_fact_stores_its_value_once(repository):
    # One row per fact, its axes beside it -- not one row per axis, which
    # would repeat the value and let a later SUM double count a figure
    # for the crime of being precisely described.
    repo, engine = repository
    ingest(repository, MULTI)
    with engine.begin() as connection:
        facts = connection.exec_driver_sql("select count(*) from esef_dimensional_fact").scalar()
        axes = connection.exec_driver_sql("select count(*) from esef_dimensional_fact_axis").scalar()
    assert (facts, axes) == (1, 2)


# ------------------------------------------------------------------- 19
def test_re_ingesting_the_same_report_adds_nothing(repository):
    repo, engine = repository
    first = ingest(repository, SEGMENT_RND, EQUITY, MULTI)
    second = ingest(repository, SEGMENT_RND, EQUITY, MULTI)
    assert first == second == 3
    with engine.begin() as connection:
        assert connection.exec_driver_sql(
            "select count(*) from esef_dimensional_fact").scalar() == 3
        # SEGMENT_RND carries two axes, EQUITY one, MULTI two.
        assert connection.exec_driver_sql(
            "select count(*) from esef_dimensional_fact_axis").scalar() == 5


def test_re_storing_one_fact_leaves_no_stale_axis_behind(repository):
    # A fact's axes are part of what it claims. Storing it again with a
    # changed value must not leave an axis row from the previous write,
    # which would silently alter what the stored fact says.
    repo, engine = repository
    ingest(repository, MULTI)
    restated = {**MULTI, "value": "1600000000"}
    ingest(repository, restated)
    stored = repo.query()
    assert len(stored) == 1, "same concept, entity, period, unit and axes -- one fact"
    assert stored[0].value_text == "1600000000"
    assert len(stored[0].dimensions) == 2
    with engine.begin() as connection:
        assert connection.exec_driver_sql(
            "select count(*) from esef_dimensional_fact_axis").scalar() == 2


# ------------------------------------------------------------------- 20
def test_one_payload_listing_a_fact_twice_stores_it_once(repository):
    # Distinct from re-ingesting a report: this is the same fact twice
    # inside a single write, which the delete-then-insert cannot catch
    # because both rows arrive together.
    repo, engine = repository
    stored = ingest(repository, SEGMENT_RND, dict(SEGMENT_RND))
    assert stored == 1
    with engine.begin() as connection:
        assert connection.exec_driver_sql(
            "select count(*) from esef_dimensional_fact").scalar() == 1


def test_storage_is_order_independent(repository, tmp_path):
    repo, _ = repository
    ingest(repository, SEGMENT_RND, EQUITY, MULTI)
    forward = [f.fact_key for f in repo.query()]
    other = DimensionalFactRepository(create_engine(f"sqlite:///{tmp_path/'u.db'}", future=True))
    other.store(dimensional_facts(document(MULTI, EQUITY, SEGMENT_RND), source_locator="r.json"),
                observed_at=AT)
    assert sorted(forward) == sorted(f.fact_key for f in other.query())


# ------------------------------------------------------------ query seam
def test_the_query_seam_is_generic(repository):
    repo, _ = repository
    ingest(repository, SEGMENT_RND, SEGMENT_CAPEX, EQUITY, MULTI, TYPO)
    assert len(repo.query(entity="scheme:549300HGV012CNC8JD22")) == 3
    assert len(repo.query(concept="ifrs-full:ResearchAndDevelopmentExpense")) == 1
    assert len(repo.query(axis_class=AxisClass.BUSINESS_SEGMENT)) == 2
    assert len(repo.query(axis_class=AxisClass.EQUITY_COMPONENT)) == 2
    assert len(repo.query(member_qname="abvolvo:FinancialServciesMember")) == 1
    assert len(repo.query(axis_qname="ifrs-full:SegmentsAxis")) == 2
    assert len(repo.query(period_end="2024-12-31")) == 2
    assert len(repo.query()) == 5


def test_the_axis_inventory_reports_what_is_held(repository):
    repo, _ = repository
    ingest(repository, SEGMENT_RND, EQUITY)
    held = {axis: (klass, n) for axis, klass, n in repo.axes()}
    assert held["ifrs-full:SegmentsAxis"][0] == "business_segment"
    assert held["ifrs-full:ComponentsOfEquityAxis"][0] == "equity_component"


# ----------------------------------------------------------------- 1,30
def test_a_consolidated_fact_is_never_stored_here(repository):
    repo, _ = repository
    assert ingest(repository, CONSOLIDATED_REVENUE) == 0
    assert repo.query() == ()


def test_the_new_tables_do_not_touch_any_existing_table(repository):
    _, engine = repository
    names = set(inspect(engine).get_table_names())
    assert names == {"esef_dimensional_fact", "esef_dimensional_fact_axis"}


def test_creating_the_tables_twice_is_safe(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path/'v.db'}", future=True)
    DimensionalFactRepository(engine)
    repo = DimensionalFactRepository(engine)
    repo.store(dimensional_facts(document(SEGMENT_RND), source_locator="r.json"), observed_at=AT)
    assert len(repo.query()) == 1

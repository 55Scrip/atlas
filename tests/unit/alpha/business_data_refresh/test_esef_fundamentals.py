"""What a European filing becomes once it is a Business Record.

The parsing is tested where the parsing lives. What is tested here is the
handful of decisions taken on the way out, at the only sanctioned route from
`atlas.business_data_providers` into the record store -- and each of these
was written after a mutation showed the suite did not hold it.

The first is the one that matters most. `published_at` is Atlas's
availability boundary: it is what stops a figure from being used before it
existed. Replacing it with the period end is a one-token edit that no test
noticed, and it would date Volvo's 2024 accounts to 31 December 2024, five
months before anyone could read them -- a look-ahead, silently, in every
European record Atlas holds.
"""
from __future__ import annotations

import json
from datetime import date

from atlas.alpha.business_data_refresh.esef_fundamentals import (
    EsefPeriodEvidence,
    document_for,
    newest_per_period,
)
from atlas.business_data_providers.esef.debt import DebtOutcome, DebtResolution
from atlas.business_data_providers.esef.normalization import NormalizedPeriod
from atlas.business_data_providers.esef.source import EsefFiling

LEI = "549300HGV012CNC8JD22"


def filing(**overrides) -> EsefFiling:
    base = dict(
        lei=LEI,
        period_end=date(2024, 12, 31),
        published_at=date(2025, 5, 8),
        country="SE",
        facts_path="/a/report.json",
        package_path="/a/report.zip",
        report_path="/a/report.xhtml",
        sha256=None,
        filing_id=f"{LEI}-2024-12-31-ESEF-SE-0",
    )
    base.update(overrides)
    return EsefFiling(**base)


def evidence(**overrides) -> EsefPeriodEvidence:
    period = overrides.pop("period", None) or NormalizedPeriod(
        period_end="2024-12-31", currency="SEK", values={"revenue": 526_792e6})
    debt = overrides.pop("debt", None) or DebtResolution(
        DebtOutcome.NOT_TAGGED, "no borrowings tagged")
    return EsefPeriodEvidence(filing=filing(**overrides), period=period, debt=debt)


# --- Publication date is the availability boundary ---------------------


def test_a_record_is_dated_when_the_filing_became_readable() -> None:
    record = document_for("VOLV-B", evidence(), LEI)
    assert record.published_at.date() == date(2025, 5, 8)


def test_a_record_is_never_dated_by_the_year_it_describes() -> None:
    """The look-ahead. A 2024 fiscal year that claims to have been published
    on 2024-12-31 is available to every evaluator five months early, and
    nothing downstream can tell that it was not."""
    record = document_for("VOLV-B", evidence(), LEI)
    assert record.published_at.date() != date(2024, 12, 31)
    assert record.published_at.date() > record.period_end


def test_the_period_end_is_still_the_period_end() -> None:
    """Erring late on availability must not move the year the figures are
    about -- that would misalign debt against cash flow."""
    assert document_for("VOLV-B", evidence(), LEI).period_end == date(2024, 12, 31)


# --- The filing's own defects travel with the record -------------------


def test_a_broken_field_is_recorded_as_broken_not_merely_absent() -> None:
    """Investor's 2023 report tagged nine fields and carried a converter
    error instead of a value for every one of them. A record that says only
    "withheld" cannot tell that apart from a company that reports nothing,
    and the difference decides whether a later filing is worth re-reading."""
    period = NormalizedPeriod(
        period_end="2023-12-31", currency=None, withheld=("revenue", "cash"),
        reported_but_unusable=("revenue",))
    record = document_for("INVE-B", evidence(period=period), LEI)
    assert json.loads(record.metadata["esef_reported_but_unusable"]) == ["revenue"]
    assert json.loads(record.metadata["esef_withheld"]) == ["cash", "revenue"]


def test_a_period_with_nothing_broken_says_so_rather_than_saying_nothing() -> None:
    record = document_for("VOLV-B", evidence(), LEI)
    assert json.loads(record.metadata["esef_reported_but_unusable"]) == []


def test_the_broken_fields_reach_the_content_hash() -> None:
    """Two filings that withhold the same fields for different reasons are
    not the same evidence, and must not deduplicate onto each other."""
    withheld = ("revenue",)
    silent = NormalizedPeriod(period_end="2023-12-31", currency=None, withheld=withheld)
    broken = NormalizedPeriod(period_end="2023-12-31", currency=None, withheld=withheld,
                              reported_but_unusable=withheld)
    assert (document_for("INVE-B", evidence(period=silent), LEI).content_hash
            != document_for("INVE-B", evidence(period=broken), LEI).content_hash)


# --- One filing per fiscal year ----------------------------------------


def test_the_same_year_filed_twice_is_one_piece_of_evidence() -> None:
    """An issuer files the same annual report in Swedish and in English and
    the index lists both. They are one report; ingesting both would duplicate
    every fact in it."""
    swedish = filing(filing_id=f"{LEI}-2024-12-31-ESEF-SE-0")
    english = filing(filing_id=f"{LEI}-2024-12-31-ESEF-SE-1")
    assert len(newest_per_period((swedish, english))) == 1


def test_different_years_are_different_evidence() -> None:
    assert len(newest_per_period((
        filing(period_end=date(2024, 12, 31)),
        filing(period_end=date(2023, 12, 31), filing_id="other"),
    ))) == 2


def test_the_copy_that_carries_facts_is_the_one_kept() -> None:
    """Some index entries have no facts document. A language duplicate that
    does is the usable one, whichever order they arrive in."""
    without = filing(facts_path=None, filing_id="no-facts")
    with_facts = filing(filing_id="has-facts")
    for order in ((without, with_facts), (with_facts, without)):
        assert newest_per_period(order)[0].filing_id == "has-facts"


def test_years_come_back_newest_first() -> None:
    chosen = newest_per_period((
        filing(period_end=date(2022, 12, 31), filing_id="a"),
        filing(period_end=date(2024, 12, 31), filing_id="b"),
        filing(period_end=date(2023, 12, 31), filing_id="c"),
    ))
    assert [f.period_end.year for f in chosen] == [2024, 2023, 2022]

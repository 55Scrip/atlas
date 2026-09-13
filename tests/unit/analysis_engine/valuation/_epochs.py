"""Builders for FCF-yield inputs in the fiscal-epoch construction
(Valuation Observation Integrity).

Periods are real ISO dates: a fiscal year ends, its annual statement is filed
weeks later, and market observations sit on trading dates -- the evaluator's
whole job is keeping those three apart. Statement facts come from records
whose id starts with ``stmt-``; `evaluate` treats exactly those as annual
financial statements unless told otherwise.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from itertools import count

from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.provenance import Provenance, SourceKind, UpdateTrigger
from atlas.analysis_engine.valuation.cash_flow import evaluate_fcf_yield_relative
from atlas.analysis_engine.valuation.facts import ValuationFact, ValuationFactKind
from atlas.analysis_engine.valuation.models import ValuationFinding
from tests.unit.analysis_engine.valuation._real_cases import CASES

AS_OF = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)
#: Any operating-business industry label; the method applies to it.
APPLICABLE = "SOFTWARE - INFRASTRUCTURE"

_ids = count()


def _prov() -> Provenance:
    return Provenance(
        source_kind=SourceKind.ANALYSIS_ENGINE_STAGE, source_references=(), dependencies=(),
        update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED, consumers=(), computed_at=AS_OF,
    )


def _at(day: date | str) -> datetime:
    day = date.fromisoformat(day) if isinstance(day, str) else day
    return datetime(day.year, day.month, day.day, tzinfo=timezone.utc)


def business_fact(
    kind: BusinessFactKind, value: float, period: str, published: date | str, *, record: str, unit: str = "USD"
) -> BusinessFact:
    return BusinessFact(
        id=f"{record}:{kind.value}:{period}", company="TEST", kind=kind, value=value, unit=unit, period=period,
        source_record_id=record, provenance=_prov(), extracted_at=AS_OF, published_at=_at(published),
    )


def statement_fcf(value: float, period: str, filed: date | str, *, record: str | None = None, unit: str = "USD"):
    """Free cash flow from an annual financial statement filed on `filed`."""
    return business_fact(
        BusinessFactKind.FREE_CASH_FLOW, value, period, filed, record=record or f"stmt-{next(_ids)}", unit=unit
    )


def report_fcf(value: float, period: str, published: date | str, *, record: str | None = None):
    """Free cash flow from a record that is not an annual statement."""
    return business_fact(BusinessFactKind.FREE_CASH_FLOW, value, period, published, record=record or f"report-{next(_ids)}")


def filing(filed: date | str, period: str = "2000-12-31"):
    """A statement filed on `filed` that carries something other than free
    cash flow -- a filing date Atlas knows, and nothing else."""
    return business_fact(BusinessFactKind.REVENUE, 1.0, period, filed, record=f"stmt-{next(_ids)}")


def quote(period: str, price: float, shares: float = 100.0, unit: str = "USD") -> tuple[ValuationFact, ValuationFact]:
    record = f"quote-{next(_ids)}"

    def one(kind: ValuationFactKind, value: float) -> ValuationFact:
        return ValuationFact(
            id=f"{record}:{kind.value}:{period}", company="TEST", kind=kind, value=value, unit=unit, period=period,
            source_record_id=record, provenance=_prov(), extracted_at=AS_OF, published_at=_at(period),
        )

    return (one(ValuationFactKind.SHARE_PRICE, price), one(ValuationFactKind.SHARES_OUTSTANDING, shares))


def evaluate(
    business_facts,
    valuation_facts,
    *,
    industry: str | None = APPLICABLE,
    at: datetime = AS_OF,
    statements: frozenset[str] | None = None,
) -> ValuationFinding:
    if statements is None:
        statements = frozenset(f.source_record_id for f in business_facts if f.source_record_id.startswith("stmt-"))
    return evaluate_fcf_yield_relative(
        tuple(business_facts), tuple(valuation_facts), statement_record_ids=statements, industry=industry, evaluated_at=at
    )


def filed_on(year: int) -> date:
    """Fiscal year `year` (ending 12-31) is filed mid-February next year."""
    return date(year + 1, 2, 14)


def first_quote_day(year: int) -> str:
    """The first market observation after fiscal year `year` was filed."""
    return (filed_on(year) + timedelta(days=14)).isoformat()


def annual_history(fcf: dict[int, float], prices: dict[int, float], *, shares: float = 100.0):
    """One statement per fiscal year (filed in its own year's report) and one
    market observation shortly after each filing, for every year in
    `prices`. Returns `(business_facts, valuation_facts)`."""
    business = [statement_fcf(value, f"{year}-12-31", filed_on(year)) for year, value in sorted(fcf.items())]
    market = [fact for year, value in sorted(prices.items()) for fact in quote(first_quote_day(year), value, shares)]
    return business, market


def real_case(ticker: str):
    """`(business_facts, valuation_facts, industry)` exactly as Atlas holds them."""
    case = CASES[ticker]
    business = []
    for period, value, unit, published, source in case["fcf"]:
        record = f"stmt-{ticker}-{period}" if source == "statement" else f"{source}-{ticker}-{period}"
        business.append(business_fact(BusinessFactKind.FREE_CASH_FLOW, value, period, published, record=record, unit=unit))
    for filed in case["filings"]:
        business.append(filing(filed))
    market = [fact for day, price, shares, unit in case["quotes"] for fact in quote(day, price, shares, unit)]
    return business, market, case["industry"]

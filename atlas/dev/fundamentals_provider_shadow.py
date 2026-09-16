"""What a fundamentals provider must actually supply, stated as a test.

Atlas's requirement is not "financial statements". It is a specific set of
fields with specific temporal semantics, and the difference decides whether a
vendor is useful or merely plausible. This harness answers that empirically:
it feeds one company's annual figures to Atlas's real evaluators, in memory,
and reports what each of them concludes.

Nothing here reads or writes the live database, creates a Case, or produces a
recommendation. It imports the evaluators and calls them on constructed facts.

Run it against a candidate provider's data before believing a coverage claim:

    python -m atlas.dev.fundamentals_provider_shadow

The four scenarios are the ones that separated real candidates from apparent
ones during the September 2026 European provider evaluation:

* **full** -- every field present, with a real filing date. Financial Risk
  concludes; the fiscal epochs form with 3 priors, which is exactly what
  `MINIMUM_PRIOR_EPOCHS` requires.
* **no_debt** -- what raw ESEF filings actually give you. No issuer in the
  sample tagged total debt with a standard IFRS concept, so Financial Risk
  returns `MISSING_DEBT` and concludes nothing.
* **no_filing_date** -- what most commercial vendors give you for non-US
  companies: a filing date collapsed onto the period end, or none at all.
  Financial Risk is unaffected -- it never reads the date. The valuation's
  prior epochs collapse from 3 to 0, because an epoch may not be priced
  before its figures were public and a same-day date proves nothing was.
  This is the single most expensive thing a vendor can get wrong, and it is
  invisible in any coverage table.
* **no_basis** -- fundamentals and market data both present, no issuer
  common-equity basis. Withholds on `DENOMINATOR_EVIDENCE_MISSING`, which
  production reaches whenever there is no SEC CIK for the issuer.

The figures below are Volvo's, taken from its own ESEF annual reports. They
are here to make the scenarios concrete, not because Atlas holds them.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.provenance import Provenance, SourceKind, UpdateTrigger
from atlas.analysis_engine.risk.financial_risk import evaluate_financial_risk
from atlas.analysis_engine.valuation.cash_flow import evaluate_fcf_yield_relative, fiscal_epochs
from atlas.analysis_engine.valuation.facts import ValuationFact, ValuationFactKind

#: Volvo AB, consolidated, from its ESEF filings: revenue, operating cash
#: flow, capital expenditure, all SEK. Free cash flow is derived the way
#: Atlas defines it (OCF - capex) rather than taken from a vendor field.
#: Capex is the point of interest: Volvo tags it with a company-specific
#: extension concept, not a standard IFRS one.
_YEARS: dict[str, tuple[float, float, float]] = {
    "2020": (338_446e6, 30_610e6, 5_733e6),
    "2021": (372_216e6, 33_647e6, 8_809e6),
    "2022": (473_479e6, 33_244e6, 11_301e6),
    "2023": (552_764e6, 26_675e6, 13_120e6),
}
#: When each annual report actually became public. A Swedish issuer files in
#: the spring following the year end; the ESEF repository's own `date_added`
#: corroborates two of these (2022-03-22 for FY2021, 2024-04-23 for FY2023).
_FILED = {"2020": "2021-03-10", "2021": "2022-03-22", "2022": "2023-03-15", "2023": "2024-04-23"}
_OBSERVED = {"2020": "2021-06-30", "2021": "2022-06-30", "2022": "2023-06-30", "2023": "2024-06-30"}
_PRICE = {"2020": 200.0, "2021": 205.0, "2022": 190.0, "2023": 265.0}
_SHARES = 2_030_000_000.0
_DEBT = 240_000e6

#: Late enough that every figure is public, early enough that the newest is
#: inside Financial Risk's own 730-day staleness window.
_AT = datetime(2025, 6, 30, tzinfo=timezone.utc)
_COMPANY = "VOLV-B"
_CURRENCY = "SEK"
_INDUSTRY = "Industrials"


def _provenance(reference: str) -> Provenance:
    return Provenance(
        source_kind=SourceKind.EXTERNAL_DATA_SOURCE, source_references=(reference,),
        dependencies=(), update_trigger=UpdateTrigger.NEW_EVIDENCE_RECORDED,
        consumers=(), computed_at=_AT,
    )


def _business_facts(*, with_debt: bool, with_filing_date: bool):
    facts, records = [], set()
    for year, (revenue, operating_cash_flow, capex) in sorted(_YEARS.items()):
        record = f"shadow:{_COMPANY}:{year}"
        records.add(record)
        period_end = f"{year}-12-31"
        published = _FILED[year] if with_filing_date else period_end
        published_at = datetime.fromisoformat(published).replace(tzinfo=timezone.utc)

        def fact(kind: BusinessFactKind, value: float) -> BusinessFact:
            return BusinessFact(
                id=f"{record}:{kind.value}:{period_end}", company=_COMPANY, kind=kind,
                value=value, unit=_CURRENCY, period=period_end, source_record_id=record,
                provenance=_provenance("shadow"), extracted_at=_AT, published_at=published_at,
            )

        facts += [
            fact(BusinessFactKind.REVENUE, revenue),
            fact(BusinessFactKind.FREE_CASH_FLOW, operating_cash_flow - capex),
            fact(BusinessFactKind.CAPITAL_EXPENDITURE, capex),
        ]
        if with_debt:
            facts.append(fact(BusinessFactKind.TOTAL_DEBT, _DEBT))
    return tuple(facts), frozenset(records)


def _valuation_facts() -> tuple[ValuationFact, ...]:
    facts = []
    for year, observed in _OBSERVED.items():
        for kind, value in ((ValuationFactKind.SHARE_PRICE, _PRICE[year]),
                            (ValuationFactKind.SHARES_OUTSTANDING, _SHARES)):
            facts.append(ValuationFact(
                id=f"shadow:{_COMPANY}:{kind.value}:{observed}", company=_COMPANY, kind=kind,
                value=value, unit=_CURRENCY, period=observed,
                source_record_id=f"shadow:market:{observed}", provenance=_provenance("shadow"),
                extracted_at=_AT,
                published_at=datetime.fromisoformat(observed).replace(tzinfo=timezone.utc),
            ))
    return tuple(facts)


def _names(gaps) -> list[str]:
    return [getattr(gap, "value", gap) for gap in gaps or ()]


def _scenario(label: str, *, with_debt: bool, with_filing_date: bool, with_market: bool) -> None:
    facts, records = _business_facts(with_debt=with_debt, with_filing_date=with_filing_date)
    market = _valuation_facts() if with_market else ()

    risk = evaluate_financial_risk(
        facts, statement_record_ids=records, industry=_INDUSTRY, evaluated_at=_AT)
    epochs = fiscal_epochs(
        facts, market, statement_record_ids=records, industry=_INDUSTRY, evaluated_at=_AT)
    valuation = evaluate_fcf_yield_relative(
        facts, market, statement_record_ids=records, industry=_INDUSTRY,
        evaluated_at=_AT, basis=None)

    priors = len(getattr(epochs, "prior_epochs", ()) or ())
    print(f"\n{label}")
    print(f"  Financial Risk v2 : {risk.status.value:20} gaps={_names(risk.missing_evidence)}")
    print(f"  fiscal epochs     : current={getattr(epochs, 'current', None) is not None}  priors={priors}")
    print(f"  FCF-yield v3      : {valuation.status.value:20} gaps={_names(valuation.missing_evidence)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m atlas.dev.fundamentals_provider_shadow",
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.parse_args(argv)

    print("Atlas fundamentals contract -- what each shape of provider data yields.")
    print("In memory only: no database is opened and no Case is composed.")
    _scenario("FULL          every field, real filing dates",
              with_debt=True, with_filing_date=True, with_market=True)
    _scenario("NO DEBT       raw ESEF: no standard total-debt concept",
              with_debt=False, with_filing_date=True, with_market=True)
    _scenario("NO FILING DT  vendor maps filing date onto the period end",
              with_debt=True, with_filing_date=False, with_market=True)
    _scenario("NO MARKET     fundamentals only, no price or share count",
              with_debt=True, with_filing_date=True, with_market=False)
    print("\nEvery run above withholds the valuation on DENOMINATOR_EVIDENCE_MISSING:")
    print("this harness passes no issuer basis, which is what production cannot")
    print("build for an issuer with no SEC CIK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

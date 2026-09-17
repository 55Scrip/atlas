"""Tagged facts in, Atlas fields out -- by concept, never by name.

Three things about ESEF reports make naive reading wrong, and all three were
found in real filings rather than anticipated:

**Instants are dated the following morning.** A balance sheet closing on
2024-12-31 is reported at instant `2025-01-01T00:00:00`. Looking it up under
the date it belongs to returns nothing, which is indistinguishable from an
issuer that never tagged its balance sheet -- an error that reads as a fact.

**One Atlas field has several legitimate IFRS concepts.** Schneider reports
revenue as `RevenueFromContractsWithCustomers`; Volvo uses `Revenue`. Both are
correct IFRS. An ordered candidate list settles it; a substring search over
labels would also "settle" it, and would eventually settle it wrongly.

**Facts carry dimensions.** The same concept appears many times over -- by
segment, by geography, by class. Only the undimensioned fact is the
consolidated figure. Taking the first match returned 533,269 MSEK for Volvo's
2023 revenue, when the consolidated number is 552,764 MSEK.

Where no standard concept is reported, anchoring gives a second route: the
issuer's own extensions that its taxonomy declares to be *narrower than* the
standard concept Atlas wants are, by that declaration, parts of it, and may be
summed. That is how Volvo's capital expenditure is found without a line of
Volvo-specific code. Where neither route works, the field is absent, and
absent is a legitimate answer everywhere in Atlas.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from atlas.business_data_providers.esef.taxonomy import EsefTaxonomy, to_qname

__all__ = ["NormalizedPeriod", "CONCEPT_CANDIDATES", "normalize_filing",
           "duration_facts", "instant_facts"]

#: Atlas field -> the IFRS concepts that legitimately carry it, most specific
#: first. Order is the rule; the first concept actually reported wins, and no
#: further concept is consulted, so two spellings can never be summed.
CONCEPT_CANDIDATES: dict[str, tuple[str, ...]] = {
    "revenue": ("ifrs-full:Revenue", "ifrs-full:RevenueFromContractsWithCustomers"),
    "operating_income": ("ifrs-full:ProfitLossFromOperatingActivities",),
    "net_income": ("ifrs-full:ProfitLoss",),
    "gross_profit": ("ifrs-full:GrossProfit",),
    "operating_cash_flow": ("ifrs-full:CashFlowsFromUsedInOperatingActivities",),
    "capital_expenditure": (
        "ifrs-full:PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
        "ifrs-full:PurchaseOfPropertyPlantAndEquipmentIntangibleAssetsOtherThanGoodwill"
        "InvestmentPropertyAndOtherNoncurrentAssets",
    ),
}
#: Balance-sheet fields, read at an instant rather than over a period.
INSTANT_CANDIDATES: dict[str, tuple[str, ...]] = {
    "cash": ("ifrs-full:CashAndCashEquivalents",),
    "equity": ("ifrs-full:Equity",),
    "total_assets": ("ifrs-full:Assets",),
    "current_assets": ("ifrs-full:CurrentAssets",),
    "current_liabilities": ("ifrs-full:CurrentLiabilities",),
}

_UNDIMENSIONED = {"concept", "entity", "period", "unit", "language"}


def _to_linkbase(qname: str) -> str:
    """`ifrs-full:Revenue` -> `ifrs-full_Revenue`, the form linkbases use."""
    return qname.replace(":", "_", 1) if ":" in qname else qname


def _undimensioned(dimensions: dict) -> bool:
    """Consolidated figures carry no dimension beyond the intrinsic ones."""
    return not set(dimensions) - _UNDIMENSIONED


def duration_facts(document: dict, concept: str) -> dict[str, tuple[float, str | None]]:
    """Consolidated period facts, keyed by the fiscal year they *end* in."""
    out: dict[str, tuple[float, str | None]] = {}
    for fact in document.get("facts", {}).values():
        dimensions = fact.get("dimensions", {})
        if dimensions.get("concept") != concept or not _undimensioned(dimensions):
            continue
        period = dimensions.get("period", "")
        if "/" not in period:
            continue
        try:
            ends = date.fromisoformat(period.split("/")[1][:10]) - timedelta(days=1)
            out[ends.isoformat()] = (float(fact["value"]), dimensions.get("unit"))
        except (TypeError, ValueError):
            continue
    return out


def instant_facts(document: dict, concept: str) -> dict[str, tuple[float, str | None]]:
    """Consolidated balance facts, keyed by the date the balance is *as of*.

    The offset is the whole point: XBRL writes the instant as the following
    midnight, so the closing balance of 2024-12-31 arrives as 2025-01-01.
    """
    out: dict[str, tuple[float, str | None]] = {}
    for fact in document.get("facts", {}).values():
        dimensions = fact.get("dimensions", {})
        if dimensions.get("concept") != concept or not _undimensioned(dimensions):
            continue
        period = dimensions.get("period", "")
        if "/" in period:
            continue
        try:
            as_of = date.fromisoformat(period[:10]) - timedelta(days=1)
            out[as_of.isoformat()] = (float(fact["value"]), dimensions.get("unit"))
        except (TypeError, ValueError):
            continue
    return out


def _currency(unit: str | None) -> str | None:
    """`iso4217:SEK` -> `SEK`. A unit Atlas cannot read is not a currency."""
    if not unit or not unit.startswith("iso4217:"):
        return None
    code = unit.split(":", 1)[1]
    return code if len(code) == 3 and code.isalpha() else None


def _resolve(document, taxonomy, candidates, reader, at):
    """A standard concept if one is reported; otherwise the issuer's own
    extensions that anchoring declares to be parts of it, summed.

    Returns `(value, currency, concepts_used)` or `(None, None, ())`.
    """
    for concept in candidates:
        found = reader(document, concept).get(at)
        if found is not None:
            return found[0], _currency(found[1]), (concept,)

    for concept in candidates:
        parts = taxonomy.extensions_narrower_than(_to_linkbase(concept))
        values, currencies, used = [], set(), []
        for part in sorted(parts):
            found = reader(document, to_qname(part)).get(at)
            if found is None:
                continue
            values.append(found[0])
            currencies.add(_currency(found[1]))
            used.append(part)
        # One currency or none: a field assembled from two currencies is not a
        # field. Partial coverage is still reported -- anchoring proved every
        # part belongs, and Atlas prefers a stated subset to a silent guess.
        if values and len(currencies) == 1:
            return sum(values), currencies.pop(), tuple(used)
    return None, None, ()


@dataclass(frozen=True)
class NormalizedPeriod:
    """One fiscal year of one issuer, as Atlas's evaluators read it."""

    period_end: str
    currency: str | None
    values: dict[str, float] = field(default_factory=dict)
    #: Atlas field -> the concepts it was read from, for the audit trail.
    concepts: dict[str, tuple[str, ...]] = field(default_factory=dict)
    withheld: tuple[str, ...] = ()

    @property
    def free_cash_flow(self) -> float | None:
        """Atlas's own definition, computed here rather than taken from a
        reported total: operating cash flow less capital expenditure."""
        ocf = self.values.get("operating_cash_flow")
        capex = self.values.get("capital_expenditure")
        return None if ocf is None or capex is None else ocf - capex


def normalize_filing(document: dict, taxonomy: EsefTaxonomy, period_end: str) -> NormalizedPeriod:
    """Every Atlas field this filing reports for one fiscal year."""
    values: dict[str, float] = {}
    concepts: dict[str, tuple[str, ...]] = {}
    withheld: list[str] = []
    currencies: set[str] = set()

    for field_name, candidates in CONCEPT_CANDIDATES.items():
        value, currency, used = _resolve(document, taxonomy, candidates, duration_facts, period_end)
        if value is None:
            withheld.append(field_name)
            continue
        values[field_name] = value
        concepts[field_name] = used
        if currency:
            currencies.add(currency)

    for field_name, candidates in INSTANT_CANDIDATES.items():
        value, currency, used = _resolve(document, taxonomy, candidates, instant_facts, period_end)
        if value is None:
            withheld.append(field_name)
            continue
        values[field_name] = value
        concepts[field_name] = used
        if currency:
            currencies.add(currency)

    # The filing's own reporting currency, taken from the facts. A report that
    # states two is not normalized into one here; that is a real anomaly and
    # the caller should see it as an absent currency rather than a chosen one.
    currency = currencies.pop() if len(currencies) == 1 else None
    return NormalizedPeriod(period_end=period_end, currency=currency, values=values,
                            concepts=concepts, withheld=tuple(sorted(withheld)))

"""Issuer common-equity market capitalisation -- descriptive, never
decision-facing (Issuer Common-Equity Market Cap v1).

Atlas's free cash flow is the issuer's, so the market capitalisation it is
comparable with is the issuer's common equity: every outstanding common
class, each at a price that prices *it*. This module composes that value
for one issuer, one economic date and one set of class counts, from
persisted evidence only, and grades it. Nothing that values, recommends or
narrates reads it.

**Counts.** One set, from one filing and one instant: every class-axis
member with outstanding shares (an issuer-level undimensioned count when
the filing gives only that). A member whose count is the sum of two or
more others in the same set is an aggregate (a "B-1 and B-2" or "all
common" member) and is excluded, never added beside its parts. A class
with no shares contributes nothing, whatever its rights.

**Prices.** A class listed on an Atlas security -- proven by the filing's
own cover (`PROVEN_BY_SHARED_DIMENSION`) -- takes that security's own raw
price on the economic date: two listed siblings are never normalised to
one price, and never priced from different dates (the caller supplies one
date's prices, or none). An unlisted class takes a listed class's price
only through rights evidence:

- a structured conversion rate into the issuer's as-converted numeraire
  (the class whose as-converted count is its own count) -- `EQUIVALENT`;
- a filed conversion into a listed class, or a filed economic-parity
  statement naming it with exactly one listed class (or a conversion
  target among several) -- `EQUIVALENT`, ratio one;
- parity with several listed classes and no conversion target -- priced
  anywhere between them, `BOUNDED`;
- per-class EPS alone (accounting, never contractual): the ratio bounded by
  the reported precision of both EPS figures -- `BOUNDED`.

With none of these, the class is missing and the whole value is
`INSUFFICIENT_EVIDENCE` -- never silently omitted.

**Preferred.** Preferred equity is not common. A preferred series the
issuer itself counts in its as-converted share basis participates and is
included, as-converted, at the numeraire's price; any other outstanding
preferred is left out of the denominator and reported as a senior claim on
the numerator (annual dividend where the rate, liquidation preference and
share count are all filed).

**When rights hold.** Evidence applies at the count instant when it holds
there (its own instant or span). A filed statement of a right (parity,
conversion) may also carry forward from the latest filing that stated it
-- never backward -- and the days carried are reported. A structured
instant value (a conversion rate, an as-converted count) holds only at its
own instant, or -- when it comes from the same filing as the counts -- at
that filing's period end.

`ISSUER_EXACT` means every nonzero class was priced by its own listing on
the date; `ISSUER_EQUIVALENT` that some class was priced through filed or
structured equivalence; `ISSUER_BOUNDED` that some contribution is an
interval; the market cap is then `[low, high]`, never a point.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from itertools import combinations

from atlas.alpha.class_rights_evidence.models import ClassRightsObservation, EvidenceStrength, RightKind

__all__ = [
    "ISSUER_EQUITY_METHODOLOGY",
    "DenominatorQuality",
    "ClassCount",
    "ListedPrice",
    "ClassContribution",
    "SeniorEquity",
    "IssuerCommonEquityMarketCap",
    "IssuerFcfYield",
    "compose_issuer_common_equity_market_cap",
    "issuer_fcf_yield",
]

ISSUER_EQUITY_METHODOLOGY = "issuer_common_equity_market_cap_v1"

_STATEMENTS = (EvidenceStrength.CONTRACTUAL, EvidenceStrength.FILING_STATEMENT)
#: A sum of members equal to another member within this relative tolerance
#: (reported counts are rounded) makes that member an aggregate.
_AGGREGATE_TOLERANCE = 1e-6
#: The as-converted numeraire's as-converted count equals its own count
#: within the counts' rounding.
_NUMERAIRE_TOLERANCE = 0.005
#: Generic us-gaap member for "the common stock" as one class.
_GENERIC_COMMON = "us-gaap:CommonStockMember"


class DenominatorQuality(str, Enum):
    ISSUER_EXACT = "issuer_exact"
    ISSUER_EQUIVALENT = "issuer_equivalent"
    ISSUER_BOUNDED = "issuer_bounded"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    NOT_APPLICABLE = "not_applicable"


_RANK = {DenominatorQuality.ISSUER_EXACT: 0, DenominatorQuality.ISSUER_EQUIVALENT: 1,
         DenominatorQuality.ISSUER_BOUNDED: 2, DenominatorQuality.INSUFFICIENT_EVIDENCE: 3}


@dataclass(frozen=True)
class ClassCount:
    """One class's outstanding shares in the chosen set. `member` is `None`
    for an issuer-level (undimensioned) count; `symbol`/`mic` only when the
    filing's own cover proves the class is that listing."""

    member: str | None
    shares: float
    as_of: date
    accession: str
    filing_date: date
    symbol: str | None = None
    mic: str | None = None


@dataclass(frozen=True)
class ListedPrice:
    symbol: str
    on: date
    price: float
    record_id: str


@dataclass(frozen=True)
class ClassContribution:
    member: str | None
    equity_kind: str
    shares: float
    share_as_of: date
    share_accession: str
    symbol: str | None
    treatment: str
    proxy_from_security: str | None
    price: float | None
    price_date: date | None
    ratio_low: float | None
    ratio_high: float | None
    equivalent_shares_low: float | None
    equivalent_shares_high: float | None
    contribution_low: float | None
    contribution_high: float | None
    quality: DenominatorQuality
    evidence: tuple[str, ...]
    evidence_strength: str | None
    carried_forward_days: int | None = None


@dataclass(frozen=True)
class SeniorEquity:
    member: str | None
    shares: float | None
    liquidation_preference: float | None
    dividend_rate: float | None
    annual_dividend: float | None
    convertible_ratio_low: float | None
    convertible_ratio_high: float | None
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class IssuerCommonEquityMarketCap:
    issuer_cik: str
    economic_date: date
    count_instant: date | None
    count_accession: str | None
    currency: str
    quality: DenominatorQuality
    market_cap_low: float | None
    market_cap_high: float | None
    contributions: tuple[ClassContribution, ...]
    excluded: tuple[str, ...]
    senior_equity: tuple[SeniorEquity, ...]
    gaps: tuple[str, ...]
    methodology: str = ISSUER_EQUITY_METHODOLOGY

    @property
    def is_point(self) -> bool:
        return self.market_cap_low is not None and self.market_cap_low == self.market_cap_high


@dataclass(frozen=True)
class IssuerFcfYield:
    """Issuer FCF over issuer common-equity market cap: an interval that
    inverts the market-cap interval (the high yield comes from the LOW cap)."""

    free_cash_flow: float
    yield_low: float | None
    yield_high: float | None
    quality: DenominatorQuality
    methodology: str = ISSUER_EQUITY_METHODOLOGY


def issuer_fcf_yield(free_cash_flow: float, cap: IssuerCommonEquityMarketCap) -> IssuerFcfYield:
    if (cap.quality is DenominatorQuality.INSUFFICIENT_EVIDENCE or not cap.market_cap_low or not cap.market_cap_high
            or cap.market_cap_low <= 0):
        return IssuerFcfYield(free_cash_flow, None, None, cap.quality)
    return IssuerFcfYield(free_cash_flow, free_cash_flow / cap.market_cap_high, free_cash_flow / cap.market_cap_low,
                          cap.quality)


# -- rights applicability ----------------------------------------------------------------------------------


def _statement_applies(o: ClassRightsObservation, instant: date, rights: tuple[ClassRightsObservation, ...]) -> int | None:
    """Days carried forward (0 when it holds at the instant); `None` when it
    does not apply -- in particular never backward, and never past a later
    filing of the same issuer that no longer states the right."""
    if o.holds_on(instant):
        return 0
    if o.effective_to >= instant:
        return None
    later = [r for r in rights if r.accession != o.accession and o.effective_to < r.effective_to <= instant
             and r.kind is RightKind.CLASS_INVENTORY]
    if later:
        return None  # a later filing was read and did not restate it
    return (instant - o.effective_to).days


def _decimals_half_step(decimals: str | None) -> float:
    if decimals in (None, "INF"):
        return 0.0
    return 0.5 * 10 ** (-int(decimals))


def _members_of(o: ClassRightsObservation, common_members: set[str]) -> set[str]:
    return set(common_members) if "*" in o.related_labels else set(o.related_members)


# -- composition -------------------------------------------------------------------------------------------


def _sums_of_others(counts: list[ClassCount]) -> set[str]:
    """Members whose count is the sum of two or more other members' counts."""
    out: set[str] = set()
    by_member = {c.member: c.shares for c in counts if c.member is not None}
    for member, total in by_member.items():
        others = [(m, s) for m, s in by_member.items() if m != member and s > 0]
        for size in range(2, len(others) + 1):
            if any(abs(sum(s for _, s in combo) - total) <= _AGGREGATE_TOLERANCE * max(total, 1) for combo in combinations(others, size)):
                out.add(member)
                break
    return out


_OWN_RIGHTS = (RightKind.CONVERSION_RATE, RightKind.EARNINGS_PER_SHARE, RightKind.AS_CONVERTED_SHARES)


def _aggregates(counts: list[ClassCount], rights: tuple[ClassRightsObservation, ...] = ()) -> set[str]:
    """Aggregate members: a total reported beside its parts. Never a listed
    class. The generic common-stock member is one whenever it sums the
    others; any other member only when it sums two or more others, carries no
    rights evidence of its own, and every one of its parts does -- a class
    Atlas cannot tell from a total is withheld, not dropped."""
    candidates = _sums_of_others(counts)
    with_rights = {o.subject_member for o in rights if o.kind in _OWN_RIGHTS} | {
        m for o in rights if o.kind in (RightKind.ECONOMIC_PARITY, RightKind.CONVERTIBLE_INTO)
        for m in (*o.related_members, o.subject_member, o.target_member) if m}
    out = set()
    by_member = {c.member: c for c in counts if c.member is not None}
    for member in candidates:
        c = by_member[member]
        if c.symbol:
            continue
        if member == _GENERIC_COMMON:
            out.add(member)
            continue
        parts = [m for m in by_member if m != member and by_member[m].shares > 0]
        if member not in with_rights and all(m in with_rights or by_member[m].symbol for m in parts):
            out.add(member)
    return out


def compose_issuer_common_equity_market_cap(
    issuer_cik: str,
    economic_date: date,
    counts: tuple[ClassCount, ...],
    prices: dict[str, ListedPrice],
    rights: tuple[ClassRightsObservation, ...],
    *,
    case_symbol: str,
    currency: str = "USD",
    classes_reported: bool = True,
    class_breakdown: tuple[tuple[str, float, date], ...] = (),
) -> IssuerCommonEquityMarketCap:
    """`prices`: listed symbol -> its raw price ON `economic_date` (a symbol
    without one is simply absent). `rights`: the issuer's rights evidence
    filed by the evaluation date. `classes_reported`: whether the count
    filing tags any class-axis member on a share fact (an issuer-level count
    in a filing that does not is the issuer's one common class).
    `class_breakdown`: (member, shares, as_of) from the latest class-level
    count evidence at or before the instant -- used only beside an
    issuer-level count, to show every other class had no shares."""
    gaps: list[str] = []

    def result(quality, low, high, contributions=(), excluded=(), senior=(), instant=None, accession=None):
        ordered = tuple(sorted(contributions, key=lambda c: (c.equity_kind, c.member or "")))
        return IssuerCommonEquityMarketCap(issuer_cik, economic_date, instant, accession, currency, quality, low, high,
                                           ordered, tuple(sorted(excluded)),
                                           tuple(sorted(senior, key=lambda s: s.member or "")), tuple(sorted(set(gaps))))

    counts = tuple(sorted(counts, key=lambda c: (c.member or "", c.symbol or "")))
    rights = tuple(sorted(rights, key=lambda r: (r.accession, r.observation_key)))
    if not counts:
        gaps.append("no_share_count")
        return result(DenominatorQuality.INSUFFICIENT_EVIDENCE, None, None)
    instants = {c.as_of for c in counts}
    accessions = {c.accession for c in counts}
    if len(instants) != 1 or len(accessions) != 1:
        gaps.append("counts_not_from_one_filing_and_instant")
        return result(DenominatorQuality.INSUFFICIENT_EVIDENCE, None, None)
    instant, accession = next(iter(instants)), next(iter(accessions))
    visible = tuple(rights)  # the caller supplies what was filed by the evaluation date
    senior = _senior_equity(visible, instant)
    if senior:
        gaps.append("senior_equity_claims_on_free_cash_flow")

    # -- inventory of the issuer's common classes at the count instant --
    inventory = [o for o in visible if o.kind is RightKind.CLASS_INVENTORY
                 and _statement_applies(o, instant, visible) is not None]
    common_members = {o.subject_member for o in inventory if o.subject_member and o.equity_kind == "common"}

    issuer_level = [c for c in counts if c.member is None]
    class_level = [c for c in counts if c.member is not None]
    contributions: list[ClassContribution] = []
    excluded: set[str] = set()

    if issuer_level and not class_level:
        count = issuer_level[0]
        price = prices.get(case_symbol)
        if price is None:
            gaps.append(f"no_price:{case_symbol}")
            return result(DenominatorQuality.INSUFFICIENT_EVIDENCE, None, None, instant=instant, accession=accession)
        distinct = common_members - {_GENERIC_COMMON}
        nonzero_breakdown = {m for m, shares, _ in class_breakdown if shares > 0}
        evidence: tuple[str, ...] = ()
        if not classes_reported:
            quality, treatment = DenominatorQuality.ISSUER_EXACT, "no_share_classes_reported"
        elif inventory and len(distinct) <= 1:
            quality, treatment = DenominatorQuality.ISSUER_EXACT, "one_common_class_in_inventory"
            evidence = tuple(sorted(f"{o.accession}:{o.observation_key}" for o in inventory))
        elif class_breakdown and len(nonzero_breakdown) <= 1:
            quality, treatment = DenominatorQuality.ISSUER_EXACT, "every_other_class_zero"
            evidence = tuple(f"{m}={shares:g}@{d.isoformat()}" for m, shares, d in class_breakdown)
            carried = max((instant - d).days for _, _, d in class_breakdown)
            if carried > 0:
                gaps.append(f"class_breakdown_carried_forward:{carried}d")
        elif (group := next((g for g in _parity_groups(visible, instant, common_members)
                             if (distinct or nonzero_breakdown) <= g[0]), None)) is not None:
            quality, treatment, evidence = DenominatorQuality.ISSUER_EQUIVALENT, "one_parity_group", group[1]
            gaps.append("listed_class_unproven_within_parity_group")
            if group[2]:
                gaps.append(f"rights_carried_forward:{group[2]}d")
        else:
            gaps.append("class_structure_unrecorded" if not (inventory or class_breakdown)
                        else "issuer_level_count_spans_classes_of_unknown_economics")
            return result(DenominatorQuality.INSUFFICIENT_EVIDENCE, None, None, instant=instant, accession=accession)
        participating = [m for m in _preferred_members(visible)
                         if _latest_instant(visible, RightKind.AS_CONVERTED_SHARES, m, instant, accession)[0] is not None]
        if participating:
            # Participating preferred beside a count that names no class: no
            # numeraire to convert it into -- withheld, never dropped.
            gaps.append("participating_preferred_beside_issuer_level_count")
            return result(DenominatorQuality.INSUFFICIENT_EVIDENCE, None, None, instant=instant, accession=accession)
        value = count.shares * price.price
        contributions.append(ClassContribution(
            None, "common", count.shares, count.as_of, count.accession, case_symbol, treatment, None, price.price,
            price.on, 1.0, 1.0, count.shares, count.shares, value, value, quality, evidence, None))
        return result(quality, value, value, contributions, excluded, senior, instant, accession)

    aggregates = _aggregates(class_level, visible)
    excluded |= {f"aggregate:{m}" for m in aggregates}
    members = [c for c in class_level if c.member not in aggregates]
    numeraire = _numeraire(visible, instant, members, accession)
    parity = _parity_groups(visible, instant, common_members | {c.member for c in members})
    listed = {c.member: c for c in members if c.symbol and c.shares > 0}
    nonzero = [c for c in members if c.shares > 0]
    if not listed and nonzero:
        # No class is proven to be a listing. The Case's own security is a
        # listing of this issuer's common stock; it prices every class only
        # when there is one class with shares, or one filed parity group
        # spans them all.
        group = next((g for g in parity if {c.member for c in nonzero} <= g[0]), None)
        if len(nonzero) == 1 or group is not None:
            gaps.append("listed_class_unproven" + ("_within_parity_group" if len(nonzero) > 1 else "_only_class_with_shares"))
            if group is not None and group[2]:
                gaps.append(f"rights_carried_forward:{group[2]}d")
            price = prices.get(case_symbol)
            if price is None:
                gaps.append(f"no_price:{case_symbol}")
                return result(DenominatorQuality.INSUFFICIENT_EVIDENCE, None, None, (), excluded, senior, instant, accession)
            quality = DenominatorQuality.ISSUER_EXACT if len(nonzero) == 1 else DenominatorQuality.ISSUER_EQUIVALENT
            evidence = group[1] if group is not None and len(nonzero) > 1 else ()
            for c in members:
                if c.shares <= 0:
                    excluded.add(f"zero_shares:{c.member}")
                    continue
                v = c.shares * price.price
                contributions.append(ClassContribution(c.member, "common", c.shares, c.as_of, c.accession, case_symbol,
                                                       "case_listing_prices_parity_class" if len(nonzero) > 1 else "only_class_with_shares",
                                                       None, price.price, price.on, 1.0, 1.0, c.shares, c.shares, v, v,
                                                       quality, evidence, "filed_statement" if evidence else None,
                                                       group[2] or None if group is not None else None))
            low = sum(c.contribution_low for c in contributions)
            return result(quality, low, low, contributions, excluded, senior, instant, accession)

    for c in members:
        if c.shares <= 0:
            excluded.add(f"zero_shares:{c.member}")
            continue
        if c.symbol:
            price = prices.get(c.symbol)
            if price is None:
                gaps.append(f"no_price:{c.symbol}")
                contributions.append(_missing(c, "listed_without_price"))
                continue
            v = c.shares * price.price
            contributions.append(ClassContribution(c.member, "common", c.shares, c.as_of, c.accession, c.symbol,
                                                   "own_listed_price", None, price.price, price.on, 1.0, 1.0,
                                                   c.shares, c.shares, v, v, DenominatorQuality.ISSUER_EXACT, (), None))
            continue
        contributions.append(_unlisted(c, visible, instant, accession, listed, prices, numeraire, parity, gaps))

    for p in _participating_preferred(visible, instant, accession, numeraire, listed, prices, gaps):
        contributions.append(p)

    quality = max((c.quality for c in contributions), key=lambda q: _RANK[q], default=DenominatorQuality.INSUFFICIENT_EVIDENCE)
    if quality is DenominatorQuality.INSUFFICIENT_EVIDENCE:
        return result(quality, None, None, contributions, excluded, senior, instant, accession)
    low = sum(c.contribution_low for c in contributions)
    high = sum(c.contribution_high for c in contributions)
    return result(quality, low, high, contributions, excluded, senior, instant, accession)


def _missing(c: ClassCount, why: str) -> ClassContribution:
    return ClassContribution(c.member, "common", c.shares, c.as_of, c.accession, c.symbol, why, None, None, None, None,
                             None, None, None, None, None, DenominatorQuality.INSUFFICIENT_EVIDENCE, (), None)


def _numeraire(rights, instant, members: list[ClassCount], accession: str) -> str | None:
    """The as-converted numeraire: the one class whose as-converted count at
    the instant (or at its own filing's period end) equals its own count."""
    by_member = {c.member: c.shares for c in members}
    found = set()
    for o in rights:
        if (o.kind is RightKind.AS_CONVERTED_SHARES and o.subject_member in by_member and o.value
                and _instant_applies(o, instant, accession) is not None and by_member[o.subject_member] > 0
                and abs(o.value / by_member[o.subject_member] - 1) <= _NUMERAIRE_TOLERANCE):
            found.add(o.subject_member)
    return next(iter(found)) if len(found) == 1 else None


def _instant_applies(o: ClassRightsObservation, instant: date, accession: str) -> int | None:
    """A structured instant value holds at its own instant; from the count
    set's own filing it also holds forward to that filing's counts."""
    if o.effective_from == o.effective_to == instant:
        return 0
    if o.accession == accession and o.effective_to <= instant and o.effective_from == o.effective_to:
        latest = max((r.effective_to for r in (o,)), default=o.effective_to)
        return (instant - latest).days
    return None


def _latest_instant(rights, kind, member, instant, accession):
    """The applicable instant observation of `kind` for `member`: at the instant
    itself, else the latest from the count set's own filing."""
    candidates = [(d, o) for o in rights if o.kind is kind and o.subject_member == member and o.value
                  and (d := _instant_applies(o, instant, accession)) is not None]
    if not candidates:
        return None, None
    best = min(d for d, _ in candidates)
    values = {o.value for d, o in candidates if d == best}
    if len(values) != 1:
        return None, None  # disagreeing reports: withheld
    return next(o for d, o in candidates if d == best), best


def _parity_groups(rights, instant, common_members: set[str]):
    """(members, evidence, days carried) for every filed parity statement that
    applies at the instant -- statements carry forward, never backward."""
    groups = []
    for o in rights:
        if o.kind is not RightKind.ECONOMIC_PARITY or o.strength not in _STATEMENTS:
            continue
        days = _statement_applies(o, instant, rights)
        if days is None:
            continue
        group = frozenset(_members_of(o, common_members))
        if len(group) >= 2:
            groups.append((group, (f"{o.accession}:{o.observation_key}",), days))
    # Evidence that holds at the instant before evidence carried to it.
    return sorted(groups, key=lambda g: (g[2], g[1]))


def _unlisted(c, rights, instant, accession, listed, prices, numeraire, parity, gaps) -> ClassContribution:
    base = dict(member=c.member, equity_kind="common", shares=c.shares, share_as_of=c.as_of,
                share_accession=c.accession, symbol=None)
    # 1. structured conversion rate into the as-converted numeraire
    rate, carried = _latest_instant(rights, RightKind.CONVERSION_RATE, c.member, instant, accession)
    if rate is not None and numeraire in listed and prices.get(listed[numeraire].symbol):
        p = prices[listed[numeraire].symbol]
        eq = c.shares * rate.value
        return ClassContribution(**base, treatment="structured_conversion_rate", proxy_from_security=p.symbol,
                                 price=p.price, price_date=p.on, ratio_low=rate.value, ratio_high=rate.value,
                                 equivalent_shares_low=eq, equivalent_shares_high=eq, contribution_low=eq * p.price,
                                 contribution_high=eq * p.price, quality=DenominatorQuality.ISSUER_EQUIVALENT,
                                 evidence=(f"{rate.accession}:{rate.observation_key}",),
                                 evidence_strength=rate.strength.value, carried_forward_days=carried or None)
    # 2. filed conversion into a listed class, or parity with listed classes
    conversions = [(o, d) for o in rights if o.kind is RightKind.CONVERTIBLE_INTO and o.subject_member == c.member
                   and o.target_member in listed and o.strength in _STATEMENTS
                   and (d := _statement_applies(o, instant, rights)) is not None]
    groups = [(g, ev, d) for g, ev, d in parity if c.member in g]
    listed_parity = sorted({m for g, _, _ in groups for m in g if m in listed and prices.get(listed[m].symbol)})
    stated = [(o, d) for o, d in conversions if o.value is not None]
    target = None
    evidence: tuple[str, ...] = ()
    days = None
    ratio = None
    if stated:
        o, days = min(stated, key=lambda x: x[1])
        target, ratio, evidence = o.target_member, o.value, (f"{o.accession}:{o.observation_key}",)
    elif conversions and any(o.target_member in listed_parity for o, _ in conversions):
        o, days = min(((o, d) for o, d in conversions if o.target_member in listed_parity), key=lambda x: x[1])
        g = next((g, ev, d) for g, ev, d in groups if o.target_member in g)
        target, ratio = o.target_member, 1.0
        evidence, days = (f"{o.accession}:{o.observation_key}",) + g[1], max(days, g[2])
    elif len(listed_parity) == 1:
        g = next((g, ev, d) for g, ev, d in groups if listed_parity[0] in g)
        target, ratio, evidence, days = listed_parity[0], 1.0, g[1], g[2]
    if target is not None and prices.get(listed[target].symbol):
        p = prices[listed[target].symbol]
        eq = c.shares * ratio
        if days:
            gaps.append(f"rights_carried_forward:{days}d")
        return ClassContribution(**base, treatment="filed_conversion_or_parity", proxy_from_security=p.symbol,
                                 price=p.price, price_date=p.on, ratio_low=ratio, ratio_high=ratio,
                                 equivalent_shares_low=eq, equivalent_shares_high=eq, contribution_low=eq * p.price,
                                 contribution_high=eq * p.price, quality=DenominatorQuality.ISSUER_EQUIVALENT,
                                 evidence=evidence, evidence_strength="filed_statement", carried_forward_days=days or None)
    if len(listed_parity) > 1:
        ps = [prices[listed[m].symbol] for m in listed_parity]
        low_p, high_p = min(p.price for p in ps), max(p.price for p in ps)
        g = next(g for g in groups if set(listed_parity) & g[0])
        if g[2]:
            gaps.append(f"rights_carried_forward:{g[2]}d")
        return ClassContribution(**base, treatment="parity_between_listed_prices",
                                 proxy_from_security=",".join(p.symbol for p in ps), price=None, price_date=ps[0].on,
                                 ratio_low=1.0, ratio_high=1.0, equivalent_shares_low=c.shares,
                                 equivalent_shares_high=c.shares, contribution_low=c.shares * low_p,
                                 contribution_high=c.shares * high_p, quality=DenominatorQuality.ISSUER_BOUNDED,
                                 evidence=g[1], evidence_strength="filed_statement", carried_forward_days=g[2] or None)
    # 3. accounting corroboration only: per-class EPS over a period containing the instant
    bounds = []
    for m, lc in listed.items():
        p = prices.get(lc.symbol)
        if p is None:
            continue
        for u in rights:
            if u.kind is not RightKind.EARNINGS_PER_SHARE or u.subject_member != c.member or not u.holds_on(instant):
                continue
            for l in rights:
                if (l.kind is RightKind.EARNINGS_PER_SHARE and l.subject_member == m and l.accession == u.accession
                        and (l.effective_from, l.effective_to) == (u.effective_from, u.effective_to) and l.value and l.value > 0):
                    hu, hl = _decimals_half_step(u.decimals), _decimals_half_step(l.decimals)
                    if l.value - hl <= 0:
                        continue
                    lo, hi = (u.value - hu) / (l.value + hl), (u.value + hu) / (l.value - hl)
                    bounds.append((lo * p.price, hi * p.price, lo, hi, p, (f"{u.accession}:{u.observation_key}",
                                                                          f"{l.accession}:{l.observation_key}")))
    if bounds:
        low = min(b[0] for b in bounds)
        high = max(b[1] for b in bounds)
        b = min(bounds, key=lambda b: b[1] - b[0])
        return ClassContribution(**base, treatment="per_class_eps_ratio",
                                 proxy_from_security=",".join(sorted({x[4].symbol for x in bounds})), price=None,
                                 price_date=b[4].on, ratio_low=min(x[2] for x in bounds), ratio_high=max(x[3] for x in bounds),
                                 equivalent_shares_low=None, equivalent_shares_high=None,
                                 contribution_low=c.shares * low, contribution_high=c.shares * high,
                                 quality=DenominatorQuality.ISSUER_BOUNDED, evidence=tuple(e for x in bounds for e in x[5]),
                                 evidence_strength=EvidenceStrength.ACCOUNTING_CORROBORATION.value)
    gaps.append(f"no_rights_evidence:{c.member}")
    return _missing(c, "unlisted_without_rights_evidence")


def _preferred_members(rights) -> set[str]:
    return {o.subject_member for o in rights if o.kind is RightKind.CLASS_INVENTORY and o.equity_kind == "preferred"
            and o.subject_member}


def _participating_preferred(rights, instant, accession, numeraire, listed, prices, gaps) -> list[ClassContribution]:
    """Preferred series the issuer counts in its as-converted basis."""
    out = []
    for member in sorted(_preferred_members(rights)):
        o, carried = _latest_instant(rights, RightKind.AS_CONVERTED_SHARES, member, instant, accession)
        if o is None:
            continue
        if numeraire not in listed or not prices.get(listed[numeraire].symbol):
            gaps.append(f"participating_preferred_unpriced:{member}")
            out.append(ClassContribution(member, "participating_preferred", o.value, o.effective_to, o.accession, None,
                                         "as_converted_without_numeraire_price", None, None, None, None, None, None,
                                         None, None, None, DenominatorQuality.INSUFFICIENT_EVIDENCE, (), None))
            continue
        p = prices[listed[numeraire].symbol]
        half = _decimals_half_step(o.decimals)
        low_eq, high_eq = max(o.value - half, 0.0), o.value + half
        quality = DenominatorQuality.ISSUER_BOUNDED if half else DenominatorQuality.ISSUER_EQUIVALENT
        out.append(ClassContribution(member, "participating_preferred", o.value, o.effective_to, o.accession, None,
                                     "structured_as_converted", p.symbol, p.price, p.on, None, None, low_eq, high_eq,
                                     low_eq * p.price, high_eq * p.price, quality, (f"{o.accession}:{o.observation_key}",),
                                     o.strength.value, carried or None))
    return out


def _senior_equity(rights, instant) -> list[SeniorEquity]:
    """Outstanding preferred the issuer does not count as-converted: a senior
    claim on free cash flow, never part of common equity."""
    as_converted = {o.subject_member for o in rights if o.kind is RightKind.AS_CONVERTED_SHARES}
    outstanding = [o for o in rights if o.kind is RightKind.PREFERRED_SHARES_OUTSTANDING and o.value
                   and o.strength is EvidenceStrength.STRUCTURED_FILING and o.effective_to <= instant]
    if not outstanding:
        return []
    latest = max(o.effective_to for o in outstanding)
    current = [o for o in outstanding if o.effective_to == latest]
    series = [o for o in current if o.subject_member]
    if series:
        # An aggregate preferred member (the sum of its series) is not a series.
        counts = [ClassCount(o.subject_member, o.value, latest, o.accession, o.filing_date) for o in series]
        aggregate = _sums_of_others(counts)
        rows = [o for o in series if o.subject_member not in aggregate]
    else:
        rows = current
    out = []
    for o in rows:
        if o.subject_member in as_converted or (not o.subject_member and as_converted):
            continue
        member = o.subject_member

        def latest_value(kind, *, member=member):
            vals = [r for r in rights if r.kind is kind and r.value is not None and r.effective_from <= instant
                    and r.subject_member == member and r.strength is EvidenceStrength.STRUCTURED_FILING]
            if not vals and member is not None:
                return None
            if not vals:
                vals = [r for r in rights if r.kind is kind and r.value is not None and r.effective_from <= instant
                        and r.strength is EvidenceStrength.STRUCTURED_FILING]
            return max(vals, key=lambda r: (r.effective_to, r.accession)).value if vals else None

        liquidation = latest_value(RightKind.LIQUIDATION_PREFERENCE)
        rate = latest_value(RightKind.PREFERRED_DIVIDEND_RATE)
        ranges = [r for r in rights if r.kind is RightKind.CONVERSION_RATIO_RANGE and r.effective_from <= instant]
        dividend = o.value * liquidation * rate if liquidation and rate else None
        out.append(SeniorEquity(member, o.value, liquidation, rate, dividend,
                                min((r.value_low for r in ranges), default=None),
                                max((r.value_high for r in ranges), default=None),
                                (f"{o.accession}:{o.observation_key}",)))
    return out

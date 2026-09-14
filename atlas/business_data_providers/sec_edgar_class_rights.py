"""Filing-level SEC class economic-rights evidence (Issuer Common-Equity
Market Cap v1).

What each class of an issuer's equity is entitled to, as one 10-K/10-Q
states it: the evidence an issuer-level market capitalisation needs before
an unlisted class may be priced from a listed one. Read from the same XBRL
instances as the share-class adapter (`sec_edgar_share_classes`), with the
same parser plumbing, and never from anything but the filing itself.

**Structured facts first.** Standard us-gaap facts dimensioned by one
member of the class axis: per-class basic EPS (`EarningsPerShareBasic` --
accounting corroboration of relative participation, never a contractual
right), preferred shares outstanding/issued, liquidation preference,
dividend rate, and the standard preferred conversion ratio. Two issuer-
extension shapes are read by their concept vocabulary, narrowly: an
instant `pure` fact whose local name contains `ConversionRate` (a class's
rate into the issuer's as-converted numeraire) and an instant `shares`
fact whose local name contains `AsConverted` (a class's -- or, undimensioned,
the issuer's -- as-converted share count). A zero rate is "not applicable",
not a rate, and is not kept.

**Class inventory.** Every class-axis member that carries a share-unit fact
is recorded with its equity kind (`common` when a common-stock concept
carries it, `preferred` for a preferred-stock concept), so a reader can tell
a single-common-class issuer that tags only preferred series from one with
several common classes.

**Text, narrowly.** The rights themselves are often stated only in the
equity and EPS notes. A handful of sentence patterns over those standard
text blocks -- economic parity "except with respect to voting" / "identical
liquidation and dividend rights", conversion into another class (with its
ratio when stated), votes per share, non-voting, liquidation preference,
seniority, preferred dividend rate, non-convertibility. Each match keeps the
sentence. Class names in text ("Class B") are resolved to class-axis members
only through the filing's own structure: a standard us-gaap `CommonClassX`
member the filing uses, or the member whose own §12(b) cover title names
that class. A statement citing the certificate of incorporation is
`CONTRACTUAL`; any other filed statement of a right is `FILING_STATEMENT`.
This is not a legal-document reader: an unmatched sentence yields nothing.

**Temporal scope.** A fact holds for its own context -- an instant, or a
duration. A text statement holds over the periods the filing presents (its
earliest income-statement duration start to its document period end), the
periods its notes describe. Nothing is extended beyond that here.

Pure: the same instance always gives the same result.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import date
from enum import Enum

from atlas.business_data_providers.sec_edgar_share_classes import CLASS_AXIS, _cover_rows, _entity_wide, _read_instance

__all__ = [
    "RIGHTS_PARSER_VERSION",
    "RIGHTS_TEXT_BLOCKS",
    "RightKind",
    "EvidenceStrength",
    "RightsFact",
    "ClassRightsFiling",
    "parse_class_rights",
    "SecEdgarClassRightsProvider",
]

RIGHTS_PARSER_VERSION = "class_rights_v1"

#: The standard text blocks whose sentences may state class rights.
RIGHTS_TEXT_BLOCKS = frozenset({
    "us-gaap:StockholdersEquityNoteDisclosureTextBlock",
    "us-gaap:EarningsPerShareTextBlock",
    "us-gaap:ScheduleOfStockByClassTextBlock",
    "us-gaap:PreferredStockTextBlock",
})


class RightKind(str, Enum):
    EARNINGS_PER_SHARE = "earnings_per_share"
    CONVERSION_RATE = "conversion_rate"
    CONVERSION_RATIO_RANGE = "conversion_ratio_range"
    AS_CONVERTED_SHARES = "as_converted_shares"
    PREFERRED_SHARES_OUTSTANDING = "preferred_shares_outstanding"
    PREFERRED_SHARES_ISSUED = "preferred_shares_issued"
    LIQUIDATION_PREFERENCE = "liquidation_preference"
    PREFERRED_DIVIDEND_RATE = "preferred_dividend_rate"
    CLASS_INVENTORY = "class_inventory"
    ECONOMIC_PARITY = "economic_parity"
    CONVERTIBLE_INTO = "convertible_into"
    VOTES_PER_SHARE = "votes_per_share"
    NON_VOTING = "non_voting"
    SENIOR_TO_COMMON = "senior_to_common"
    NOT_CONVERTIBLE = "not_convertible"


class EvidenceStrength(str, Enum):
    #: A filed statement of the rights under the governing instrument.
    CONTRACTUAL = "contractual"
    #: The issuer's filed statement of a right, no instrument cited.
    FILING_STATEMENT = "filing_statement"
    #: An XBRL fact.
    STRUCTURED_FILING = "structured_filing"
    #: Per-class EPS: how earnings were allocated, not what a class is owed.
    ACCOUNTING_CORROBORATION = "accounting_corroboration"


@dataclass(frozen=True)
class RightsFact:
    kind: RightKind
    strength: EvidenceStrength
    subject_member: str | None
    subject_label: str | None
    target_member: str | None
    target_label: str | None
    related_members: tuple[str, ...]
    related_labels: tuple[str, ...]
    value: float | None
    value_low: float | None
    value_high: float | None
    unit: str | None
    decimals: str | None
    equity_kind: str | None
    effective_from: date
    effective_to: date
    concept: str
    context_id: str
    excerpt: str | None

    @property
    def key(self) -> str:
        """Stable identity inside one filing."""
        parts = (self.kind.value, self.concept, self.context_id, self.subject_member or self.subject_label or "",
                 self.target_member or self.target_label or "", ",".join(self.related_labels),
                 "" if self.value is None else repr(self.value))
        return "|".join(parts)


@dataclass(frozen=True)
class ClassRightsFiling:
    entity_cik: str | None
    document_type: str | None
    amendment: bool
    document_period_end: date | None
    presented_from: date | None
    facts: tuple[RightsFact, ...]


# -- structured facts -------------------------------------------------------------------------------------

_PREFERRED_CONCEPTS = {
    "us-gaap:PreferredStockSharesOutstanding": (RightKind.PREFERRED_SHARES_OUTSTANDING, "shares"),
    "us-gaap:PreferredStockSharesIssued": (RightKind.PREFERRED_SHARES_ISSUED, "shares"),
    "us-gaap:PreferredStockLiquidationPreference": (RightKind.LIQUIDATION_PREFERENCE, None),
    "us-gaap:PreferredStockDividendRatePercentage": (RightKind.PREFERRED_DIVIDEND_RATE, "pure"),
}
_RANGE_AXIS = "srt:RangeAxis"
#: Share concepts that say which kind of equity a class-axis member is.
_COMMON_SHARE_CONCEPTS = frozenset({
    "us-gaap:CommonStockSharesOutstanding", "us-gaap:CommonStockSharesIssued",
    "dei:EntityCommonStockSharesOutstanding", "us-gaap:WeightedAverageNumberOfSharesOutstandingBasic",
})
_PREFERRED_SHARE_CONCEPTS = frozenset({"us-gaap:PreferredStockSharesOutstanding", "us-gaap:PreferredStockSharesIssued"})


def _num(text: str) -> float | None:
    try:
        return float(text)
    except ValueError:
        return None


def _class_member(ctx) -> tuple[str | None, list[tuple[str, str]]]:
    members = [m for d, m in ctx.explicit if d == CLASS_AXIS]
    others = [(d, m) for d, m in ctx.explicit if d != CLASS_AXIS]
    return (members[0] if len(members) == 1 else None), others


def _span(ctx) -> tuple[date, date] | None:
    if ctx.instant:
        return ctx.instant, ctx.instant
    if ctx.start and ctx.end:
        return ctx.start, ctx.end
    return None


def _structured(facts) -> list[RightsFact]:
    out: list[RightsFact] = []
    inventory: dict[str, set[str]] = {}
    ratio_range: dict[tuple[str, date], dict[str, tuple[float, str, str, str | None]]] = {}
    for concept, ctx, unit, text, decimals in facts:
        member, others = _class_member(ctx)
        span = _span(ctx)
        if span is None or ctx.typed:
            continue
        local = concept.split(":", 1)[-1]
        if unit == "shares" and member is not None and not others:
            kind = ("preferred" if concept in _PREFERRED_SHARE_CONCEPTS else
                    "common" if concept in _COMMON_SHARE_CONCEPTS else None)
            if kind:
                inventory.setdefault(member, set()).add(kind)
        value = _num(text)
        if value is None:
            continue

        def fact(kind, strength, *, subject=member, unit_=unit, low=None, high=None):
            return RightsFact(kind, strength, subject, None, None, None, (), (), value, low, high, unit_, decimals,
                              None, span[0], span[1], concept, ctx.id, None)

        if concept == "us-gaap:EarningsPerShareBasic" and member and not others and ctx.start:
            out.append(fact(RightKind.EARNINGS_PER_SHARE, EvidenceStrength.ACCOUNTING_CORROBORATION, unit_="USD/shares"))
        elif concept in _PREFERRED_CONCEPTS and ctx.instant and not [o for o in others if o[0] != _RANGE_AXIS]:
            kind, unit_ = _PREFERRED_CONCEPTS[concept]
            out.append(fact(kind, EvidenceStrength.STRUCTURED_FILING, unit_=unit_ or unit))
        elif concept == "us-gaap:PreferredStockDividendRatePercentage" and not others:
            out.append(fact(RightKind.PREFERRED_DIVIDEND_RATE, EvidenceStrength.STRUCTURED_FILING, unit_="pure"))
        elif concept == "us-gaap:PreferredStockConvertibleConversionRatio" and ctx.instant:
            bound = next((m.split(":")[-1] for d, m in others if d == _RANGE_AXIS), None)
            subject = member or next((m for d, m in others if d != _RANGE_AXIS), None)
            if subject and bound in ("MinimumMember", "MaximumMember"):
                ratio_range.setdefault((subject, ctx.instant), {})[bound] = (value, concept, ctx.id, decimals)
        elif ("ConversionRate" in local and "Adjust" not in local and unit == "pure" and ctx.instant
              and member and not others and value > 0):
            out.append(fact(RightKind.CONVERSION_RATE, EvidenceStrength.STRUCTURED_FILING))
        elif "AsConverted" in local and unit == "shares" and ctx.instant and not others:
            out.append(fact(RightKind.AS_CONVERTED_SHARES, EvidenceStrength.STRUCTURED_FILING))
    for (subject, on), bounds in ratio_range.items():
        if set(bounds) == {"MinimumMember", "MaximumMember"}:
            low, concept, context_id, decimals = bounds["MinimumMember"]
            high = bounds["MaximumMember"][0]
            out.append(RightsFact(RightKind.CONVERSION_RATIO_RANGE, EvidenceStrength.STRUCTURED_FILING, subject, None,
                                  None, None, (), (), None, low, high, "pure", decimals, "preferred", on, on,
                                  concept, context_id, None))
    return out, inventory


# -- text statements --------------------------------------------------------------------------------------

_CLASS = r"Class\s+[A-Z](?:-\d)?\b"
_CLASS_TOKEN = re.compile(r"\bClass\s+([A-Z](?:-\d)?)\b")
_PATTERNS: list[tuple[RightKind, re.Pattern]] = [
    (RightKind.ECONOMIC_PARITY, re.compile(r"\bidentical\b[^.]*\bexcept with respect to voting\b", re.I)),
    (RightKind.ECONOMIC_PARITY, re.compile(r"\bidentical liquidation and dividend rights\b", re.I)),
]
#: The subject is the LAST class named before the verb, the target the first after it.
_NO_CLASS = r"(?:(?!Class\s+[A-Z])[^.])*?"
_CONVERT_ONE_TO_ONE = re.compile(rf"({_CLASS}){_NO_CLASS}\bconvertible on a one-for-one basis into{_NO_CLASS}({_CLASS})", re.I)
_CONVERT_TO = re.compile(rf"({_CLASS}){_NO_CLASS}\bmay be converted\b{_NO_CLASS}\bto\s+({_CLASS})", re.I)
_VOTES = re.compile(rf"\bEach share of ({_CLASS})[^.]*?\bentitled to (one|two|five|ten|\d+) votes? per share", re.I)
_VOTE_ROW = re.compile(r"(?<![\w$])([A-Z])\s+\$\s?\d[\d.]*\s+[\d,]+\s+(One vote per share|Non-voting)")
_NO_VOTE = re.compile(r"preferred stock\b[^.]*\bwill not have any voting rights", re.I)
_LIQUIDATION = re.compile(r"\bliquidation (?:preference|price) of \$\s?([\d,]+(?:\.\d+)?)", re.I)
_SENIOR = re.compile(r"preferred stockholders takes precedence over[^.]*\bcommon stockholders", re.I)
_NOT_CONVERTIBLE = re.compile(r"\bpreferred stock is not convertible into\b", re.I)
_RATE_ROW = re.compile(r"\bSeries ([A-Z]) [A-Z][a-z]+ \d{1,2}, \d{4} ([\d,]+) ([\d,]+) ([\d.]+) ?%")
_WORDS = {"one": 1, "two": 2, "five": 5, "ten": 10}


def _plain(text: str) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", html.unescape(text)))
    return re.sub(r"\s+", " ", text).strip()


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.;])\s+(?=[A-Z(])", _plain(text)) if s.strip()]


def _label(token: str) -> str:
    return "Class " + _CLASS_TOKEN.match(re.sub(r"\s+", " ", token)).group(1)


def _text_facts(facts, span: tuple[date, date], resolve) -> list[RightsFact]:
    out: list[RightsFact] = []
    seen: set[tuple] = set()
    for concept, ctx, _, text, _ in facts:
        if concept not in RIGHTS_TEXT_BLOCKS:
            continue
        for sentence in _sentences(text):
            found: list[tuple] = []
            strength = (EvidenceStrength.CONTRACTUAL if re.search(r"certificate of incorporation", sentence, re.I)
                        else EvidenceStrength.FILING_STATEMENT)
            for kind, pattern in _PATTERNS:
                if pattern.search(sentence):
                    labels = tuple(sorted({"Class " + t for t in _CLASS_TOKEN.findall(sentence)}))
                    if not labels and re.search(r"each class of (?:our )?common", sentence, re.I):
                        labels = ("*",)
                    if labels:
                        found.append((kind, None, None, labels, None, None, None))
                    break
            for m in _CONVERT_ONE_TO_ONE.finditer(sentence):
                found.append((RightKind.CONVERTIBLE_INTO, _label(m.group(1)), _label(m.group(2)), (), 1.0, None, None))
            if not _CONVERT_ONE_TO_ONE.search(sentence):
                for m in _CONVERT_TO.finditer(sentence):
                    found.append((RightKind.CONVERTIBLE_INTO, _label(m.group(1)), _label(m.group(2)), (), None, None, None))
            for m in _VOTES.finditer(sentence):
                votes = m.group(2).lower()
                found.append((RightKind.VOTES_PER_SHARE, _label(m.group(1)), None, (), float(_WORDS.get(votes, votes)), None, "votes"))
            for m in _VOTE_ROW.finditer(sentence):
                if m.group(2) == "Non-voting":
                    found.append((RightKind.NON_VOTING, f"Class {m.group(1)}", None, (), None, None, None))
                else:
                    found.append((RightKind.VOTES_PER_SHARE, f"Class {m.group(1)}", None, (), 1.0, None, "votes"))
            if _NO_VOTE.search(sentence):
                found.append((RightKind.NON_VOTING, "preferred", None, (), None, None, None))
            for m in _LIQUIDATION.finditer(sentence):
                found.append((RightKind.LIQUIDATION_PREFERENCE, "preferred", None, (), float(m.group(1).replace(",", "")), None, "USD/shares"))
            if _SENIOR.search(sentence):
                found.append((RightKind.SENIOR_TO_COMMON, "preferred", None, (), None, None, None))
            if _NOT_CONVERTIBLE.search(sentence):
                found.append((RightKind.NOT_CONVERTIBLE, "preferred", None, (), None, None, None))
            for m in _RATE_ROW.finditer(sentence):
                label = f"Series {m.group(1)} preferred"
                found.append((RightKind.PREFERRED_SHARES_OUTSTANDING, label, None, (), float(m.group(3).replace(",", "")), None, "shares"))
                found.append((RightKind.PREFERRED_DIVIDEND_RATE, label, None, (), float(m.group(4)) / 100, None, "pure"))
            for kind, subject, target, labels, value, _, unit in found:
                key = (kind, subject, target, labels, value)
                if key in seen:
                    continue
                seen.add(key)
                related = tuple(sorted({m for label in labels for m in resolve(label)}))
                subject_members = resolve(subject) if subject else ()
                target_members = resolve(target) if target else ()
                equity = "preferred" if subject and "preferred" in subject.lower() else ("common" if subject or labels else None)
                out.append(RightsFact(
                    kind, strength,
                    subject_members[0] if len(subject_members) == 1 else None, subject,
                    target_members[0] if len(target_members) == 1 else None, target,
                    related, labels, value, None, None, unit, None, equity, span[0], span[1], concept, ctx.id,
                    sentence[:600],
                ))
    return out


def _resolver(facts, cover_rows, members_in_use: set[str]):
    """Class label -> the class-axis members this filing's own structure names it by."""
    by_title: dict[str, set[str]] = {}
    for row in cover_rows:
        if row.class_member and row.title:
            for token in _CLASS_TOKEN.findall(row.title):
                by_title.setdefault(f"Class {token}", set()).add(row.class_member)

    def resolve(label: str | None) -> tuple[str, ...]:
        if not label or label == "*" or not label.startswith("Class "):
            return ()
        letter = label.split(" ", 1)[1]
        standard = f"us-gaap:CommonClass{letter}Member"
        found = set(by_title.get(label, set()))
        if standard in members_in_use:
            found.add(standard)
        return tuple(sorted(found))

    return resolve


def _precision(decimals: str | None) -> float:
    if decimals is None:
        return float("-inf")
    return float("inf") if decimals == "INF" else float(decimals)


def parse_class_rights(instance_xml: str) -> ClassRightsFiling:
    contexts, facts = _read_instance(instance_xml)
    document_period_end = _entity_wide(facts, "dei:DocumentPeriodEndDate")
    period_end = date.fromisoformat(document_period_end[:10]) if document_period_end else None
    income_starts = [ctx.start for c, ctx, _, _, _ in facts
                     if c in ("us-gaap:NetIncomeLoss", "us-gaap:EarningsPerShareBasic") and ctx.start and ctx.end
                     and not ctx.explicit and not ctx.typed and 80 <= (ctx.end - ctx.start).days <= 380]
    presented_from = min(income_starts) if income_starts else None
    structured, inventory = _structured(facts)
    members_in_use = {m for ctx in contexts for d, m in ctx.explicit if d == CLASS_AXIS}
    resolve = _resolver(facts, _cover_rows(facts), members_in_use)
    text = _text_facts(facts, (presented_from, period_end), resolve) if presented_from and period_end else []
    inventory_facts = [
        RightsFact(RightKind.CLASS_INVENTORY, EvidenceStrength.STRUCTURED_FILING, member, None, None, None, (), (),
                   None, None, None, None, None, "preferred" if kinds == {"preferred"} else "common",
                   presented_from, period_end, "class_axis_share_facts", member, None)
        for member, kinds in sorted(inventory.items()) if presented_from and period_end
    ]
    # One fact per key: the same value reported twice at different precision
    # keeps its most precise report.
    best: dict[str, RightsFact] = {}
    for f in structured + inventory_facts + text:
        kept = best.get(f.key)
        if kept is None or _precision(f.decimals) > _precision(kept.decimals):
            best[f.key] = f
    ordered = sorted(best.values(), key=lambda f: f.key)
    return ClassRightsFiling(
        entity_cik=_entity_wide(facts, "dei:EntityCentralIndexKey") or None,
        document_type=_entity_wide(facts, "dei:DocumentType"),
        amendment=(_entity_wide(facts, "dei:AmendmentFlag") or "").lower() == "true",
        document_period_end=period_end,
        presented_from=presented_from,
        facts=tuple(ordered),
    )


# -- fetching -------------------------------------------------------------------------------------------


class SecEdgarClassRightsProvider:
    """Fetches one filing's XBRL instance at a URL Atlas already recorded
    for it (share evidence stores every instance URL it read): exactly one
    keyless request, with the SEC identity headers."""

    def __init__(self, fetch_text_fn=None, *, timeout: float = 120.0) -> None:
        from atlas.business_data_providers.sec_edgar_identity import SecEdgarIdentity

        self._identity = SecEdgarIdentity()
        self._fetch_text = fetch_text_fn
        self._timeout = timeout

    def fetch_instance_at(self, *, instance_url: str, on_request=None) -> str:
        if not instance_url.startswith("https://www.sec.gov/Archives/edgar/data/"):
            raise ValueError("not an SEC EDGAR archive URL")
        if on_request:
            on_request()
        if self._fetch_text is not None:
            return self._fetch_text(instance_url, self._identity.headers())
        from atlas.business_data_providers.http import fetch_text

        return fetch_text(instance_url, self._identity.headers(), timeout=self._timeout)

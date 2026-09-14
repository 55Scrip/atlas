"""Preferred-series terms as structured evidence (fiscal_epoch_v3).

A filing's stockholders'-equity note often tabulates each preferred series:
issuance date, shares issued and outstanding, the contractual rate, and the
date that rate becomes floating. The class-rights parser keeps those rows as
the excerpts of its rate and share observations; the terms inside them --
when a claim began, how long its fixed rate holds -- are what the
common-attributable free cash flow needs, so they are derived here into
dated observations of their own:

- `SERIES_ISSUED_ON` on the issuance date (the claim's economic onset);
- `PREFERRED_DIVIDEND_RATE` holding from issuance to the day before the rate
  floats (to the statement's own period end when no reset is tabulated);
- `DIVIDEND_RATE_RESETS_ON` on the reset date;
- `PREFERRED_SHARES_ISSUED` / `PREFERRED_SHARES_OUTSTANDING` for the series at
  the statement's period end.

Only a table whose own header names its columns (issuance date, shares
issued, shares outstanding, the rate) is read, and a row only when its series
resolves to exactly one member the issuer's evidence already names (or, with
none named, the standard us-gaap series member). Every derived observation
keeps its source filing, accession, form, filing date, concept, context and
row text, and is recorded under its own version (`SERIES_TERMS_VERSION`) --
the parsed filing itself is never rewritten. Pure and deterministic.
"""
from __future__ import annotations

import re
from dataclasses import replace
from datetime import date, datetime, timedelta

from atlas.alpha.class_rights_evidence.models import (
    ClassRightsFiling,
    ClassRightsObservation,
    EvidenceStrength,
    RightKind,
)

__all__ = ["SERIES_TERMS_VERSION", "derive_series_terms", "record_series_terms", "series_terms_filings"]

SERIES_TERMS_VERSION = "series_terms_v1"

_MONTH = "January|February|March|April|May|June|July|August|September|October|November|December"
_DATE = rf"(?:{_MONTH}) \d{{1,2}}, \d{{4}}"
_ROW = re.compile(
    rf"Series ([A-Z]{{1,2}})\s+({_DATE})\s+([\d,]+)\s+([\d,]+)\s+(\d+(?:\.\d+)?)\s*%((?:\s+{_DATE}){{0,2}})"
)
_DATES = re.compile(_DATE)
_HEADER = ("Issuance Date", "Shares Issued", "Shares Outstanding")
_RATE_HEADERS = ("Contractual Rate", "Dividend Rate")


def _day(text: str) -> date:
    return datetime.strptime(text, "%B %d, %Y").date()


def _layout(header: str) -> dict[str, int] | None:
    """Column order from the table's own header; `None` unless it names the
    columns a row is read by."""
    if not all(h in header for h in _HEADER) or not any(h in header for h in _RATE_HEADERS):
        return None
    if header.index("Shares Issued") > header.index("Shares Outstanding"):
        return None  # only the issued-then-outstanding order is read
    trailing = [(header.find(name), key) for name, key in (("Earliest Redemption", "redemption"),
                                                          ("Becomes Floating", "reset")) if name in header]
    return {key: i for i, (_, key) in enumerate(sorted(trailing))}


def _member(letter: str, known: set[str]) -> str | None:
    matches = {m for m in known if m.split(":")[-1].lower() in (f"series{letter.lower()}preferredstockmember",
                                                                  f"series{letter.lower()}preferredmember")}
    if len(matches) == 1:
        return matches.pop()
    if not matches and not any("series" in m.lower() for m in known):
        return f"us-gaap:Series{letter}PreferredStockMember"
    return None


def derive_series_terms(observations: tuple[ClassRightsObservation, ...], *, recorded_at: datetime
                        ) -> tuple[ClassRightsObservation, ...]:
    """Series-term observations derived from `observations` (one issuer's
    persisted rights evidence), in a deterministic order."""
    known = {o.subject_member for o in observations if o.subject_member}
    by_block: dict[tuple[str, str], list[ClassRightsObservation]] = {}
    for o in observations:
        if o.strength is EvidenceStrength.FILING_STATEMENT and o.excerpt:
            by_block.setdefault((o.accession, o.concept), []).append(o)
    out: dict[tuple[str, str], ClassRightsObservation] = {}
    for (_, _), rows in sorted(by_block.items()):
        layout = next((l for o in rows if (l := _layout(o.excerpt)) is not None), None)
        if layout is None:
            continue
        for source in sorted(rows, key=lambda o: o.observation_key):
            for match in _ROW.finditer(source.excerpt):
                letter, issued_on, issued, outstanding, rate, tail = match.groups()
                member = _member(letter, known)
                if member is None:
                    continue
                onset = _day(issued_on)
                trailing = [_day(d) for d in _DATES.findall(tail)]
                reset = trailing[layout["reset"]] if "reset" in layout and len(trailing) > layout["reset"] else None
                issued_n, outstanding_n = float(issued.replace(",", "")), float(outstanding.replace(",", ""))
                period_end = source.effective_to

                def derived(kind, value, unit, start, end, source=source, member=member):
                    key = f"series_terms:{kind.value}:{member}:{start.isoformat()}:{end.isoformat()}"
                    return key, replace(
                        source, observation_key=key, kind=kind, strength=EvidenceStrength.FILING_STATEMENT,
                        subject_member=member, subject_label=f"Series {letter}", target_member=None, target_label=None,
                        related_members=(), related_labels=(), value=value, value_low=None, value_high=None, unit=unit,
                        decimals=None, equity_kind="preferred", effective_from=start, effective_to=end,
                        parser_version=SERIES_TERMS_VERSION, recorded_at=recorded_at)

                terms = [
                    derived(RightKind.SERIES_ISSUED_ON, issued_n, "shares", onset, onset),
                    derived(RightKind.PREFERRED_SHARES_ISSUED, issued_n, "shares", period_end, period_end),
                    derived(RightKind.PREFERRED_SHARES_OUTSTANDING, outstanding_n, "shares", period_end, period_end),
                ]
                fixed_until = reset - timedelta(days=1) if reset is not None else period_end
                if fixed_until >= onset:
                    terms.append(derived(RightKind.PREFERRED_DIVIDEND_RATE, float(rate) / 100, "pure", onset, fixed_until))
                if reset is not None:
                    terms.append(derived(RightKind.DIVIDEND_RATE_RESETS_ON, None, None, reset, reset))
                for key, observation in terms:
                    out.setdefault((source.accession, key), observation)
    return tuple(o for _, o in sorted(out.items()))


def series_terms_filings(derived: tuple[ClassRightsObservation, ...], sources: dict[str, ClassRightsFiling],
                         *, recorded_at: datetime) -> tuple[tuple[ClassRightsFiling, tuple[ClassRightsObservation, ...]], ...]:
    """Derived observations grouped by source filing, each with the filing
    record it is recorded under (`SERIES_TERMS_VERSION`)."""
    grouped: dict[str, list[ClassRightsObservation]] = {}
    for o in derived:
        grouped.setdefault(o.accession, []).append(o)
    out = []
    for accession, observations in sorted(grouped.items()):
        source = sources.get(accession)
        if source is None:
            continue
        filing = replace(source, observations=len(observations), parser_version=SERIES_TERMS_VERSION,
                         recorded_at=recorded_at)
        out.append((filing, tuple(observations)))
    return tuple(out)


def record_series_terms(repository, issuer_ciks: frozenset[str], *, recorded_at: datetime, dry_run: bool = False
                        ) -> tuple[tuple[str, int, bool], ...]:
    """Derive and record every issuer's series terms through the rights
    repository's own append-only path (one transaction per source filing; a
    filing already recorded under `SERIES_TERMS_VERSION` is left as it is).
    Returns (accession, observations, written)."""
    out = []
    for cik in sorted(issuer_ciks):
        observations = tuple(o for o in repository.observations_for_issuers(frozenset({cik}))[cik]
                             if o.parser_version != SERIES_TERMS_VERSION)
        sources = {f.accession: f for f in repository.filings(frozenset({cik})) if f.parser_version != SERIES_TERMS_VERSION}
        derived = derive_series_terms(observations, recorded_at=recorded_at)
        for filing, rows in series_terms_filings(derived, sources, recorded_at=recorded_at):
            wrote = False if dry_run else repository.record_filing(filing, rows)
            out.append((filing.accession, len(rows), wrote))
    return tuple(out)

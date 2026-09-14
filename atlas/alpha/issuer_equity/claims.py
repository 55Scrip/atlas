"""Senior preferred claims on a fiscal year's free cash flow
(`common_attributable_fcf_v1`), from persisted class economic-rights
evidence only.

Atlas's free cash flow (OCF − capex) is before every dividend: preferred
dividends are financing flows under US GAAP. A preferred series the issuer
does *not* count in its as-converted share basis is senior equity, left out
of the common-equity denominator (`composer`), so its contractual dividend
is a claim on the free cash flow ahead of common equity. A series the issuer
does count as-converted participates as common equity in the denominator and
claims nothing here -- deducting it too would count it twice.

**A series' claim over a fiscal year** is shares × liquidation preference ×
dividend rate × the fraction of the year it accrued, as an interval whose
ends are both evidence-derived:

- *Onset.* A tabulated issuance date (`SERIES_ISSUED_ON`) is the onset.
  Otherwise the onset lies after the latest affirmative zero (the series', or
  the issuer's whole preferred count) and no later than the first evidence of
  the series; with no zero before it, the onset is unknown and a fiscal year
  it may reach is unquantified. Nothing accrues before the onset -- a claim
  that began after a fiscal year never touches that year.
- *Termination.* A dated end (`SERIES_TERMINATED_ON`), or an affirmative zero
  after the series was outstanding, ends it; without either, it is known to
  run to its latest evidence of being outstanding, and possibly to the end of
  the year (the interval widens, never a guess).
- *Partial years.* Days before the first certain day, or after the last, count
  only toward the upper end. The day count is not in the evidence, so the
  fraction is bounded: at least `days / 365` with the issue day excluded, at
  most `days / 360` with it included (never more than a year); a whole year is
  exactly one year's dividend under either convention.
- *Rate.* Every day that may accrue must be covered by a rate that holds on
  it: a tabulated fixed rate from issuance to the day before it floats, or a
  structured rate inside its own dated span. A day past a floating reset with
  no rate evidence makes the year unquantified -- no reference rate is ever
  invented.
- *Shares.* Between the series' later outstanding counts and its issued count
  (a retired share is never reissued without its issued count changing).

A year with any series Atlas cannot bound this way is `UNQUANTIFIED`, and the
year's common-attributable free cash flow is unknown. Pure and deterministic.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum

from atlas.alpha.class_rights_evidence.models import ClassRightsObservation, EvidenceStrength, RightKind
from atlas.alpha.issuer_equity.composer import ClassCount, _sums_of_others

__all__ = ["ClaimStatus", "FiscalYear", "SeniorClaimComposition", "SeriesAccrual", "compose_senior_claims"]

_PREFERRED_KINDS = frozenset({
    RightKind.PREFERRED_DIVIDEND_RATE, RightKind.PREFERRED_SHARES_OUTSTANDING, RightKind.PREFERRED_SHARES_ISSUED,
    RightKind.SERIES_ISSUED_ON, RightKind.DIVIDEND_RATE_RESETS_ON, RightKind.SERIES_TERMINATED_ON,
    RightKind.LIQUIDATION_PREFERENCE, RightKind.CONVERSION_RATIO_RANGE,
})
_EVIDENCED = (EvidenceStrength.STRUCTURED_FILING, EvidenceStrength.FILING_STATEMENT, EvidenceStrength.CONTRACTUAL)


class ClaimStatus(str, Enum):
    #: No senior series may have been outstanding during the year.
    NONE = "none"
    QUANTIFIED = "quantified"
    UNQUANTIFIED = "unquantified"


@dataclass(frozen=True)
class FiscalYear:
    start: date
    end: date


@dataclass(frozen=True)
class SeriesAccrual:
    member: str
    low: float
    high: float
    accrual_days: tuple[int, int]
    shares: tuple[float, float]
    rate: tuple[float, float]
    liquidation: tuple[float, float]
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class SeniorClaimComposition:
    fiscal_year: FiscalYear
    status: ClaimStatus
    low: float = 0.0
    high: float = 0.0
    series: tuple[SeriesAccrual, ...] = ()
    reasons: tuple[str, ...] = ()

    @property
    def evidence(self) -> tuple[str, ...]:
        return tuple(sorted({e for s in self.series for e in s.evidence}))


def _key(o: ClassRightsObservation) -> str:
    return f"{o.accession}:{o.observation_key}"


def _senior_series(rights: tuple[ClassRightsObservation, ...]) -> tuple[set[str], set[str]]:
    """(senior series members, participating members)."""
    participating = {o.subject_member for o in rights if o.kind is RightKind.AS_CONVERTED_SHARES and o.subject_member}
    members = {o.subject_member for o in rights if o.kind in _PREFERRED_KINDS and o.subject_member} - participating
    # An aggregate preferred member (the sum of other members at one date) is not a series.
    by_date: dict[date, list[ClassCount]] = {}
    for o in rights:
        if (o.kind is RightKind.PREFERRED_SHARES_OUTSTANDING and o.subject_member and o.value is not None
                and o.strength is EvidenceStrength.STRUCTURED_FILING):
            by_date.setdefault(o.effective_to, []).append(ClassCount(o.subject_member, o.value, o.effective_to, o.accession, o.filing_date))
    aggregates = set().union(*(_sums_of_others(counts) for counts in by_date.values())) if by_date else set()
    return members - aggregates, participating


def _for(rights, kind, member, *, single: bool, strengths=_EVIDENCED):
    """`member`'s observations of `kind`; the issuer-level ones too when the
    issuer has a single senior series."""
    own = [o for o in rights if o.kind is kind and o.subject_member == member and o.strength in strengths]
    if own or not single:
        return own
    return [o for o in rights if o.kind is kind and o.subject_member is None and o.strength in strengths]


def _fraction(days: int, year_days: int, *, upper: bool) -> float:
    if days >= year_days:
        return 1.0
    if days <= 0:
        return 0.0
    return min(1.0, max(days / 360, days / year_days)) if upper else min(days / 365, days / year_days)


def _accrue(rights, member, year: FiscalYear, totals: dict[date, float], *, single: bool
            ) -> SeriesAccrual | str | None:
    """The series' accrual over the year, `None` when it cannot have been
    outstanding, or the reason it cannot be quantified."""
    issued_on = sorted({o.effective_from for o in rights if o.kind is RightKind.SERIES_ISSUED_ON and o.subject_member == member})
    ended_on = sorted({o.effective_from for o in rights if o.kind is RightKind.SERIES_TERMINATED_ON and o.subject_member == member})
    outstanding = [o for o in _for(rights, RightKind.PREFERRED_SHARES_OUTSTANDING, member, single=single) if o.value is not None]
    own_zeros = sorted(o.effective_to for o in outstanding if o.subject_member == member and o.value == 0)
    positives = sorted(o.effective_to for o in outstanding if o.value > 0)
    first_seen = min([o.effective_from for o in rights if o.subject_member == member and o.kind in _PREFERRED_KINDS]
                     + positives, default=None)
    if len(issued_on) > 1 or len(ended_on) > 1:
        return f"conflicting_series_dates:{member}"
    zeros = sorted(set(own_zeros) | {d for d, v in totals.items() if v == 0})

    # onset: exact, or (after the latest zero before first evidence, no later than first evidence]
    if issued_on:
        onset_early = onset_late = issued_on[0]
        exact_onset = True
    else:
        if first_seen is None:
            return None
        before = [z for z in zeros if z < first_seen]
        onset_early = before[-1] + timedelta(days=1) if before else None
        onset_late = first_seen
        exact_onset = False
    if onset_early is not None and onset_early > year.end:
        return None  # began after the year: never applied backward

    # termination: exact, or (last evidence outstanding, first zero after it]
    last_positive = max((d for d in positives if d >= onset_late), default=None)
    if ended_on:
        end_early = end_late = ended_on[0] - timedelta(days=1)
    else:
        after = [z for z in zeros if z >= onset_late and (last_positive is None or z > last_positive)]
        end_early = last_positive if last_positive is not None else onset_late
        end_late = after[0] - timedelta(days=1) if after else year.end
    if end_late < year.start:
        return None  # ended before the year
    if onset_early is None and year.start < onset_late:
        return f"onset_unknown:{member}"

    start_certain, start_possible = max(year.start, onset_late), max(year.start, onset_early or onset_late)
    end_certain, end_possible = min(year.end, end_early), min(year.end, end_late)
    days_certain = max(0, (end_certain - start_certain).days + 1)
    days_possible = max(0, (end_possible - start_possible).days + 1)
    if days_possible == 0:
        return None
    if exact_onset and year.start < onset_late <= year.end and days_certain:
        days_certain -= 1  # the issue day itself may not accrue
    year_days = (year.end - year.start).days + 1

    # rate on every day that may accrue
    rates = [o for o in _for(rights, RightKind.PREFERRED_DIVIDEND_RATE, member, single=single) if o.value]
    covering = [o for o in rates if o.effective_from <= end_possible and o.effective_to >= start_possible]
    day = start_possible
    for o in sorted(covering, key=lambda o: o.effective_from):
        if o.effective_from <= day:
            day = max(day, o.effective_to + timedelta(days=1))
    if day <= end_possible:
        return f"rate_unproven:{member}"

    issued = [o.value for o in _for(rights, RightKind.PREFERRED_SHARES_ISSUED, member, single=single)
              if o.value and o.effective_to >= onset_late]
    counts = [o.value for o in outstanding if o.value > 0 and o.effective_to >= onset_late]
    if not counts:
        return f"shares_unproven:{member}"
    liquidation = [o.value for o in _for(rights, RightKind.LIQUIDATION_PREFERENCE, member, single=True) if o.value]
    if not liquidation:
        return f"liquidation_unproven:{member}"
    shares = (min(counts), max(counts + issued))
    rate = (min(o.value for o in covering), max(o.value for o in covering))
    liq = (min(liquidation), max(liquidation))
    low = shares[0] * liq[0] * rate[0] * _fraction(days_certain, year_days, upper=False)
    high = shares[1] * liq[1] * rate[1] * _fraction(days_possible, year_days, upper=True)
    evidence = tuple(sorted({_key(o) for o in rights if o.subject_member == member and o.kind in _PREFERRED_KINDS}))
    return SeriesAccrual(member, low, high, (days_certain, days_possible), shares, rate, liq, evidence)


def compose_senior_claims(rights: tuple[ClassRightsObservation, ...], years: tuple[FiscalYear, ...]
                          ) -> dict[FiscalYear, SeniorClaimComposition]:
    """Each fiscal year's senior claim. `rights`: the issuer's evidence filed
    by the evaluation date."""
    rights = tuple(sorted(rights, key=lambda o: (o.accession, o.observation_key, o.parser_version)))
    series, _ = _senior_series(rights)
    totals = {o.effective_to: o.value for o in rights if o.kind is RightKind.PREFERRED_SHARES_OUTSTANDING
              and o.subject_member is None and o.value is not None and o.strength is EvidenceStrength.STRUCTURED_FILING}
    single = len(series) == 1
    out = {}
    for year in sorted(set(years), key=lambda y: (y.end, y.start)):
        accruals, reasons = [], []
        for member in sorted(series):
            result = _accrue(rights, member, year, totals, single=single)
            if isinstance(result, str):
                reasons.append(result)
            elif result is not None:
                accruals.append(result)
        if reasons:
            out[year] = SeniorClaimComposition(year, ClaimStatus.UNQUANTIFIED, series=tuple(accruals), reasons=tuple(reasons))
        elif accruals:
            out[year] = SeniorClaimComposition(year, ClaimStatus.QUANTIFIED, sum(a.low for a in accruals),
                                               sum(a.high for a in accruals), tuple(accruals))
        else:
            out[year] = SeniorClaimComposition(year, ClaimStatus.NONE)
    return out

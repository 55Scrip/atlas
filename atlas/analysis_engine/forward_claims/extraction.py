"""Deterministic forward-claim extraction (Forward-Looking Evidence,
Stage 1).

**No LLM. No embedding model. No semantic interpretation.** Explicit
lexical rules over one `BusinessRecord`'s own transcript text, in the
same spirit as `business_facts.extraction`'s key lookup -- one layer
looser, because a spoken sentence has no metadata key, and no looser
than that.

**False negatives are the accepted cost.** Every rule below is a
conjunction, and any one of them failing rejects the candidate with a
named reason. A missed guidance statement is a gap Atlas can close
later; a fabricated one is a claim it would defend with a real source
reference, which is worse than silence.

The five conditions a sentence must satisfy, all of them:

1. **A company insider said it.** Classified from the transcript
   record's own `title`, never guessed from the content. An analyst
   asking "should we expect $7 billion in 2027?" contains every other
   marker a CFO's answer does.
2. **It looks forward.** An explicit forward verb ("expect", "guidance",
   "outlook"...). "Reaffirming our 2026 guidance range" qualifies;
   "revenue grew" does not.
3. **It is not a historical report.** Past-tense financial reporting is
   rejected even when it also contains a forward word -- ASML's "net
   sales *were* EUR 9.3 billion, which is above the high end of our
   guidance" is a result, not guidance, and the word "guidance" in it is
   describing a comparison.
4. **It names a subject Atlas knows**, with a number and a scale.
5. **It names an explicit future calendar year**, no earlier than the
   source's own fiscal period. "Next year" is rejected rather than
   resolved.

Third-party attribution ("analysts expect", "the street is modelling")
is rejected even from an executive's mouth: quoting someone else's
forecast is not issuing guidance.
"""
from __future__ import annotations

import re
from datetime import datetime

from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.analysis_engine.forward_claims.contracts import (
    ClaimBound,
    ClaimRejectionReason,
    ClaimSubject,
    ClaimType,
    ClaimantRole,
    HorizonKind,
)
from atlas.analysis_engine.forward_claims.models import ForwardClaim

__all__ = ["EXTRACTOR_VERSION", "RejectedCandidate", "classify_claimant", "extract_forward_claims"]

#: Bumped whenever a rule below changes in a way that could alter which
#: claims are produced. Stamped onto every claim so an older claim stays
#: distinguishable from a newer one without re-reading the source.
EXTRACTOR_VERSION = "transcript-guidance-v1"

_SENTENCE = re.compile(r"(?<=[.!?])\s+")

_ANALYST = re.compile(r"\banalyst\b", re.I)
_OPERATOR = re.compile(r"\boperator\b", re.I)
#: `chief ... officer` tolerates multi-word offices -- Salesforce's
#: "Chief Operating & Financial Officer" is a CFO, and a single-word
#: pattern classified its guidance as an outsider's. Safe to widen
#: because the analyst and operator checks run first, so a broader
#: executive pattern can never reclassify an analyst.
_EXECUTIVE = re.compile(
    r"\b(chief\s+[\w\s&,\-]{0,40}?officer|c\.?e\.?o|c\.?f\.?o|c\.?o\.?o|chair(man|woman|person)?|"
    r"president|vice\s+president|treasurer|head\s+of|director\s+of|investor\s+relations|founder)\b",
    re.I,
)

_FORWARD = re.compile(
    r"\b(expect|expects|expecting|anticipate|anticipates|guidance|guiding|outlook|"
    r"forecast|forecasts|reaffirm|reaffirming|raising|raise\s+the|target(?:ing)?)\b",
    re.I,
)

#: Past-tense financial reporting. Checked before anything else
#: succeeds, so a sentence that both reports a result and mentions
#: guidance is treated as the result it is.
_HISTORICAL = re.compile(
    r"\b(were|was|generated|delivered|reported|returned|achieved|came\s+in|"
    r"grew|increased\s+to|declined\s+to|posted|recorded)\b",
    re.I,
)

#: Someone else's forecast, quoted.
_THIRD_PARTY = re.compile(r"\b(analysts?|consensus|the\s+street|investors)\s+(expect|forecast|model)", re.I)

_SUBJECTS: tuple[tuple[ClaimSubject, re.Pattern[str]], ...] = (
    # Adjusted EBITDA before plain revenue: "adjusted EBITDA guidance"
    # also contains no revenue token, but ordering makes the intent
    # explicit rather than incidental.
    (ClaimSubject.ADJUSTED_EBITDA, re.compile(r"\b(adjusted\s+ebitda|ebitda)\b", re.I)),
    (ClaimSubject.FREE_CASH_FLOW, re.compile(r"\b(free\s+cash\s+flow|adjusted\s+free\s+cash\s+flow)\b", re.I)),
    (ClaimSubject.CAPITAL_EXPENDITURE, re.compile(r"\b(capex|capital\s+expenditures?)\b", re.I)),
    (ClaimSubject.REVENUE, re.compile(r"\b(revenue|net\s+sales)\b", re.I)),
)

_SCALES: dict[str, str] = {"billion": "BILLION", "bn": "BILLION", "million": "MILLION", "mm": "MILLION"}
_CURRENCIES: dict[str, str] = {"$": "USD", "€": "EUR", "£": "GBP", "eur": "EUR", "usd": "USD"}

_MONEY = re.compile(
    r"(?P<cur>\$|€|£|\bEUR\b|\bUSD\b)?\s?(?P<num>\d[\d,]*(?:\.\d+)?)\s*(?P<scale>billion|million|bn|mm)\b",
    re.I,
)
_RANGE_JOIN = re.compile(r"^\s*(?:-|–|—|to|and)\s*$", re.I)
_LOWER = re.compile(r"\b(more\s+than|at\s+least|greater\s+than|in\s+excess\s+of|above)\b", re.I)
_UPPER = re.compile(r"\b(up\s+to|no\s+more\s+than|less\s+than|below)\b", re.I)
_APPROX = re.compile(r"\b(approximately|about|around|roughly)\b", re.I)

#: One explicit year and whatever qualifier sits directly in front of
#: it. The qualifier decides the `HorizonKind`; its absence is recorded
#: as unspecified rather than assumed to be either.
_HORIZON = re.compile(
    r"(?P<text>(?P<prefix>fiscal\s+year\s+|fiscal\s+|FY\s?|calendar\s+year\s+|calendar\s+|CY\s?|full\s+year\s+)?"
    r"(?P<year>20[2-9]\d))\b",
    re.I,
)


def _horizon_kind(prefix: str | None) -> HorizonKind:
    word = (prefix or "").strip().lower()
    if word.startswith(("fiscal", "fy")):
        return HorizonKind.FISCAL_YEAR
    if word.startswith(("calendar", "cy")):
        return HorizonKind.CALENDAR_YEAR
    return HorizonKind.UNSPECIFIED_YEAR


class RejectedCandidate:
    """A sentence that looked like guidance and was not stored, with the
    reason. Diagnostic output only -- nothing in Atlas consumes it."""

    __slots__ = ("company", "source_record_id", "text", "reason")

    def __init__(self, *, company: str, source_record_id: str, text: str, reason: ClaimRejectionReason) -> None:
        self.company, self.source_record_id, self.text, self.reason = company, source_record_id, text, reason

    def __repr__(self) -> str:  # pragma: no cover - diagnostic only
        return f"RejectedCandidate({self.company}, {self.reason.value}, {self.text[:60]!r})"


def classify_claimant(title: str | None, speaker: str | None = None) -> ClaimantRole:
    """Deterministic, from the transcript record's own `title`. Analyst
    is checked first: "Analyst, Head of Semiconductor Research" names an
    analyst, and matching the executive pattern first would call it an
    executive."""
    text = (title or "").strip()
    if not text:
        return ClaimantRole.UNKNOWN
    if _ANALYST.search(text):
        return ClaimantRole.ANALYST
    if _OPERATOR.search(text):
        return ClaimantRole.OPERATOR
    if _EXECUTIVE.search(text):
        return ClaimantRole.EXECUTIVE
    return ClaimantRole.UNKNOWN


def _money_matches(sentence: str) -> list[re.Match[str]]:
    return list(_MONEY.finditer(sentence))


def _parse_value(sentence: str, matches: list[re.Match[str]]) -> tuple[ClaimBound, float, float, str, str] | None:
    """Returns `(bound, low, high, unit, value_text)`, or `None` when the
    number cannot be read without guessing."""
    first = matches[0]

    def magnitude(m: re.Match[str]) -> float | None:
        scale = _SCALES.get(m.group("scale").lower())
        if scale is None:
            return None
        try:
            base = float(m.group("num").replace(",", ""))
        except ValueError:
            return None
        return base * (1_000_000_000 if scale == "BILLION" else 1_000_000)

    def unit_of(m: re.Match[str]) -> str:
        cur = (m.group("cur") or "").strip().lower()
        currency = _CURRENCIES.get(cur, "USD" if cur in ("$", "") else cur.upper())
        return f"{currency}_{_SCALES[m.group('scale').lower()]}"

    low = magnitude(first)
    if low is None:
        return None

    # A range only when two amounts are adjacent, separated by nothing
    # but a joining token -- so "$6.8 billion-$7.6 billion" is a range
    # while two amounts in different clauses are not silently paired.
    if len(matches) >= 2:
        between = sentence[first.end() : matches[1].start()]
        if _RANGE_JOIN.match(between):
            high = magnitude(matches[1])
            if high is not None and high >= low and unit_of(first) == unit_of(matches[1]):
                return (
                    ClaimBound.RANGE,
                    low,
                    high,
                    unit_of(first),
                    sentence[first.start() : matches[1].end()].strip(),
                )

    prefix = sentence[max(0, first.start() - 40) : first.start()]
    if _LOWER.search(prefix):
        bound = ClaimBound.LOWER_BOUND
    elif _UPPER.search(prefix):
        bound = ClaimBound.UPPER_BOUND
    else:
        bound = ClaimBound.POINT
    approx = _APPROX.search(prefix)
    start = first.start() - len(approx.group(0)) - 1 if approx and approx.end() >= len(prefix) - 1 else first.start()
    return bound, low, low, unit_of(first), sentence[max(0, start) : first.end()].strip()


def extract_forward_claims(
    record: BusinessRecord, *, extracted_at: datetime
) -> tuple[tuple[ForwardClaim, ...], tuple[RejectedCandidate, ...]]:
    """Reads exactly one transcript `BusinessRecord`. Any other document
    type produces nothing -- this module never opens a filing URL, never
    calls a provider, and never reads a record's `source_reference`."""
    claims: list[ForwardClaim] = []
    rejected: list[RejectedCandidate] = []
    if record.document_type is not SourceKind.TRANSCRIPT:
        return (), ()

    content = record.metadata.get("content")
    if not isinstance(content, str) or not content.strip():
        return (), ()
    title = record.metadata.get("title")
    speaker = record.metadata.get("speaker")
    role = classify_claimant(title if isinstance(title, str) else None)

    source_year = record.period_end.year if record.period_end is not None else None

    for sentence in _SENTENCE.split(content):
        sentence = sentence.strip()
        if not sentence:
            continue
        has_money = _money_matches(sentence)
        if not (_FORWARD.search(sentence) and has_money):
            continue  # not even a candidate; not worth a rejection record

        def reject(reason: ClaimRejectionReason) -> None:
            rejected.append(
                RejectedCandidate(
                    company=record.company, source_record_id=record.id, text=sentence, reason=reason
                )
            )

        if role is not ClaimantRole.EXECUTIVE:
            reject(ClaimRejectionReason.NOT_A_COMPANY_INSIDER)
            continue
        if _THIRD_PARTY.search(sentence):
            reject(ClaimRejectionReason.ATTRIBUTED_TO_A_THIRD_PARTY)
            continue
        if _HISTORICAL.search(sentence):
            reject(ClaimRejectionReason.HISTORICAL_STATEMENT)
            continue

        # One sentence may carry guidance for more than one measure --
        # "2026 Adjusted EBITDA guidance range of $6.8 billion-$7.6
        # billion and our adjusted free cash flow ... range of $3.925
        # billion-$4.725 billion" is two claims, and taking only the
        # first would silently drop the second. Each subject is paired
        # with the amounts that appear after it and before the next
        # subject, so a figure is never attached across a boundary.
        subject_spans = sorted(
            {(m.start(), s) for s, pattern in _SUBJECTS for m in pattern.finditer(sentence)}
        )
        if not subject_spans:
            reject(ClaimRejectionReason.NO_KNOWN_SUBJECT)
            continue

        mentions = [m for m in _HORIZON.finditer(sentence) if source_year is None or int(m.group("year")) >= source_year]
        if not mentions:
            reject(ClaimRejectionReason.NO_EXPLICIT_FUTURE_PERIOD)
            continue
        horizon = str(min(int(m.group("year")) for m in mentions))
        at_horizon = [m for m in mentions if m.group("year") == horizon]
        explicit_kinds = {
            _horizon_kind(m.group("prefix")) for m in at_horizon
        } - {HorizonKind.UNSPECIFIED_YEAR}
        if len(explicit_kinds) > 1:
            # "fiscal 2026 ... calendar 2026" in one sentence: which of the
            # two the figure belongs to cannot be read off the text.
            reject(ClaimRejectionReason.AMBIGUOUS_HORIZON)
            continue
        horizon_kind = explicit_kinds.pop() if explicit_kinds else HorizonKind.UNSPECIFIED_YEAR
        horizon_match = next(
            (m.group("text") for m in at_horizon if _horizon_kind(m.group("prefix")) is horizon_kind),
            at_horizon[0].group("text"),
        )

        produced_any = False
        for position, (offset, subject) in enumerate(subject_spans):
            if len(subject_spans) == 1:
                # Only one measure is named, so every figure in the
                # sentence is about it -- and the subject may follow its
                # own number ("more than $10 billion of revenue").
                owned = has_money
            else:
                # Several measures share the sentence. Each owns only the
                # figures between it and the next, so a number is never
                # attached across a boundary to the wrong measure.
                next_offset = subject_spans[position + 1][0] if position + 1 < len(subject_spans) else len(sentence)
                owned = [m for m in has_money if offset < m.start() < next_offset]
            if not owned:
                continue
            parsed = _parse_value(sentence, owned)
            if parsed is None:
                continue
            bound, low, high, unit, value_text = parsed

            claim_id = f"{record.id}:{subject.value}:{horizon_kind.value}:{horizon}"
            if any(c.id == claim_id for c in claims):
                # One statement, one claim per (subject, horizon): a
                # repeated figure in the same sentence is the same claim.
                continue
            if sentence not in content:
                # Source grounding is the claim's evidence, not a
                # debug aid -- a real check, never an `assert`, which
                # `python -O` would strip and leave claims ungrounded.
                continue
            produced_any = True
            claims.append(
                ForwardClaim(
                    id=claim_id,
                    company=record.company,
                    claim_type=ClaimType.GUIDANCE,
                    subject=subject,
                    bound=bound,
                    value_low=low,
                    value_high=high,
                    unit=unit,
                    value_text=value_text,
                    horizon_period=horizon,
                    horizon_kind=horizon_kind,
                    horizon_text=horizon_match,
                    claimant_role=role,
                    stated_by=speaker if isinstance(speaker, str) else "",
                    stated_by_title=title if isinstance(title, str) else "",
                    source_record_id=record.id,
                    source_kind=record.document_type,
                    source_text=sentence,
                    reported_at=record.published_at,
                    extracted_at=extracted_at,
                    extractor_version=EXTRACTOR_VERSION,
                )
            )
        if not produced_any:
            reject(ClaimRejectionReason.NO_VALUE)
    return tuple(claims), tuple(rejected)

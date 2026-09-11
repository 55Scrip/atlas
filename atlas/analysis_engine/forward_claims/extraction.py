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

**All three operands of a claim come from one clause** (Stage 1.1).
Conditions 4 and 5 are about the sentence; a claim is narrower. Its
subject, its figure and its year must sit in the same local
proposition, or the figure is borrowing an operand it does not own.
Four quarters of real calls showed each way that goes wrong: a
capital-return figure taking "adjusted EBITDA" from a leverage ratio
three clauses later, a "current year" figure taking 2026 from a clause
that gave no number, and a fourth-quarter figure read as a full year.
A clause ends at a comma, semicolon or colon followed by a space, or at
a subordinating conjunction; bare "and" does not end one, because real
guidance coordinates two measures under one verb and one year. The one
operand allowed to come from outside is a year stated as a
sentence-opening frame ("For the full year 2026, we expect CapEx..."),
which governs the clause it introduces. Everything else that cannot be
grounded is rejected -- the same trade as everywhere above.

**Grounded is not enough: the figure must be the company's current
guidance for the measure itself** (Stage 1.2). A figure the company is
citing -- its "previously communicated" number, the baseline in "up
from" -- is skipped, and a measure scoped to part of the company --
"adjusted EBITDA from these assets", "segment revenue", a named segment
in front of the measure -- is rejected. Both were real, both were
locally grounded, and both were hidden only because the genuine claim
in the same statement happened to come first; these rules hold for any
sentence on its own, with no competing claim to hide behind.
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
EXTRACTOR_VERSION = "transcript-guidance-v3"

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


#: Where one local proposition ends. Punctuation counts only when a
#: space follows, so the comma inside "$1,485 million" never splits a
#: figure. The conjunctions always open a subordinate clause -- VST's
#: "all while achieving an attractive net debt to adjusted EBITDA
#: ratio", TSLA's "while we are expecting to be around $9 billion for
#: the current year". Bare "and" is deliberately absent: "our 2026
#: Adjusted EBITDA guidance range of ... and our adjusted free cash flow
#: before growth guidance range of ..." is one proposition about two
#: measures and one year, and "between €44 billion and €60 billion" is
#: one range.
_CLAUSE_BREAK = re.compile(r"[,;:]\s+|\s+(?:while|whereas|although|though|because|but)\s+", re.I)

#: A period shorter than a year, anywhere in the figure's proposition:
#: "fourth quarter of 2025", "Q4 2025", "second half of 2026",
#: "fiscal 2025 third quarter". Its presence means the year that
#: proposition names is not proven to be the figure's full-year period.
_SUB_ANNUAL = re.compile(
    r"\b(?:(?:first|second|third|fourth|1st|2nd|3rd|4th)[\s-]+(?:fiscal[\s-]+)?(?:quarter|half)|"
    r"Q[1-4]|H[12])\b",
    re.I,
)

#: A subject word naming a different, derived measure -- a ratio, a
#: margin, a yield, a per-unit figure -- rather than the measure itself.
#: All from the real corpus: "net debt to adjusted EBITDA ratio", "free
#: cash flow margin", "net revenue yield", "revenue per gigawatt", "free
#: cash flow conversion". Such a mention still separates the figures
#: around it; it never owns one.
_DERIVED_AFTER = re.compile(r"^(?:\s+before\s+growth)?\s+(?:ratios?|multiples?|margins?|yields?|per|conversion)\b", re.I)
_DERIVED_BEFORE = re.compile(r"\b(?:debt|leverage)[\s-]+to[\s-]+$", re.I)


#: Words that qualify a measure without narrowing it below the company:
#: "our fiscal year 2026 revenue", "total net sales", "company revenue".
#: Skipped when reading what stands directly in front of a measure.
_COMPANY_QUALIFIERS = frozenset({
    "our", "its", "the", "total", "company", "company-wide", "consolidated", "overall", "annual",
    "full", "year", "full-year", "fiscal", "calendar", "gaap", "non-gaap", "reported", "fy", "cy",
})
#: A year or a period label. Periods are the sub-annual rule's business,
#: not a narrowing of the measure: "Q3 total net sales" is a quarter,
#: not a segment.
_PERIOD_TOKEN = re.compile(r"(?:FY|CY)?'?(?:20)?\d\d|Q[1-4]|H[12]", re.I)

#: Generic words -- corporate structure, not any company's segment
#: names -- that narrow a measure below the company: "segment revenue",
#: "incremental EBITDA", "acquired assets' EBITDA", "other revenue".
_SUBSET_WORDS = frozenset({
    "segment", "segments", "division", "divisional", "unit", "units", "business-unit", "subsidiary",
    "incremental", "additional", "other", "acquired", "acquisition", "asset", "assets", "asset-level",
    "standalone", "contribution", "contributions", "contribute", "contributes", "contributing", "contributed",
})

#: A measure restricted to where it comes from: "$270 million of
#: adjusted EBITDA from these assets", "EBITDA contribution".
_SUBSET_AFTER = re.compile(
    r"^(?:\s+before\s+growth)?\s+(?:from|attributable\s+to|contributed\s+by|generated\s+by|associated\s+with|"
    r"related\s+to|contributions?)\b",
    re.I,
)

#: Grammar words that are capitalised only because they open a clause.
_CLAUSE_OPENERS = frozenset({
    "in", "for", "on", "at", "by", "with", "of", "and", "or", "but", "as", "to", "from", "over", "a", "an",
    "the", "this", "that", "these", "those", "our", "its", "their", "we", "i", "it", "so", "now", "then",
})
_WORD = re.compile(r"[\w'&-]+")

#: Marks what follows as something the company cites rather than
#: issues: its own earlier number ("our previously communicated 2026
#: adjusted EBITDA midpoint opportunity of $6.8 billion", "our previous
#: estimate of $180 billion to $190 billion"), or a baseline ("up from",
#: "compared with $8 billion in 2025"). "from" is a baseline only when a
#: figure or a year follows it ("from $9 billion", "from 2025 levels");
#: "EBITDA from these assets" is a scope, which the measure-scope rule
#: reads instead. A marker reaches only as far as the next new-value
#: word: "from our prior range to $41.3 billion" and "from $9 billion to
#: $10 billion" issue the figure after "to". Not "initial": "initial
#: 2027 guidance" is usually guidance being issued.
_REFERENCE = re.compile(
    r"\bpreviously\s+(?:communicated|announced|provided|issued|disclosed|shared|stated|discussed|given|guided|"
    r"outlined|reported)\b|"
    r"\b(?:prior|previous|original|earlier|last)\s+(?:(?!to\b)[\w-]+\s+){0,4}?(?:estimate|guidance|outlook|"
    r"range|forecast|target|expectation|view|midpoint|plan)s?\b|"
    r"\bfrom\s+(?=(?:(?:approximately|about|around|roughly)\s+)?(?:[$€£]|\d))|"
    r"\bcompared\s+(?:with|to)\b|\bversus\b|\bvs\b\.?|\brelative\s+to\b",
    re.I,
)
_NEW_VALUE = re.compile(r"\b(?:to|now)\b", re.I)
#: A baseline given as a bare figure -- "from $9 billion to $10 billion"
#: -- where the "to" after it issues the new value rather than closing a
#: range.
_BARE_FROM = re.compile(r"\bfrom\s+(?:(?:approximately|about|around|roughly)\s+)?[$€£]?\s*$", re.I)


def _below_company_level(sentence: str, start: int, end: int, clause_start: int) -> bool:
    """Whether the measure mention at `start:end` is scoped to part of
    the company. Reads only what is attached to the mention itself --
    the word directly in front of it, past company-level qualifiers, and
    what directly follows it -- never the rest of the sentence, so "2026
    adjusted EBITDA of $6.8 billion to $7.6 billion ..., including the
    expected contribution from the assets acquired" stays company-level.

    A capitalised modifier ("Semiconductor Systems revenue", "AI capex",
    "H20 revenue") names a segment, product or programme; acronyms count
    even at the start of a clause, other words there are capitalised
    only by grammar. Lower-case segment names ("retail EBITDA") are not
    recognised: that would need a list of what companies call their
    segments."""
    if _SUBSET_AFTER.match(sentence[end:]):
        return True
    words = _WORD.findall(sentence[clause_start:start])
    for position in range(len(words) - 1, -1, -1):
        word = words[position]
        if word.lower() in _COMPANY_QUALIFIERS or _PERIOD_TOKEN.fullmatch(word):
            continue
        if word.lower() in _SUBSET_WORDS:
            return True
        if word.lower() in _CLAUSE_OPENERS or not any(ch.isupper() for ch in word):
            return False
        acronym = word.isupper() or any(ch.isdigit() for ch in word)
        return acronym or position > 0
    return False


def _cited(text: str) -> bool:
    """Whether the item that ends `text` -- a figure or a year, included
    so a marker can see what follows it -- lies inside a citation: a
    reference marker with no new-value word after it."""
    return any(not _NEW_VALUE.search(text[marker.end() :]) for marker in _REFERENCE.finditer(text))


def _cited_figures(sentence: str, figures: list[re.Match[str]], clause_start: int) -> set[int]:
    """Start offsets of the figures in one clause that the company is
    citing rather than issuing. Each figure is read from what leads into
    it -- back to the previous figure or the clause start, so a measure's
    own words ("our previously communicated 2026 adjusted EBITDA midpoint
    opportunity of") are part of it. A cited figure may be a range: after
    "previous estimate of", "$180 billion to $190 billion" is cited
    whole; after a bare "from", "to" issues the new value instead."""
    cited: set[int] = set()
    group: tuple[bool, int] | None = None  # (bare "from", figures so far)
    previous: re.Match[str] | None = None
    for figure in figures:
        lead_in = sentence[previous.end() if previous else clause_start : figure.start("num")]
        joiner = sentence[previous.end() : figure.start()] if previous else ""
        if (
            group is not None
            and group[1] < 2
            and _RANGE_JOIN.match(joiner)
            and not (group[0] and joiner.strip().lower() == "to")
        ):
            cited.add(figure.start())
            group = (group[0], group[1] + 1)
        elif _cited(sentence[previous.end() if previous else clause_start : figure.end()]):
            cited.add(figure.start())
            group = (bool(_BARE_FROM.search(lead_in)), 1)
        else:
            group = None
        previous = figure
    return cited


def _clause_spans(sentence: str) -> list[tuple[int, int]]:
    spans, start = [], 0
    for boundary in _CLAUSE_BREAK.finditer(sentence):
        spans.append((start, boundary.start()))
        start = boundary.end()
    spans.append((start, len(sentence)))
    return spans


def _within(position: int, spans: list[tuple[int, int]]) -> bool:
    return any(start <= position < end for start, end in spans)


def _names_a_derived_measure(sentence: str, mention: re.Match[str]) -> bool:
    return bool(
        _DERIVED_AFTER.match(sentence[mention.end() :]) or _DERIVED_BEFORE.search(sentence[: mention.start()])
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

        # Every subject mention, in order. One naming a derived measure
        # ("net debt to adjusted EBITDA ratio") stays in the list as a
        # boundary between the figures around it, but is never a
        # claim's subject.
        subject_spans = sorted(
            {
                (m.start(), m.end(), s, _names_a_derived_measure(sentence, m))
                for s, pattern in _SUBJECTS
                for m in pattern.finditer(sentence)
            }
        )
        if all(derived for _, _, _, derived in subject_spans):
            reject(ClaimRejectionReason.NO_KNOWN_SUBJECT)
            continue

        mentions = [m for m in _HORIZON.finditer(sentence) if source_year is None or int(m.group("year")) >= source_year]
        if not mentions:
            reject(ClaimRejectionReason.NO_EXPLICIT_FUTURE_PERIOD)
            continue
        sentence_horizon = str(min(int(m.group("year")) for m in mentions))
        if len(
            {_horizon_kind(m.group("prefix")) for m in mentions if m.group("year") == sentence_horizon}
            - {HorizonKind.UNSPECIFIED_YEAR}
        ) > 1:
            # "fiscal 2026 ... calendar 2026" in one sentence: which of the
            # two the figure belongs to cannot be read off the text. Kept
            # sentence-wide even though each clause is now read on its own
            # -- grounding narrows what Atlas claims, it never widens it.
            reject(ClaimRejectionReason.AMBIGUOUS_HORIZON)
            continue

        clauses = _clause_spans(sentence)

        def clause_of(position: int) -> int | None:
            return next((i for i, (a, b) in enumerate(clauses) if a <= position < b), None)

        # A sentence-opening clause that states a year and nothing else
        # ("For the full year 2026, we expect CapEx to be ...") frames the
        # clause it introduces, and only that one.
        opening = clauses[0]
        year_frame = (
            len(clauses) > 1
            and not any(clause_of(offset) == 0 for offset, _, _, _ in subject_spans)
            and not any(clause_of(m.start("num")) == 0 for m in has_money)
            and any(clause_of(m.start()) == 0 for m in _HORIZON.finditer(sentence))
        )

        failures: list[ClaimRejectionReason] = []
        produced_any = False
        for offset, mention_end, subject, derived in subject_spans:
            if derived:
                continue
            home = clause_of(offset)
            scope = [clauses[home]] + ([opening] if year_frame and home == 1 else [])

            # The year: from the subject's own proposition, never from
            # another clause in the same sentence.
            if any(_within(m.start(), scope) for m in _SUB_ANNUAL.finditer(sentence)):
                failures.append(ClaimRejectionReason.SUB_ANNUAL_HORIZON)
                continue
            # A year inside a citation belongs to the cited figure, not to
            # the one being issued: "2027 revenue of $10 billion compared
            # with $8 billion in 2025" is about 2027.
            local_years = [
                m
                for m in mentions
                if _within(m.start(), scope)
                and not _cited(sentence[next(a for a, b in scope if a <= m.start() < b) : m.end()])
            ]
            if not local_years:
                failures.append(ClaimRejectionReason.UNGROUNDED_OPERANDS)
                continue
            horizon = str(min(int(m.group("year")) for m in local_years))
            at_horizon = [m for m in local_years if m.group("year") == horizon]
            explicit_kinds = {_horizon_kind(m.group("prefix")) for m in at_horizon} - {HorizonKind.UNSPECIFIED_YEAR}
            if len(explicit_kinds) > 1:
                failures.append(ClaimRejectionReason.AMBIGUOUS_HORIZON)
                continue
            horizon_kind = explicit_kinds.pop() if explicit_kinds else HorizonKind.UNSPECIFIED_YEAR
            horizon_match = next(
                (m.group("text") for m in at_horizon if _horizon_kind(m.group("prefix")) is horizon_kind),
                at_horizon[0].group("text"),
            )

            # The measure: the company's, not part of it. After the period
            # checks, so "Q4 2026 revenue" is reported as the quarter it is.
            if _below_company_level(sentence, offset, mention_end, clauses[home][0]):
                failures.append(ClaimRejectionReason.MEASURE_BELOW_COMPANY_LEVEL)
                continue

            # The figure: from the subject's own clause. One sentence may
            # still carry two claims -- "2026 Adjusted EBITDA guidance range
            # of $6.8 billion-$7.6 billion and our adjusted free cash flow
            # ... range of $3.925 billion-$4.725 billion" is two measures in
            # one clause, and each owns only the figures between it and
            # the next, so a number is never attached to the wrong one.
            neighbours = [span for span in subject_spans if clause_of(span[0]) == home]
            clause_money = [m for m in has_money if clause_of(m.start("num")) == home]
            if len(neighbours) == 1:
                # The only measure in its clause owns every figure there,
                # and may follow its own number ("more than $10 billion of
                # revenue").
                owned = clause_money
            elif any(m.start() < neighbours[0][0] for m in clause_money):
                # Several measures, and a figure before the first of them:
                # "$10 billion of revenue and $2 billion of capex" cannot be
                # paired by position without guessing which way it runs.
                failures.append(ClaimRejectionReason.UNGROUNDED_OPERANDS)
                continue
            else:
                here = neighbours.index((offset, mention_end, subject, derived))
                next_offset = neighbours[here + 1][0] if here + 1 < len(neighbours) else clauses[home][1]
                owned = [m for m in clause_money if offset < m.start() < next_offset]
            if not owned:
                failures.append(ClaimRejectionReason.UNGROUNDED_OPERANDS)
                continue
            # The figure being issued, not one being cited -- the company's
            # own earlier number or a baseline is skipped: "raising 2026
            # revenue guidance from $9 billion to $10 billion" issues $10
            # billion. Stage 2.1 can still read a cited earlier figure from
            # the claim's source sentence as its stated prior.
            cited = _cited_figures(sentence, clause_money, clauses[home][0])
            current = [figure for figure in owned if figure.start() not in cited]
            if not current:
                failures.append(ClaimRejectionReason.REFERENCE_VALUE)
                continue
            parsed = _parse_value(sentence, current)
            if parsed is None:
                failures.append(ClaimRejectionReason.NO_VALUE)
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
            # The most specific reason any measure in the sentence failed
            # on; a sentence with nothing readable at all is NO_VALUE, as
            # before.
            for reason in (
                ClaimRejectionReason.SUB_ANNUAL_HORIZON,
                ClaimRejectionReason.AMBIGUOUS_HORIZON,
                ClaimRejectionReason.MEASURE_BELOW_COMPANY_LEVEL,
                ClaimRejectionReason.REFERENCE_VALUE,
                ClaimRejectionReason.UNGROUNDED_OPERANDS,
            ):
                if reason in failures:
                    reject(reason)
                    break
            else:
                reject(ClaimRejectionReason.NO_VALUE)
    return tuple(claims), tuple(rejected)

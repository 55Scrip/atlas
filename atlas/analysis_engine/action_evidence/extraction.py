"""Reading observed actions out of filing narrative, and refusing the rest.

Every rule below was earned by a sentence in the Sprint 23 benchmark,
and each refusal names the thing it refuses. The predicate list is
short because the corpus is: four finite predicates and one ongoing
form covered every hand-verified positive, and a longer list would be
a guess about text nobody has read.

**Order of the checks is the order of the claims.** A sentence first has
to report something (a predicate in active voice with a real object),
then it has to report it *happening* (not negated, not hedged, not a
position "as of" a date), and only then is it read for actor, object,
counterparty, quantity and date.
"""
from __future__ import annotations

import re
from typing import Iterable

from atlas.analysis_engine.action_evidence.contracts import (
    ActionEvidence,
    ActionStatus,
    ActionType,
    ActorKind,
    DateEvidence,
    DateKind,
    Quantity,
    QuantityKind,
    SourceLocator,
    SourceParagraph,
)

__all__ = ["split_sentences", "read_sentence", "extract_actions", "REJECTION_REASONS"]

# ------------------------------------------------------------------ sentences
#: A generic ``(?<=[.!?])\s+`` split cuts "the U.S. Department of Commerce"
#: in two and loses the counterparty. Dotted initialisms and a closed set of
#: corporate and title abbreviations keep their full stops.
_INITIALISM = re.compile(r"\b(?:[A-Za-z]\.){2,}")
_ABBREVIATIONS = ("Inc.", "Corp.", "Co.", "Ltd.", "No.", "Nos.", "vs.", "St.",
                  "Mr.", "Ms.", "Dr.", "Jr.", "Sr.", "approx.")
_BREAK = re.compile(r"(?<=[.!?])\s+(?=[\"“(•◦A-Z0-9])")
_BULLET = re.compile(r"^[\s•◦▪●\-–]+")
_GUARD = "\x00"


def split_sentences(text: str) -> list[str]:
    protected = _INITIALISM.sub(lambda m: m.group(0).replace(".", _GUARD), text)
    for abbr in _ABBREVIATIONS:
        protected = protected.replace(abbr, abbr.replace(".", _GUARD))
    out = []
    for piece in _BREAK.split(protected):
        piece = _BULLET.sub("", piece.replace(_GUARD, ".")).strip()
        if piece:
            out.append(piece)
    return out


# ------------------------------------------------------------------ predicates
#: (source words, family, status). Only what the benchmark earned.
_FINITE = (
    ("entered into", ActionType.CONTRACT_ENTERED, ActionStatus.ENTERED),
    ("acquired", ActionType.ACQUISITION, ActionStatus.COMPLETED),
    ("completed", ActionType.COMPLETION, ActionStatus.COMPLETED),
    ("executed", ActionType.EXECUTION, ActionStatus.COMPLETED),
)
_AUX = r"(?:(?:had|has|have)\s+)?(?:(?:also|subsequently|previously|successfully)\s+)?"

#: Predicates whose surface varies, kept apart from the literal table above so
#: that table's behaviour is provably unchanged. Each pattern absorbs its own
#: preposition where the source uses one, so the object span starts at the
#: thing acted upon rather than at "on" or "of".
#:
#: Share repurchase exists because a StrategyClaim demanded it and the held
#: filings supply it: claims about returning capital had no action vocabulary
#: at all before this. It reads no noun -- "repurchase" and "repurchases"
#: standing alone report nothing, so a board "authorizing $10 billion in
#: repurchases" is a permission and never a purchase.
#:
#: Construction is deliberately absent. The filings do report real
#: groundbreakings, but every one of them is refused by a guard that predates
#: this vocabulary, so a CONSTRUCTION_STARTED type could never be emitted.
_FINITE_PATTERNS = (
    (r"repurchased", ActionType.SHARE_REPURCHASE, ActionStatus.COMPLETED),
)
_FINITE_RX = [(re.compile(r"\b" + _AUX + re.escape(words) + r"\b", re.I), words, t, s)
              for words, t, s in _FINITE]
_FINITE_RX += [(re.compile(r"\b" + _AUX + pattern + r"\b", re.I), None, t, s)
               for pattern, t, s in _FINITE_PATTERNS]
_ONGOING_RX = re.compile(r"\bis now ([a-z]+ing)\b")
#: "plan" after a determiner is a thing, not an intention. The forward guard
#: reads the word as a modal, so "As part of this plan, we broke ground"
#: was refused as though it described something not yet done. Stripped
#: before the hedge checks, exactly as dates are, so the verb "plan to" --
#: which really is intent -- keeps its meaning, and so does the adjective
#: "planned".
_NOUN_PLAN = re.compile(r"\b(?:the|this|that|our|its|their|a|an|such|each|any)\s+plans?\b", re.I)
#: An object that only points forward at a table or list names nothing.
_CATAPHORA = re.compile(r"(?:the\s+)?(?:following|below|table)\b|\bas\s+follows\b", re.I)

# ------------------------------------------------------------------ refusals
REJECTION_REASONS = (
    "no_predicate", "heading", "adjectival_participle", "position_as_of", "negated",
    "forward", "conditional", "no_actor", "not_active_object",
)
_AS_OF = re.compile(r"^As of\b")
_NEGATION = re.compile(r"\b(?:not|never|no longer)\b|n['’]t\b", re.I)
_FORWARD = re.compile(
    r"\b(?:will|would|may|might|could|should|shall|plans?|planned|planning|expects?|expected|"
    r"intends?|intended|anticipates?|anticipated|aims?|seeks?|proposes?|proposed|potential(?:ly)?|"
    r"to be)\b", re.I)
_CONDITIONAL = re.compile(
    r"\b(?:if|unless|subject to|upon (?:closing|completion|receipt|approval)|assuming|pending|once)\b",
    re.I)
#: A predicate followed by one of these is a participle or a passive, not a
#: filer doing something to an object: "net assets acquired in ...",
#: "agreements entered into by ...".
_NOT_AN_OBJECT = re.compile(
    r"^(?:in|on|at|by|of|for|to|from|with|and|or|as|during|under|through|since|"
    r"prior|pursuant|is|was|were|are|be|been)\b|^[,.;:)]|^$", re.I)
#: "We executed well on pricing": an adverb straight after the predicate and
#: then a preposition is the verb used intransitively -- a performance
#: comment, not an act done to an object. "fully autonomous ... services"
#: and "individually immaterial acquisitions" keep theirs.
_INTRANSITIVE_ADVERB = re.compile(
    r"^(?:well|\w+ly)\s+(?:in|on|at|by|of|for|to|from|with|against|across)\b", re.I)
#: "Completed assets are transferred ..." -- a leading participle followed
#: by its own finite verb is an adjective on the subject, not a predicate.
_FINITE_AFTER = re.compile(r"^[^,]*?\b(?:is|are|was|were|has|have|had)\b", re.I)
_DETERMINER_ACTOR = {"the", "a", "an", "this", "that", "these", "those", "such", "each",
                     "any", "all", "its", "their", "our"}

# ------------------------------------------------------------------ actors
_REPORTED = re.compile(r"^(?P<reporter>.+?)\s+announced\s+(?:that\s+)?(?P<inner>we|it|the Company)$")
_CONNECTOR = {"of", "and", "&", "the", "for", "de", "la"}


def _classify_actor(segment: str) -> tuple[str | None, ActorKind | None, str | None]:
    """(actor text, kind, reported_via) or (None, None, None) if no actor."""
    segment = segment.strip().rstrip(",").strip()
    # A short label introducing the clause -- "Singapore: we broke ground" --
    # hides the actor behind it and, where an actor was still found, was
    # pasted onto the front of its name. The label is dropped only when real
    # text follows it, so a bare "Amazon Web Services:" cannot become one.
    if ":" in segment:
        label, _, rest = segment.rpartition(":")
        if rest.strip() and 0 < len(label.split()) <= 4:
            segment = rest.strip()
        elif not rest.strip():
            # a bare heading with the clause hanging off it: the label names
            # the topic, not whoever acted
            return None, None, None
    if "," in segment:
        segment = segment.rsplit(",", 1)[1].strip()
    reported = _REPORTED.match(segment)
    if reported:
        inner = reported.group("inner")
        text = reported.group("reporter").strip() if inner == "it" else inner
        _, kind, _ = _classify_actor(text)
        return (text, kind, "announced") if kind else (None, None, None)
    if segment.lower() == "we":
        return segment, ActorKind.FILER_PRONOUN, None
    if segment in ("the Company", "The Company"):
        return segment, ActorKind.FILER_DEFINED, None
    words = segment.split()
    if words and words[-1].lower() in _DETERMINER_ACTOR:
        return None, None, None
    if 0 < len(words) <= 6 and words[0][:1].isupper() and all(
            w[:1].isupper() or w.lower() in _CONNECTOR for w in words):
        return segment, ActorKind.NAMED, None
    return None, None, None


# ------------------------------------------------------------------ spans
_PREPOSITIONS = {"to", "of", "in", "on", "at", "for", "with", "from", "by", "about", "into"}
_DETERMINERS = {"the", "a", "an", "our", "its", "their", "this", "that", "these", "those",
                "each", "any", "all", "such", "certain", "approximately", "up", "his", "her"}
_COMMA_BREAKS = {"which", "who", "pursuant", "including", "as", "where", "while", "and"}
_PAREN_PREPOSITION = re.compile(r"^(?:with|for|to|including|as|in|on|of|see)\b")


def _span(text: str, stops: tuple[str, ...]) -> str:
    """Leading span of `text`, ending at the first top-level boundary.
    Parentheticals are part of the span unless they open with a
    preposition -- "(PPA)" names the object, "(with options to extend
    ...)" qualifies it."""
    depth, i, n = 0, 0, len(text)
    while i < n:
        ch = text[i]
        if ch == "(":
            if depth == 0 and _PAREN_PREPOSITION.match(text[i + 1:]):
                break
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif depth == 0:
            rest = text[i:]
            if ch in ".;" and (i + 1 == n or text[i + 1] == " ") and not re.match(r"\.\d", rest):
                if not _INITIALISM.match(text[max(0, i - 3):i + 1]) and not any(
                        text[:i + 1].endswith(a) for a in _ABBREVIATIONS):
                    break
            if ch == ",":
                nxt = rest[1:].strip().split(" ", 1)[0].lower().strip(",")
                if nxt.endswith("ing") or nxt in _COMMA_BREAKS:
                    break
            if any(rest.startswith(s) for s in stops) or _SECOND_PREDICATE.match(rest):
                prev = text[:i].rsplit(" ", 1)[-1].lower()
                if not (rest.startswith(" that ") and prev in _PREPOSITIONS):
                    break
            if rest.startswith(" to "):
                nxt = rest[4:].split(" ", 1)[0].lower()
                if nxt not in _DETERMINERS and not nxt[:1].isdigit() and not nxt.startswith("$"):
                    break
        i += 1
    return text[:i].strip().rstrip(",;:").strip()


#: What "entered into" enters when it is a contract. Earned by the corpus:
#: every agreement-like object in the 16 filings uses one of these.
_AGREEMENT = re.compile(
    r"\b(?:agreements?|contracts?|PPAs?|leases?|subleases?|loans?|facilit(?:y|ies)|swaps?|"
    r"orders?|arrangements?|ASAOC|notes?|amendments?|transactions?)\b", re.I)
_OBJECT_STOPS = (" with ", " for ", " pursuant to", " under ", " from ", " that ", " which ",
                 " whereby ", " where ", " who ", " in connection")
#: "a term loan agreement and borrowed $1.68 billion": a second predicate
#: coordinated onto the first is not part of its object.
_SECOND_PREDICATE = re.compile(r"^ (?:and|or) (?:[a-z]+ed|has|have|had|began)\b")
_PARTY_STOPS = (" for ", " pursuant", " under ", " in connection", " whereby", " that ", " which ",
                " who ", " where ", " in which", " related to", " relating to")
#: A counterparty is a party. "with an aggregate $900 million notional amount"
#: and "with notional amounts of approximately $108 million" describe the
#: instrument, and carry the number that gives them away.
_QUANTITY_IN_SPAN = re.compile(r"\$\s?\d|\d\s?%|\d[\d,.]*\s*(?:MW|GW|billion|million)\b")

def _counterparty(rest: str, object_text: str, marker: str) -> str | None:
    """The party of "entered into <object> with <party>" or "acquired
    <object> from <party>": straight after the object (a qualifying
    parenthetical may intervene), or introduced by a comma after an
    interposed phrase. A "with" found anywhere else in the sentence --
    "provided us with the ability", "in connection with our acquisition"
    -- is not a party to anything."""
    tail = rest[len(object_text):] if rest.startswith(object_text) else ""
    t = tail.lstrip()
    while t.startswith("("):
        depth, j = 0, 0
        for j, ch in enumerate(t):
            depth += ch == "("
            depth -= ch == ")"
            if depth == 0:
                break
        t = t[j + 1:].lstrip()
    start = None
    if t.startswith(marker):
        start = len(tail) - len(t) + len(marker)
    else:
        depth = 0
        for i, ch in enumerate(tail):
            depth += ch == "("
            depth -= ch == ")"
            if depth == 0 and tail.startswith(", " + marker, i):
                start = i + 2 + len(marker)
                break
    if start is None:
        return None
    party = _span(tail[start:], _PARTY_STOPS)
    if not party or _QUANTITY_IN_SPAN.search(party):
        return None
    return party


# ------------------------------------------------------------------ quantities
_QUALIFIER_BEFORE = re.compile(
    r"((?:up to\s+)?(?:an additional|a total of|approximately)|up to|more than|over|at least)\s*$", re.I)
_QTY = [
    (re.compile(r"\$\s?(\d[\d,]*(?:\.\d+)?(?:\s*(?:billion|million|thousand))?)"), "$", QuantityKind.MONETARY),
    (re.compile(r"(?<![\d.])(\d[\d,]*(?:\.\d+)?)\s*(MW|GW|MWh|GWh|megawatts?|gigawatts?)\b"), None,
     QuantityKind.CAPACITY),
    (re.compile(r"\b(?P<code>INR|EUR|GBP|JPY|CAD|AUD|CNY|CHF|SGD|KRW|TWD|MXN|BRL)\s?"
                r"(\d[\d,]*(?:\.\d+)?(?:\s*(?:billion|million|thousand))?)"), "<code>", QuantityKind.MONETARY),
    (re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)\s?%"), "%", QuantityKind.PERCENT),
    (re.compile(r"(?<![\d.,$])(\d{1,3})[-\s](year|month)s?\b"), None, QuantityKind.DURATION),
]
_BARE_OF = re.compile(r"(?<![\d.,$])(\d{2,}(?:,\d{3})*)\s+of\s+(?=[a-z])")
_OF_PHRASE = re.compile(r"^\s*of\s+([^,.;()]{1,60}?)(?=\s+(?:from|and\s+\d|in\s+[A-Z])|[,.;(]|$)")


def _quantities(sentence: str) -> tuple[Quantity, ...]:
    out: list[Quantity] = []
    taken: list[tuple[int, int]] = []
    for rx, unit, kind in _QTY:
        for m in rx.finditer(sentence):
            if any(a <= m.start() < b for a, b in taken):
                continue
            taken.append((m.start(), m.end()))
            u = m.group("code") if unit == "<code>" else (unit if unit is not None else m.group(2))
            if unit == "<code>":
                value = m.group(2)
            else:
                value = m.group(1)
            before = _QUALIFIER_BEFORE.search(sentence[:m.start()])
            after = _OF_PHRASE.match(sentence[m.end():])
            # "up to" and "of power at ..." are two separate things the source
            # says about the number; kept apart rather than run together.
            qual = " | ".join(x for x in ((before.group(1) if before else ""),
                                          (f"of {after.group(1).strip()}" if after else "")) if x)
            out.append(Quantity(value_text=value.strip(), unit=u, kind=kind, qualifier=qual))
    for m in _BARE_OF.finditer(sentence):
        value = m.group(1)
        if any(a <= m.start() < b for a, b in taken) or 1900 <= int(value.replace(",", "")) <= 2100:
            continue
        after = _OF_PHRASE.match(sentence[m.end() - len("of ") - 1:])
        out.append(Quantity(value_text=value, unit=None, kind=QuantityKind.UNSPECIFIED,
                            qualifier=f"of {after.group(1).strip()}" if after else ""))
    return tuple(out)


# ------------------------------------------------------------------ dates
_MONTHS = ("january february march april may june july august september october "
           "november december").split()
_M = "(" + "|".join(m.capitalize() for m in _MONTHS) + ")"
_DAY_DATE = re.compile(r"\b(?:On|on)\s+" + _M + r"\s+(\d{1,2}),\s+(\d{4})")
_MONTH_DATE = re.compile(r"\b(?:In|in)\s+" + _M + r"\s+(\d{4})")
_YEAR_DATE = re.compile(r"\b(?:In|in|During|during)\s+(\d{4})\b")
_ANY_DATE = re.compile(_M + r"(?:\s+\d{1,2},)?\s+\d{4}")


#: "During the year ended December 31, 2024" says the act happened somewhere
#: inside that year -- not on the 31st of December. The year is kept, the day
#: and month are not, and the kind says PERIOD so nothing downstream can read
#: it as an instant. Singular only: "the years ended December 31, 2024 and
#: 2025" spans two years and is left unread rather than collapsed into one.
_PERIOD_YEAR = re.compile(
    r"(?:During|In|For)\s+the\s+(?:fiscal\s+)?year\s+ended\s+[A-Z][a-z]+\s+\d{1,2},\s*(\d{4})", re.I)


#: Things filings put in front of a sentence before its date: a footnote
#: marker, a heading closed by a dash, a section label closed by a colon.
#: None of them changes what the date governs.
_LEADING_FURNITURE = re.compile(
    r"^(?:\(\d{1,2}\)\s*|\[\d{1,2}\]\s*|[A-Z][^.\u2014:]{0,60}?\s*[\u2014\u2013-]{1,2}\s+|[A-Z][A-Za-z ]{1,30}:\s+)+")

#: A year after the predicate, inside the predicate's own clause. "We
#: repurchased 3.2 million shares for $300 million in 2024" dates the
#: repurchase; the year is a period, never a day, and never a month.
_TRAILING_YEAR = re.compile(r"\bin\s+((?:19|20)\d{2})\b", re.I)
#: ... unless the year belongs to something else that happened. A programme
#: adopted in 2024 says nothing about when shares were bought back under it.
_YEAR_OF_ANOTHER_ACT = re.compile(
    r"\b(?:adopted|approved|authorized|authorised|established|dated|announced|commenced|"
    r"issued|amended|expiring|maturing|effective|beginning|ending|commencing)\s+$", re.I)


def _date(prefix: str, reported_via: str | None, rest: str = "") -> DateEvidence | None:
    """The sentence-opening date adverbial only. "dated May 15, 2025" inside
    the sentence dates an agreement, not the action, and is left alone."""
    head = re.sub(r"^(?:For example|Additionally|In addition|Also|Further),\s*", "", prefix)
    head = _LEADING_FURNITURE.sub("", head.strip())
    period = _PERIOD_YEAR.match(head.strip())
    if period:
        return DateEvidence(raw_text=period.group(0), kind=DateKind.PERIOD,
                            year=int(period.group(1)), month=None, day=None)
    for rx, precision in ((_DAY_DATE, "day"), (_MONTH_DATE, "month"), (_YEAR_DATE, "year")):
        m = rx.search(head)
        if not m or m.start() > 3 or head[max(0, m.start() - 6):m.start()].strip().endswith("dated"):
            continue
        if precision == "day":
            month, day, year = _MONTHS.index(m.group(1).lower()) + 1, int(m.group(2)), int(m.group(3))
        elif precision == "month":
            month, day, year = _MONTHS.index(m.group(1).lower()) + 1, None, int(m.group(2))
        else:
            month, day, year = None, None, int(m.group(1))
        if reported_via:
            kind = DateKind.ANNOUNCEMENT
        elif precision == "year":
            kind = DateKind.PERIOD
        else:
            kind = DateKind.EVENT
        return DateEvidence(raw_text=m.group(0), kind=kind, year=year, month=month, day=day)
    return _trailing_year(rest)


def _trailing_year(rest: str) -> DateEvidence | None:
    """A year inside the predicate's own clause, at the precision given.

    Only the first one counts: "repurchased ... for $300 million in 2024 and
    8.6 million shares for $425 million in 2023" reports two buybacks, and the
    record describes the first of them.
    """
    clause = re.split(r";|\.\s", rest)[0]
    m = _TRAILING_YEAR.search(clause)
    if not m or _YEAR_OF_ANOTHER_ACT.search(clause[:m.start()]):
        return None
    return DateEvidence(raw_text=m.group(0), kind=DateKind.PERIOD,
                        year=int(m.group(1)), month=None, day=None)


# ------------------------------------------------------------------ reading
def _candidates(sentence: str):
    for rx, words, atype, status in _FINITE_RX:
        for m in rx.finditer(sentence):
            yield m, m.group(0), atype, status
    for m in _ONGOING_RX.finditer(sentence):
        yield m, m.group(0), ActionType.ONGOING_ACTIVITY, ActionStatus.ONGOING


def read_sentence(sentence: str, locator_base: dict | None = None
                  ) -> list[tuple[ActionEvidence | None, str | None]]:
    """Every predicate occurrence in one sentence, each read or refused.

    Returns (record, None) for an observed action and (None, reason) for a
    refusal, so a caller can see *why* a sentence did not count."""
    base = locator_base or dict(issuer="", accession="", section="", paragraph_ordinal=0,
                                sentence_ordinal=0)
    results: list[tuple[ActionEvidence | None, str | None]] = []
    found = False
    for m, predicate, atype, status in _candidates(sentence):
        found = True
        prefix, rest = sentence[:m.start()], sentence[m.end():].lstrip()
        if _AS_OF.match(sentence):
            results.append((None, "position_as_of")); continue
        # Dates are removed before the hedge checks: "dated May 15, 2025"
        # names a month, and a case-blind modal check reads it as "may".
        clause = _ANY_DATE.sub(" ", prefix.rsplit(";", 1)[-1])
        clause = _NOUN_PLAN.sub(" ", clause)
        if _NEGATION.search(clause[-40:]):
            results.append((None, "negated")); continue
        if _FORWARD.search(clause):
            results.append((None, "forward")); continue
        if _CONDITIONAL.search(clause):
            results.append((None, "conditional")); continue
        if _NOT_AN_OBJECT.match(rest) or _INTRANSITIVE_ADVERB.match(rest):
            results.append((None, "not_active_object")); continue
        if m.start() == 0 and predicate[:1].isupper():
            if _FINITE_AFTER.match(rest):
                results.append((None, "adjectival_participle")); continue
            actor_text, kind, via = None, ActorKind.IMPLICIT, None
        elif predicate[:1].isupper():
            # Title-case text away from the sentence start: a heading or a
            # label, never a finite predicate in running prose.
            results.append((None, "heading")); continue
        else:
            actor_text, kind, via = _classify_actor(prefix)
            if kind is None:
                results.append((None, "no_actor")); continue
        object_text = _span(rest, _OBJECT_STOPS)
        if not object_text or _CATAPHORA.match(object_text):
            # "we repurchased the following (in millions):" introduces a
            # table. The act is real but the sentence names nothing, so a
            # record built from it would carry an object that points at
            # words this layer never read.
            results.append((None, "not_active_object")); continue
        if atype is ActionType.CONTRACT_ENTERED and not _AGREEMENT.search(object_text):
            atype = ActionType.ENTRY
        counterparty = None
        marker = {ActionType.CONTRACT_ENTERED: "with ", ActionType.ENTRY: "with ",
                  ActionType.ACQUISITION: "from "}.get(atype)
        if marker:
            counterparty = _counterparty(rest, object_text, marker)
        results.append((ActionEvidence(
            locator=SourceLocator(predicate_offset=m.start(), **base),
            sentence=sentence,
            actor_text=actor_text,
            actor_kind=kind,
            actor_is_filer=True if kind in (ActorKind.FILER_PRONOUN, ActorKind.FILER_DEFINED) else None,
            predicate=predicate,
            action_type=atype,
            status=status,
            object_text=object_text,
            counterparty_text=counterparty,
            quantities=_quantities(sentence),
            date=_date(prefix, via, rest),
            reported_via=via,
        ), None))
    if not found:
        results.append((None, "no_predicate"))
    return results


def extract_actions(paragraphs: Iterable[SourceParagraph]) -> tuple[ActionEvidence, ...]:
    """Every observed action in the given narrative, in source order.

    Deterministic, and keyed by where the words are: the same filing read
    twice yields the same records, and two paragraphs that repeat the same
    sentence are two observations, not one -- merging them would be an
    identity judgement this layer does not make."""
    out: dict[str, ActionEvidence] = {}
    for p in sorted(paragraphs, key=lambda p: (p.issuer, p.accession, p.ordinal)):
        for s_ord, sentence in enumerate(split_sentences(p.text)):
            base = dict(issuer=p.issuer, accession=p.accession, section=p.section,
                        paragraph_ordinal=p.ordinal, sentence_ordinal=s_ord)
            for record, _ in read_sentence(sentence, base):
                if record is not None:
                    out.setdefault(record.key, record)
    return tuple(out.values())

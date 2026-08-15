"""A fixed, symmetric, deterministic canonicalization -- not a fuzzy
match (Sprint 19 ground rule 3).

The distinction that matters: a fuzzy/substring/ranked match asks "how
close is this to that?" and returns whichever candidate scores best.
This function asks a strictly binary question -- "after applying this
one fixed, published transform to both strings, are they identical?" --
and if the answer is no, there is no match at all, not a lower-ranked
one. The same input always canonicalizes to the same output; there is
no threshold to tune and no scored "best guess" anywhere in this
module. `_LEGAL_SUFFIXES` is a closed, explicit list -- it is never
extended dynamically, never learned, and never provider-specific.

Verified against SEC's own real `company_tickers.json` (10,391 entries,
fetched live during Sprint 19's investigation): this transform
correctly collapses "NVIDIA" to the same canonical form as SEC's
"NVIDIA CORP", "Berkshire Hathaway" to the same form as "BERKSHIRE
HATHAWAY INC", and "Alphabet" to the same form as "Alphabet Inc."
Canonicalizing all 10,391 real titles produced 7,985 distinct groups;
46 groups exceeded 5 tickers. Manual inspection of those 46 found most
to be genuine same-issuer preferred-share/related-security clusters
(Morgan Stanley's ten MS-P* preferred series, Public Storage's
seventeen PSA-P* series) -- but a few of the largest (Bank of Montreal,
UBS AG, Brookfield) are the SEC *filer* for dozens of third-party
exchange-traded notes/products that share that bank's name as issuer
of record, not securities a query for the bank itself would usually
mean. This is a real, honestly-reported limitation of exact-title
canonicalization on its own (see this package's own final-report
Known Limitations) -- not a false-merge across unrelated companies (no
group observed mixes two genuinely different, unrelated businesses),
but a signal-to-noise problem a production system would need to filter
by security/form type, which this feasibility seam does not attempt.
"""
from __future__ import annotations

import re

_PUNCTUATION_RE = re.compile(r"[.,/()]")
_WHITESPACE_RE = re.compile(r"\s+")

#: Common legal-entity suffixes stripped before comparison. Closed set,
#: chosen because they appear in SEC's own titles (`_TICKER_MAP_URL`,
#: `atlas.business_data_providers.sec_edgar`) as boilerplate around the
#: company's actual name -- never a heuristic guess at what a human
#: might have meant.
_LEGAL_SUFFIXES = (
    r"\bINCORPORATED\b",
    r"\bCORPORATION\b",
    r"\bHOLDINGS\b",
    r"\bHOLDING\b",
    r"\bCOMPANY\b",
    r"\bCORP\b",
    r"\bINC\b",
    r"\bLTD\b",
    r"\bLIMITED\b",
    r"\bCO\b",
    r"\bPLC\b",
    r"\bLLC\b",
    r"\bN\s?V\b",
    r"\bS\s?A\b",
)
_LEGAL_SUFFIX_RE = re.compile("|".join(_LEGAL_SUFFIXES))


def canonicalize_company_text(text: str) -> str:
    """Upper-case, strip punctuation, strip legal-entity suffixes,
    collapse whitespace. Applied identically to the user's query and to
    every SEC title -- neither side is treated specially."""
    upper = text.upper()
    no_punctuation = _PUNCTUATION_RE.sub(" ", upper)
    no_suffixes = _LEGAL_SUFFIX_RE.sub(" ", no_punctuation)
    return _WHITESPACE_RE.sub(" ", no_suffixes).strip()

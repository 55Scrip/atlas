"""Progressively weaker company-name matching strategies, tried in
order before Atlas ever asks the user (Zero-Effort Import Polish,
Sprint 11 Phase 1). Every strategy here is deterministic and
explainable -- no scored "best guess," no learned/dynamic suffix list.

`name_variants` complements, not duplicates,
`atlas.alpha.security_discovery.canonicalize.canonicalize_company_text`
-- that function already strips a closed set of US-centric suffixes
(INC/CORP/LTD/PLC/LLC/NV/SA) as part of matching against SEC's own
titles. This module adds two things that package doesn't need: ADR/ADS
suffix stripping (SEC titles are never themselves "X ADR"), and common
non-US legal-entity suffixes (SE, AG, ASA, AB, A/S, Oyj, GmbH, SpA)
that appear in real broker exports but not in SEC's own filer titles.
"""
from __future__ import annotations

import re

_ADR_SUFFIX_PATTERN = re.compile(
    r"\s*\b(ADR|ADS|AMERICAN\s+DEPOSITARY\s+RECEIPTS?|AMERICAN\s+DEPOSITARY\s+SHARES?)\b\.?\s*$",
    re.IGNORECASE,
)

_LEGAL_SUFFIX_PATTERN = re.compile(
    r"\s*\b(SE|AG|ASA|A/S|OYJ|GMBH|SPA|S\.?P\.?A\.?|AB|GROUP|HOLDING|HOLDINGS)\b\.?\s*$",
    re.IGNORECASE,
)


def _strip(pattern: re.Pattern[str], name: str) -> str | None:
    stripped = pattern.sub("", name).strip()
    return stripped if stripped and stripped != name.strip() else None


def name_variants(name: str) -> tuple[str, ...]:
    """Every distinct variant worth trying, most-specific first: the
    name as given, then with an ADR suffix removed, then with a legal-
    entity suffix removed, then both removed together."""
    variants = [name]
    without_adr = _strip(_ADR_SUFFIX_PATTERN, name)
    if without_adr:
        variants.append(without_adr)
    without_legal = _strip(_LEGAL_SUFFIX_PATTERN, name)
    if without_legal:
        variants.append(without_legal)
    if without_adr:
        without_both = _strip(_LEGAL_SUFFIX_PATTERN, without_adr)
        if without_both:
            variants.append(without_both)

    deduped: list[str] = []
    for candidate in variants:
        if candidate not in deduped:
            deduped.append(candidate)
    return tuple(deduped)


_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")
_MIN_ABBREVIATED_TOKEN_LENGTH = 3


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(match.group(0).lower() for match in _TOKEN_PATTERN.finditer(text))


def token_prefix_match(query: str, candidate: str) -> bool:
    """True when every token of `query` is a case-insensitive prefix of
    the corresponding token of `candidate`, same count and order --
    catches real abbreviation patterns real broker exports use
    ("Semicond" for "Semiconductor", "Mfg" for "Manufacturing", "Intl"
    for "International") without any edit-distance/fuzzy scoring that
    could match an unrelated name. A single short token is too weak a
    signal to trust automatically: at least two tokens are required,
    each at least three characters, matching the exact token count of
    the candidate."""
    query_tokens = _tokens(query)
    candidate_tokens = _tokens(candidate)
    if len(query_tokens) < 2 or len(query_tokens) != len(candidate_tokens):
        return False
    return all(
        len(q) >= _MIN_ABBREVIATED_TOKEN_LENGTH and c.startswith(q)
        for q, c in zip(query_tokens, candidate_tokens)
    )

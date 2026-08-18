"""Normalization tests -- Sprint N Phase 5 steps 1-2."""
from __future__ import annotations

from atlas.alpha.canonical_security_resolution.normalization import normalize_company_text, normalize_ticker


def test_normalize_company_text_none_is_empty_string() -> None:
    assert normalize_company_text(None) == ""


def test_normalize_company_text_reuses_security_discovery_canonicalizer() -> None:
    """`canonicalize_company_text` normalizes case/punctuation/common
    legal suffixes -- it does not collapse a full legal name down to a
    brand abbreviation (that would be fuzzy matching, which it
    explicitly is not; see that module's own docstring). "Apple Inc."
    and "APPLE INC" differ only in case and the "Inc."/"INC" suffix
    form, which the transform does normalize away."""
    assert normalize_company_text("Apple Inc.") == normalize_company_text("APPLE INC")


def test_normalize_ticker_strips_and_uppercases() -> None:
    assert normalize_ticker("  aapl ") == "AAPL"


def test_normalize_ticker_is_deterministic() -> None:
    assert normalize_ticker("brk.b") == normalize_ticker("BRK.B")

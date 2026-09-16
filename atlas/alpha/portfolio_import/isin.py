"""ISIN: the one identifier a brokerage export carries that names a
security rather than describing it.

A ticker is what a venue calls something. `SU` is Suncor Energy on the NYSE
and `SU.PA` is Schneider Electric in Paris; `VOLV-B` means nothing outside
Stockholm. An ISIN is unambiguous worldwide, and it identifies a *security* --
Volvo A and Volvo B have different ISINs, as do an ordinary share and its ADR.
That distinction is the point, not a limitation: sharing issuer fundamentals
between two securities is a decision to make deliberately after proving they
share an issuer, never a side effect of treating them as the same thing.

Validation is the ISO 6166 check digit, and it matters here for one specific
reason: a malformed ISIN must never resolve anything. Silently accepting
`SE000000000` and matching it to a security would be the same class of error
as matching on a ticker, only harder to notice. An invalid ISIN is therefore
not evidence -- the row keeps its ticker and name and resolves, or does not,
on those.
"""
from __future__ import annotations

__all__ = ["normalize_isin", "is_valid_isin"]


def normalize_isin(raw: str | None) -> str | None:
    """Whitespace and case only. Nothing else about an ISIN is Atlas's to
    change, and an empty string is absence, never evidence."""
    if raw is None:
        return None
    cleaned = raw.strip().replace(" ", "").upper()
    return cleaned or None


def is_valid_isin(candidate: str | None) -> bool:
    """ISO 6166: two letters, nine alphanumerics, one check digit, verified
    by the Luhn sum over the digit-expanded body."""
    value = normalize_isin(candidate)
    if value is None or len(value) != 12:
        return False
    if not value[:2].isalpha() or not value[2:].isalnum() or not value[11].isdigit():
        return False

    # Letters expand to their position value (A=10 ... Z=35), then Luhn runs
    # over the resulting digit string.
    digits = "".join(
        str(ord(character) - 55) if character.isalpha() else character
        for character in value[:11]
    )
    total = 0
    # Doubling starts from the rightmost body digit, so parity depends on the
    # expanded length rather than the original character positions.
    double = True
    for character in reversed(digits):
        digit = int(character)
        if double:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
        double = not double
    return (10 - total % 10) % 10 == int(value[11])

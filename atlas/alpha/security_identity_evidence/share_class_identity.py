"""What an ISIN can and cannot prove, stated once.

Measured against the live provider, 2026-09-16:

* `SE0000115446` (Volvo B) returns **209** listings.
* `FR0000121972` (Schneider Electric) returns **156**.
* `CA8672241079` (Suncor Energy) returns **171**.

So an ISIN does not name one tradeable listing, and any code that expects
it to will either pick arbitrarily or give up. Both are wrong. What an ISIN
names is a *share class*, and every one of those hundreds of listings agrees
about which share class it is: all 209 Volvo B rows carry
`shareClassFIGI = BBG001S69SV8`.

That agreement is the identity worth keeping. It is stable across venues,
it survives a company being listed somewhere new, and it separates the two
securities that motivated all of this:

    Schneider Electric  ticker SU on exchCode FP  ->  BBG001S67MN2
    Suncor Energy       ticker SU on exchCode CN  ->  BBG001S5YSF0

Same ticker. Different companies. Different share classes. A ticker cannot
tell them apart and a share-class FIGI cannot confuse them.

Unanimity is required rather than assumed. If a response ever disagrees with
itself about the share class, that is not something to average out or take a
majority of -- it means the ISIN does not identify one thing, and the honest
answer is to resolve nothing.
"""
from __future__ import annotations

from dataclasses import dataclass

from atlas.alpha.security_identity_evidence.openfigi_adapter import OpenFigiMatch

__all__ = ["ShareClassIdentity", "share_class_identity"]


@dataclass(frozen=True)
class ShareClassIdentity:
    """The share class an ISIN names, plus what every listing agreed on."""

    share_class_figi: str
    name: str | None
    security_type: str | None
    listing_count: int


def share_class_identity(matches: tuple[OpenFigiMatch, ...]) -> ShareClassIdentity | None:
    """The one share class every listing agrees on, or `None`.

    `None` means exactly one of three honest things -- the provider knew
    nothing, no listing carried a share class, or the listings disagreed --
    and in all three the caller must resolve nothing rather than guess.
    """
    if not matches:
        return None

    figis = {match.share_class_figi for match in matches if match.share_class_figi}
    if len(figis) != 1:
        # Zero: nothing to key on. More than one: the ISIN is not naming a
        # single share class, so neither can we.
        return None

    share_class_figi = figis.pop()
    agreeing = [m for m in matches if m.share_class_figi == share_class_figi]
    names = {m.name for m in agreeing if m.name}
    types = {m.security_type for m in agreeing if m.security_type}
    return ShareClassIdentity(
        share_class_figi=share_class_figi,
        # Descriptive only, and only when undisputed. Never a match key:
        # names are for a human reading an audit trail.
        name=names.pop() if len(names) == 1 else None,
        security_type=types.pop() if len(types) == 1 else None,
        listing_count=len(agreeing),
    )

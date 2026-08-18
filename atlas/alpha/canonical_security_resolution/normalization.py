"""Resolution algorithm steps 1-2 (Sprint N Phase 5): normalize company
text and ticker.

Company-name normalization reuses `atlas.alpha.security_discovery.
canonicalize.canonicalize_company_text` rather than reimplementing it --
that function is already the exact deterministic, non-fuzzy, binary
comparison primitive Sprint J/K identified as the right tool for this
job (see `docs/canonical_security_identity_design.md` Phase 5), and it
is already reused by `atlas.alpha.security_identity_evidence` for the
same purpose. Re-deriving a second normalization function here would
create two subtly different definitions of "the same company name" in
the codebase -- exactly the kind of drift this whole resolution service
exists to prevent.
"""
from __future__ import annotations

from atlas.alpha.security_discovery.canonicalize import canonicalize_company_text


def normalize_company_text(text: str | None) -> str:
    """Empty string for `None` or blank input -- callers compare this
    against candidates whose own `company_name` may also be absent;
    two empty strings are never treated as agreeing (see
    `comparison.py`'s own `agrees=None` handling for missing data)."""
    if text is None:
        return ""
    return canonicalize_company_text(text)


def normalize_ticker(ticker: str) -> str:
    """`.strip().upper()` -- the same structural-only normalization
    already used everywhere else on the live path (Watchlist,
    Portfolio; see `docs/identity_integration_architecture.md` Phase 2).
    Never a candidate for the ATLAS-031A-style provider-local ticker
    variants (`BRK.B` -> `BRK-B`) -- that remains a provider-adapter
    concern, not a cross-provider normalization concern."""
    return ticker.strip().upper()

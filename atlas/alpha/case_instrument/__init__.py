"""The authoritative Case -> operative-instrument binding for Alpha.

**What this package exists to fix.** A Core `Case` is, by doctrine, "a
single, immutable ownership boundary" carrying only `id` and
`recorded_at` (`OE-002` §3.1). It has never known which security it is
about. Alpha recovered that backwards, from membership: a Portfolio
holding whose `case_id` matched, or a Watchlist entry whose `case_id`
matched -- including deliberately-preserved *removed* Watchlist rows,
which is what has been keeping a de-listed prospect's Case readable.

That worked, but it made the investor's *relationship* to a company the
source of the Case's *identity*. The visible consequence:
`CaseGenerationService.ensure_case_id` accepts a ticker and never
persists it, so a Case created outside a membership add path came
back with no company profile, no business facts and no coverage -- an
Investment Case that cannot say which company it is about. That is why
Discovery could only reach a real Case by adding to the Watchlist
first.

This package holds the binding instead. Membership stays exactly what
it should be: a statement about the investor's relationship to an
instrument, not the reason Atlas knows what the instrument is.

**Why the Core aggregate is untouched.** Putting a ticker on `Case`
would change Core doctrine for an Alpha-layer concern, and would put
the weaker of Atlas's two identity models into the domain's own
vocabulary. The binding lives here, beside the membership tables it
replaces as an authority.

**Why not `canonical_security_id` yet.** `atlas.alpha.canonical_security`
is the right long-term target -- stable ids, exchange MICs, share
classes -- but it currently resolves 15 of the 26 case-bearing tickers
in the real corpus; the other 11 (ABB, ALFA, ASSA-B, ATCO-B, INVE-B,
LATO-B, MTRS, SAND, SU.PA, TSMC, VOLV-B) have already been through
canonical resolution and returned a persisted `NO_MATCH`. Closing that
gap needs provider access, which a backfill may not do. It is also in
deliberate shadow mode: `tests/unit/alpha/canonical_security
/test_integration_safety.py` forbids exactly this kind of wiring.

So `instrument_key` carries the operative ticker Atlas already keys
every other subsystem on (`business_records.company`, the trade log's
`security`, both membership tables), and `canonical_security_id` sits
beside it, nullable and unused, so a row can gain a canonical identity
later without another schema change and without touching Core.
"""

"""Canonical Security Identity Gate -- Sprint O.

The mandatory checkpoint between "a provider returned data for a
ticker" and "a `BusinessRecord` gets created for it." Wires Sprint N's
shadow-only `CanonicalSecurityResolutionService`
(`atlas.alpha.canonical_security_resolution`) into the live enrichment
pipeline for the first time: every prior sprint in this arc (J through
N) built the identity model, the resolution algorithm, and the shadow
persistence layer without touching production behavior at all. This
package is where that stops being true, on purpose, and only here.

    RawBusinessDocument(s)
            |
            v
    candidate_mapping.candidates_from_documents()   -- ProviderCandidate(s)
            |
            v
    CanonicalSecurityIdentityGate.evaluate()
            |
            v
    CanonicalSecurityResolutionService.resolve()     -- Sprint N, unmodified
            |
            v
    GateDecision(allowed, outcome, provenance | None)

`allowed=True` only when the resolution outcome is `AUTO_ACCEPT` and
the resulting `CanonicalSecurity` reached `CANONICAL` -- every other
outcome (`MANUAL_CONFIRMATION`, `LOW_CONFIDENCE`, `AMBIGUOUS`,
`NO_MATCH`, `REJECT`) is `allowed=False`. No fallback, no provider
retry, no automatic ADR substitution: `evaluate()` makes exactly one
resolution attempt and returns a decision the caller
(`atlas.alpha.business_data_refresh.service.refresh_company_data`)
acts on deterministically.

**What this package deliberately does not do:**
- Does not call a provider itself -- `candidate_mapping` only ever
  reads the `RawBusinessDocument`s its caller already fetched.
- Does not modify `atlas.alpha.canonical_security` or
  `atlas.alpha.canonical_security_resolution` -- both are used exactly
  as Sprint M/N built them.
- Does not change what a `BusinessRecord` *means* -- only which
  `BusinessRecord`s ever get constructed, and what provenance they
  carry once they do (see `provenance.BusinessRecordIdentityProvenance`
  and the four new, optional, additive fields on `BusinessRecord`
  itself).

**No provider adapter is touched or imported by name.**
`candidate_mapping.py` maps generically off `RawBusinessDocument
.provider_id` (a plain string) and `.metadata` (a plain dict) -- adding
a fifth provider later means adding one entry to a lookup table, never
changing this package's logic, and never importing
`atlas.business_data_providers.*` from here.

This is the one package in this codebase explicitly allowed to import
*both* `atlas.alpha.canonical_security`/`canonical_security_resolution`
*and* `atlas.analysis_engine.business_data`/`atlas.alpha
.business_data_refresh` -- see the updated integration-safety guards in
both canonical-security test directories, which name this package as
the single, deliberate exception the whole arc since Sprint M was
building toward.
"""

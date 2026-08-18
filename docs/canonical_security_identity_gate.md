# Canonical Security Identity Gate — Sprint O

**Sprint scope:** wire Sprints J–N's Canonical Security foundation,
Confidence Engine, and Resolution Service into the live enrichment
pipeline as a **mandatory** checkpoint. No BusinessRecord may be created
from an unresolved, ambiguous, or unsafe security identity. This sprint
introduces exactly one thing — the gate — and touches nothing else:
`BusinessRecord` semantics are unchanged, Investment Case semantics are
unchanged, provider adapters are unchanged.

---

## 1. What the gate is

`atlas.alpha.canonical_security_gate.gate.CanonicalSecurityIdentityGate`
(`atlas/alpha/canonical_security_gate/gate.py`) is the one checkpoint
between "a provider returned identity-bearing documents for a ticker" and
"a `BusinessRecord` may be created for it." It wraps Sprint N's
`CanonicalSecurityResolutionService` unmodified and enforces its outcome
table exactly:

| Outcome | Gate decision |
|---|---|
| `AUTO_ACCEPT` (and `CanonicalSecurity.resolution_status == "CANONICAL"`) | **proceed** |
| `MANUAL_CONFIRMATION` | stop |
| `LOW_CONFIDENCE` | stop |
| `AMBIGUOUS` | stop |
| `NO_MATCH` | stop |
| `REJECT` | stop |

No fallback, no provider retry, no automatic ADR substitution.
`evaluate()` makes exactly one resolution attempt and returns a
`GateDecision` the caller acts on deterministically — `allowed: bool`,
`outcome`, a human-readable `reason`, and (only when `allowed`) a
`BusinessRecordIdentityProvenance` to stamp onto every record the run
produces.

## 2. Where it sits: the integration package

`atlas/alpha/canonical_security_gate/` is the **one** package in the
codebase allowed to import both `atlas.alpha.canonical_security` /
`canonical_security_resolution` (Sprints J–N's identity model) and
`atlas.analysis_engine.business_data` / `atlas.alpha.business_data_refresh`
(the enrichment pipeline). This boundary is enforced mechanically, not
just by convention: the AST-based integration-safety guard tests in
`tests/unit/alpha/canonical_security/test_integration_safety.py` and
`tests/unit/alpha/canonical_security_resolution/test_integration_safety.py`
both exclude this package (and its own tests) and then assert that *no
other file anywhere in the repository* imports both sides. Every
production caller — `business_data_refresh/service.py`, `bulk.py`,
`cli.py`, the three API `dependencies.py` modules, `watchlist/service.py`,
`portfolio/service.py` — reaches the gate only through this package;
none of them import `canonical_security`/`canonical_security_resolution`
directly.

Sub-modules:

- `exchange_mapping.py` — `map_exchange_display_name_to_mic`, a closed
  dict translating the free-text exchange strings providers return
  ("NASDAQ", "NYSE", …) into MIC codes the Sprint J model requires.
- `candidate_mapping.py` — `candidates_from_documents`, turning a tuple
  of `RawBusinessDocument` (only `SourceKind.COMPANY_PROFILE` ones) into
  `ProviderCandidate` tuples the Resolution Service consumes, with
  defensive parsing that returns `None` for anything malformed rather
  than raising or fabricating a value.
- `provenance.py` — `BusinessRecordIdentityProvenance`, the four fields
  (`canonical_security_id`, `resolution_version`, `resolved_at`,
  `provider_evidence_reference`) threaded onto every `BusinessRecord`
  created in an allowed run.
- `gate.py` — the gate itself, described above.
- `factory.py` — `build_identity_gate(engine)`, the **sole** construction
  point, for both production wiring and every test fixture. It creates
  the Sprint M (`canonical_security`) and Sprint N
  (`canonical_security_resolution`) tables and constructs the full gate
  in one call, so no caller — production or test — ever needs its own
  direct import of either package.

## 3. Where it sits: the pipeline

`refresh_company_data()` (`atlas/alpha/business_data_refresh/service.py`)
now takes `identity_gate` as a required keyword-only argument — there is
no optional or bypass path at this layer. Its fetch order was restructured
specifically for this sprint:

1. Every provider implementing `CompanyProfileProvider` is asked for its
   identity documents **first** — before any fundamentals or
   market-data fetch.
2. `identity_gate.evaluate(ticker=..., documents=<profile documents>)`
   runs exactly once against whatever candidates that produced.
3. If the decision is not `allowed`, the function returns immediately:
   `RefreshSummary.identity_gate_outcome`/`identity_gate_reason` report
   why, `new_records == 0`, and — critically — **no other provider is
   ever called**. SEC EDGAR's fundamentals fetch, Alpha Vantage's quote
   fetch, the historical-snapshot pass: none of them run. This is the
   literal implementation of "no fallback, no provider retry."
4. If allowed, the profile documents are ingested first (carrying the
   gate's provenance), then the normal fundamentals/market-data/
   historical passes proceed, each ingested `BusinessRecord` stamped
   with the identical `CanonicalSecurity` provenance from step 2.

`ensure_company_enriched()` (the Watchlist/Portfolio automatic-trigger
entrypoint) and `enrich_holdings()` (bulk enrichment) both require
`identity_gate` the same way and delegate straight through — they gained
no new logic of their own, only the same mandatory dependency.

`AlphaWatchlistService` and `AlphaPortfolioService` each gained
`identity_gate` as a third, all-or-nothing enrichment dependency:
automatic enrichment on "add a ticker" only fires when
`business_record_repository`, `business_data_providers`, and
`identity_gate` are *all* wired; omitting any of them is a deliberate,
pre-existing no-op, never an error.

## 4. Failure handling and evidence capture

Every resolution attempt is persisted — allowed or not. `evaluate()`
always calls `SqlAlchemyResolutionRepository.save()`, including the
zero-candidate case (constructed directly as a `NO_MATCH`
`ResolutionResult` rather than calling `resolve()`, which raises for an
empty candidate tuple — a real, expected case this gate must not treat
as a crash). A blocked run is never silent: `RefreshSummary` carries the
exact outcome and a human-readable reason, and the full evidence trail
(which candidates were seen, what confidence each reached, why) lives in
the Sprint N resolution-record row referenced by
`provider_evidence_reference`.

## 5. Provenance on BusinessRecord

Four new, nullable, additive fields on `BusinessRecord`
(`atlas/analysis_engine/business_data/models.py`), its table
(`atlas/alpha/business_data_refresh/table.py`), and its repository
round-trip (`repository.py`):

- `canonical_security_id`
- `resolution_version`
- `identity_resolved_at`
- `provider_evidence_reference`

All four are `None` on every pre-Sprint-O record — no migration, no
backfill. Within any single allowed `refresh_company_data` run, all four
are always populated together, identically, on every record the run
produces (fundamentals, market snapshots, the profile document itself).
A second run for the same ticker reuses the same `CanonicalSecurity`
(verified by `_find_existing`, which looks up
`CanonicalSecurityRepository.find_by_ticker_and_exchange` before
resolving) rather than creating a duplicate identity.

## 6. Manual confirmation — backend pathway only

No UI is built in this sprint. What exists is that
`GateDecision.resolution_result` deliberately exposes the complete
`ResolutionResult` object, so a future manual-confirmation UI can call
`CanonicalSecurityResolutionService.confirm_manually(result,
chosen_candidate=...)` directly against it — proven end-to-end by
`tests/unit/alpha/canonical_security_gate/test_manual_confirmation_pathway.py`.
The gate does not build, wire, or expose this to any API endpoint;
it only avoids closing the door Sprint N already opened.

## 7. Pipeline invariants (Phase 14)

These are structural, not just tested-and-hoped-for — each is backed by
a specific mechanism, and violating any of them is either a compile-time
impossibility or a test failure:

1. **No `BusinessRecord` without a `CanonicalSecurity`.** Every ingestion
   call inside `refresh_company_data` runs only after `identity_gate`
   returned `allowed=True`; the function returns before any fetch beyond
   the identity pass otherwise. Enforced by
   `test_identity_gate_integration.py::TestNoBusinessRecordWithoutCanonicalSecurity`.
2. **No gate bypass.** `identity_gate` is a required keyword-only
   parameter on `refresh_company_data`, `ensure_company_enriched`, and
   `enrich_holdings` — there is no code path in this package that
   constructs a `BusinessRecord` without going through one of these three
   functions.
3. **No provider identity bypass.** Identity candidates come only from
   `CompanyProfileProvider.fetch_company_profile()` responses, mapped
   through `candidates_from_documents`. A provider that only implements
   `fetch()` (fundamentals/market data) contributes zero identity
   candidates, by construction — there is no path for a fundamentals
   document to influence the gate's decision.
4. **No ticker-only path.** `NO_MATCH` is the explicit, tested outcome
   when zero identity-bearing documents exist — a ticker string alone,
   with no provider corroboration, can never reach `AUTO_ACCEPT`.
5. **No ADR/native auto-merge.** The gate calls
   `CanonicalSecurityResolutionService.resolve()` exactly once per
   evaluation with no retry and no substitution logic of its own; any
   ADR-vs-native disambiguation is entirely Sprint N's Confidence
   Engine's own Rule 1–4 logic (unchanged), not something this gate adds
   or overrides.
6. **Every attempt is recorded.** `SqlAlchemyResolutionRepository.save()`
   is called on every `evaluate()` invocation, allowed or not — there is
   no early return that skips persistence.

## 8. Existing Cases and BusinessRecords — untouched

No migration was written or is needed. Every `BusinessRecord` persisted
before this sprint has all four provenance fields as `None`; the
repository's `_to_record` reads them via `.get()` for exactly this
backward-compatible reason. Existing Investment Cases, existing
Watchlist/Portfolio entries, and existing `BusinessRecord` rows are
unaffected — they simply have no identity provenance until (and unless)
they go through a fresh, allowed `refresh_company_data` run.

## 9. Architecture verification against Sprints J–N (Phase 18)

The gate implements Sprint N's own documented outcome table and
Confidence Engine rules (`canonical_security_resolution/confidence.py`)
without modification — this sprint added zero lines to
`canonical_security`, `canonical_security_resolution`, or their
Confidence Engine. The one deviation from a literal reading of the
Sprint N design is deliberate and narrow: `evaluate()` special-cases the
empty-candidate case to build a `NO_MATCH` `ResolutionResult` directly
rather than calling `resolve()` (which raises `NoCandidatesToResolveError`
for that input) — a caller-side adaptation, not a change to Sprint N's
resolution semantics. Everything else — normalization, candidate
corroboration, the four confidence tiers, the six outcomes — is called
through Sprint N's public API exactly as designed.

## 10. Final review checklist (Phase 19)

- [x] Watchlist behavior unchanged except for the added, opt-in
      `identity_gate` enrichment dependency (existing no-op-when-
      unwired behavior preserved).
- [x] Portfolio behavior unchanged except for the same addition.
- [x] Investment Case composition semantics unchanged — this sprint
      touches only enrichment (pre-`BusinessRecord`), never composition
      (post-`BusinessRecord`).
- [x] Provider adapters (`sec_edgar.py`, `alpha_vantage.py`) unchanged —
      zero diffs in this sprint.
- [x] `BusinessRecord` creation is now unconditionally gated: no code
      path in `business_data_refresh` creates one without a prior
      `AUTO_ACCEPT` decision.
- [x] All identity resolution happens strictly before any
      `BusinessRecord` is created, never after or in parallel.
- [x] Full combined regression (`canonical_security`,
      `canonical_security_resolution`, `canonical_security_gate`,
      `business_data_refresh`, `watchlist`, `portfolio`,
      `investment_case`, `business_data_providers`, and the two
      `infrastructure/api` suites) — 712 passed, 0 failed, 0
      integration-safety-guard violations.
- [x] Narrow provider/business-data baseline
      (`-k "provider or business_data or sec_edgar or alpha_vantage"`)
      — 439 passed, 2 failed, identical to every prior sprint's
      pre-existing, unrelated `test_no_provider_imports_added` failures
      (a stale cached path unrelated to this sprint's changes).

## 11. Readiness assessment (Phase 20)

**Central finding — read this before assuming automatic enrichment still
works the way it used to.**

With the two provider adapters exactly as they exist today, unmodified:

- **SEC EDGAR** (`atlas/business_data_providers/sec_edgar.py`) discards
  the company `title` field from `company_tickers.json` when building
  its ticker→CIK cache — it supplies **zero** identity fields to the
  gate.
- **Alpha Vantage** (`atlas/business_data_providers/alpha_vantage.py`)'s
  `_IDENTITY_FIELD_MAP` supplies name/exchange/sector/industry/country/
  description/currency/fiscal-year-end, but **never** `security_type`
  (there is no `AssetType` mapping).

Confidence Engine Rule 3 requires `exchange_mic`, `country`, and
`security_type` **all** present on a candidate to reach `HIGH`
confidence; without all three, a single candidate tops out at `MEDIUM`
(→ `MANUAL_CONFIRMATION`) or `LOW` (→ `LOW_CONFIDENCE`). Since only one
of the two real providers supplies identity data at all, and that one
provider can never supply `security_type`, **`AUTO_ACCEPT` is
structurally unreachable for any new ticker today, through a single
real provider candidate alone.** It becomes reachable only through Rule
4's multi-provider-agreement tier promotion — two independent providers
corroborating the same canonicalized company name — which requires a
second identity source Atlas does not yet have (a future OpenFIGI,
Twelve Data, or similar adapter).

**Practical consequence:** as of this sprint, the Watchlist and
Portfolio automatic "add a ticker" enrichment paths will, for any
brand-new company, resolve to `MANUAL_CONFIRMATION` (or occasionally
`LOW_CONFIDENCE`/`NO_MATCH`) rather than `AUTO_ACCEPT` — meaning **no
`BusinessRecord` is created and no enrichment happens** for a newly
added ticker, silently, from the investor's point of view (the
enrichment trigger has always been a fire-and-forget background call;
this sprint makes it correctly block, but there is still no UI surface
that tells the investor why nothing showed up, since no UI work was in
scope). This is not a bug in this sprint's implementation — it is the
correct, designed behavior of "never create a BusinessRecord from an
unresolved identity" being enforced for the first time, exposing a real
gap that already existed silently before (providers were always this
identity-poor; nothing previously checked).

**What already works despite this:** any ticker whose
`CanonicalSecurity` was already established — by a prior run, by a
future manual-confirmation call, or by the multi-provider-agreement path
— is reused via `find_by_ticker_and_exchange` and continues to enrich
normally on every subsequent run. The gap is specifically the *first*
resolution of a *brand-new* ticker under exactly the two providers this
codebase has today.

**What closes the gap, in order of leverage:**

1. A second identity-bearing provider (OpenFIGI is purpose-built for
   this; Twelve Data's `symbol_search` was already evaluated in Sprint
   H) — reaches `AUTO_ACCEPT` via Rule 4 without touching Alpha
   Vantage's own field map.
2. Extending Alpha Vantage's own `_IDENTITY_FIELD_MAP` to derive
   `security_type` from its `OVERVIEW` response's `AssetType`-equivalent
   field, if one exists — reaches `HIGH` confidence from a single
   provider via Rule 3, without a second provider at all.
3. A manual-confirmation UI surfacing `MANUAL_CONFIRMATION`/
   `LOW_CONFIDENCE`/`AMBIGUOUS` cases — the backend pathway already
   exists (`confirm_manually`), only the UI is missing.

None of these three is in scope for this sprint; this section exists so
the gap is visible before it is discovered in production rather than
after.

**Readiness for Twelve Data / multi-provider / international / IFRS /
exchange-aware securities:** this sprint's model already carries
`exchange_mic` and is currency-aware end to end, so adding a genuinely
international, IFRS-reporting, exchange-disambiguated provider (Twelve
Data or otherwise) requires no schema change here — only a new
`CompanyProfileProvider` implementation feeding the same
`candidates_from_documents` path. The gate itself needs no changes to
support that provider; only `business_data_refresh`'s provider tuple
composition (already provider-agnostic, proven by the swappability
tests) needs to include it.

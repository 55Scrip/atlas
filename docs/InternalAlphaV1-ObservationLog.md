# Internal Alpha v1 — Observation Log

Real-portfolio usage session. Observation-first: findings recorded before any
fix is attempted. See the accompanying final report (delivered in chat, not
duplicated here) for prioritization, severity rollup, and the recommended
next sprint.

## Session

**Date:** 2026-08-10
**Scenario:** First real-portfolio usage pass. The Alpha portfolio already
held 25 real holdings (`entry_mode: IMPORTED`, established 2026-08-05) plus
one Watchlist entry (AAPL). No synthetic fixtures were used — all findings
below come from the actual running app against the actual `database/atlas.db`.
**Portfolio state:** 25 holdings (INVE-B, MSFT, AMZN, AVGO, GOOG, ABB, BRK.B,
META, VST, VOLV-B, AZN, ALFA, TREL-B, SAND, NVDA, ASSA-B, ATCO-B, MTRS, MA,
SEB-A, NVO, VRT, AMAT, CAST, SAVE), 22.07% unallocated cash, no absolute
portfolio value entered.
**What I was trying to do:** Use Atlas as a real investor would — audit data
coverage across every real holding, then walk Daily Brief, Portfolio,
Investment Case, and History as an investor reviewing their book.

---

## IA-001

**Area:** Portfolio / Data / Architecture
**Severity:** CRITICAL
**Status:** CONFIRMED

**Problem:** 20 of 25 real holdings (80%) had zero persisted `BusinessRecord`s
of any kind before this session — including large, liquid, obviously-covered
US names (AMZN, GOOG, MA, NVO, AMAT).

**Expected behavior:** Per the product's own stated core principle, no
holding should require manual research; automatic enrichment should have
already populated real financial data for every coverable holding.

**Actual behavior:** Only the 5 holdings that had been individually
live-verified in prior sprints (MSFT, AVGO, BRK.B, NVDA, META) plus the one
Watchlist entry (AAPL) had any data. Every holding that entered the portfolio
via the bulk `import_portfolio` path had none.

**User impact:** A real investor bulk-importing their existing portfolio —
the single most realistic onboarding path — gets a portfolio of 25 empty
Investment Cases, silently defeating the "no manual research" promise for
every holding except however many happen to get manually re-triggered later.

**Evidence:** Direct query against `database/atlas.db`; confirmed via
`SELECT DISTINCT document_type FROM business_records WHERE company = ?` for
every ticker.

**Root cause:** `atlas/alpha/portfolio/service.py`'s `import_portfolio` calls
`_ensure_cases` (creates Cases) but never calls `_trigger_enrichment`.
Enrichment (`ensure_company_enriched`) is wired only into the single-holding
trade-log path (`reconcile_replace_allocation`'s sibling, the BUY/ADD branch
around line 615) and into `AlphaWatchlistService.add`. This is not a latent
bug — it is an explicit, deliberate, disclosed scope decision from a prior
sprint, documented in the code itself: *"Deliberately NOT wired into the bulk
`import_portfolio`/`reconcile_replace_allocation` paths — see the design
record's Known Limitations for why a bulk, many-ticker import synchronously
triggering many sequential provider calls is out of this slice's scope."*
The refresh CLI's own docstring confirms the same intent: *"do not refresh
all 25 live internal holdings automatically. Start with one or two explicitly
selected internal Cases."*

**Recommended next action:** Design a rate-limit-aware, batched backfill path
for bulk-imported portfolios (either an explicit operator/UI-triggered bulk
refresh, or an async queue with pacing) — this is the strongest, most
evidence-backed candidate for the next sprint.

**Implementation required now:** No — worked around by manually enriching two
explicitly-selected holdings (AMZN, GOOG) via the already-shipped
`python -m atlas.alpha.business_data_refresh.cli` tool, matching that tool's
own documented intended usage exactly. No production code was changed for
this observation.

---

## IA-002

**Area:** Data / Architecture
**Severity:** MEDIUM
**Status:** CONFIRMED

**Problem:** SEC EDGAR extraction only reads `us-gaap`-taxonomy concepts.
Foreign private issuers that resolve to a real SEC CIK but file Form 20-F
under the `ifrs-full` taxonomy get zero fundamentals data.

**Expected behavior:** Either real IFRS-taxonomy data, or at minimum this is
an acceptable, explicit gap — not a silent one.

**Actual behavior:** It already fails honestly and explicitly — no fabricated
data, a clear typed provider error (`"SEC companyfacts for CIK 0000901832
(AZN) has no us-gaap facts at all"`) — but real fundamentals data that likely
exists in SEC's own IFRS-tagged filings for this class of company is left
uncollected.

**User impact:** Dual-listed / foreign-domiciled holdings (a real, non-trivial
slice of an internationally diversified portfolio — this one has ABB, AZN,
NVO, VOLV-B, and others) get market data (via Alpha Vantage) but never real
SEC fundamentals, even when SEC EDGAR does have structured data for them.

**Evidence:** Live CLI run against AZN (AstraZeneca's NASDAQ ADR, real CIK
0000901832): SEC leg failed with the exact error above; Alpha Vantage leg
succeeded (2 new records, no error).

**Root cause:** `atlas/business_data_providers/sec_edgar.py`'s
`_DURATION_CONCEPT_TAGS`/`_INSTANT_CONCEPT_TAGS` only ever look under
`facts["us-gaap"]` in SEC's `companyfacts` response; the parallel
`facts["ifrs-full"]` namespace SEC also serves for 20-F filers is never
consulted.

**Recommended next action:** Not urgent. Worth scoping in a future data
sprint if international/dual-listed coverage becomes a priority.

**Implementation required now:** No.

---

## IA-003

**Area:** Portfolio / Investment Case / Architecture
**Severity:** CRITICAL
**Status:** CONFIRMED

**Problem:** The Portfolio page's headline "Conviction" and "Evidence"
columns — the first thing an investor sees when scanning their holdings —
show "Insufficient evidence" for **every single holding**, including ones
with rich, `confidence: full` real financial analysis.

**Expected behavior:** A holding with real, full-confidence Growth, Capital
Allocation, Financial Risk, and Valuation findings should read as
materially different, at the portfolio-glance level, from a holding with
zero data.

**Actual behavior:** MSFT — 16+ years of real SEC financials, `"business":
{"growth":"moderate","capitalAllocation":"moderate"}`, `"valuation":
{"status":"fairly_valued","confidence":"full"}` with 20 years of supporting
FCF-yield facts, `"financial_risk"` at `"confidence":"full"` — still reports
top-level `"conviction":{"level":"insufficient_evidence","reasons":
["evidence_coverage_insufficient"]}`. Every other holding checked (ABB,
ALFA, META, INVE-B, AMZN, GOOG) shows the identical `conviction.level`
regardless of how much real company data exists underneath.

**User impact:** This is the single most damaging finding for "is Atlas
usable for real investing work." The primary triage surface gives literally
zero differentiating signal between a holding Atlas has deeply analyzed and
one it knows nothing about. A real investor scanning this table would
reasonably conclude Atlas has nothing on any of their 25 holdings — false.

**Evidence:** Direct comparison of `/api/alpha-portfolio/cockpit`'s
per-holding `conviction` field against the same holding's own rich
`business`/`valuation`/`riskFindings` fields, returned in the *same* API
response, for MSFT and five other holdings.

**Root cause:** Two separate, never-reconciled "conviction"/"evidence"
concepts coexist in the codebase: the original `decision_engine`'s
investor-recorded-evidence-trail concept (gated on whether the investor has
personally logged `Observation`s under a `Decision` for that holding — see
`evidence_coverage_insufficient`), and the newer `analysis_engine`'s
company-data-driven findings (Growth/Capital Allocation/Risk/Valuation,
built across the last several sprints). The Portfolio table's headline
columns read only the former.

**Recommended next action:** The strongest, most evidence-backed candidate
for the next sprint. Either (a) have the Portfolio-level "Conviction"
concept incorporate the real company-data confidence signal Atlas already
computes, or (b) if the two concepts must stay separate by design, rename
and visually separate them so a real investor is never told "insufficient
evidence" about a holding Atlas has actually analyzed in depth one click
away.

**Implementation required now:** No — does not corrupt data, does not block
continued use (the Investment Case page itself is fully accurate); it is a
critical usability/architecture problem, not a blocking bug.

---

## IA-004

**Area:** Daily Brief / History / Analysis
**Severity:** MEDIUM
**Status:** CONFIRMED

**Problem:** Change Intelligence phrases a one-time data backfill (a company
that had zero data now has data for the first time) identically to an
organic market/company event.

**Expected behavior:** Per the sprint's own design goal, Atlas should
distinguish "the company changed" from "Atlas's analytical coverage of the
company changed."

**Actual behavior:** After manually enriching AMZN and GOOG, Daily Brief
read: *"New risk identified: financial risk,"* *"New risk identified:
valuation,"* — phrased exactly as it would for a real, newly-discovered
market risk, with no "this is first-time coverage" framing.

**User impact:** A real investor could reasonably read this as "something
changed in the market for AMZN today" when in fact nothing changed except
that Atlas's own data foundation caught up.

**Evidence:** `/daily-brief` page content, captured immediately after the
AMZN/GOOG CLI enrichment.

**Root cause:** Not fully traced — the change-detection logic in
`investment_case_change` treats "field went from null to populated" the same
as "field's value changed" for the purpose of framing a finding as a new
risk, without a distinct "first coverage" case.

**Recommended next action:** Add a distinct "coverage established" framing
to Change Intelligence, separate from "risk newly identified," for the
specific case of a finding moving from `insufficient_input` (never
evaluated) directly to a real status.

**Implementation required now:** No.

---

## IA-005

**Area:** History / Reliability
**Severity:** MEDIUM
**Status:** OBSERVED

**Problem:** History shows byte-identical entries for the same underlying
event, twice, milliseconds apart.

**Expected behavior:** One timeline entry per real analytical change.

**Actual behavior:** Two GOOG entries with identical text
(`"Atlas can now evaluate Growth..."` etc.) at `2026-08-10T19:59:30.212178Z`
and `2026-08-10T19:59:30.210394Z` — 1.8ms apart. A similar adjacent-duplicate
pattern was visible for AMZN immediately below.

**User impact:** Timeline noise; directly touches the sprint's own "is
History too noisy?" test question — for this specific case, yes.

**Evidence:** `/history` page content, same session.

**Root cause:** Not investigated. Plausibly one `AnalyticalSnapshot` per
provider leg of the same CLI refresh (SEC vs. Alpha Vantage), not coalesced
into a single snapshot per refresh operation.

**Recommended next action:** Investigate whether snapshot persistence should
coalesce multiple provider updates from one refresh call into one row.

**Implementation required now:** No.

---

## IA-006

**Area:** Reliability
**Severity:** LOW
**Status:** OBSERVED

**Problem:** The business-data-refresh CLI depends on
`ALPHA_VANTAGE_API_KEY` already being present in the invoking shell's
environment; it does not load the repo's own `.env`.

**Expected behavior:** Running the CLI exactly as documented
(`python -m atlas.alpha.business_data_refresh.cli TICKER`) should pick up the
real key already sitting in `.env`.

**Actual behavior:** First invocation failed with `"ALPHA_VANTAGE_API_KEY is
not set"` for all three Alpha Vantage legs, despite a valid key being present
in `.env` at the repo root. Explicitly sourcing `.env` first
(`set -a && source .env && set +a`) fixed it.

**User impact:** Low — a one-time, easily-diagnosed operator paper cut. Does
not affect the actual running backend server (which is launched separately
and, empirically, does have the key available).

**Evidence:** Direct CLI run, first without and then with `.env` sourced.

**Root cause:** No `load_dotenv`/`python-dotenv` call anywhere in the
codebase (confirmed via repo-wide grep) — the app never reads `.env` itself;
whatever process launches the real backend server evidently gets the key
some other way (shell profile, IDE launch config), which the bare CLI
invocation doesn't inherit by default.

**Recommended next action:** Minor DX polish for a future sprint — not
urgent.

**Implementation required now:** No.

---

## IA-007

**Area:** Portfolio / UX
**Severity:** MEDIUM
**Status:** OBSERVED

**Problem:** The "Today's Priorities" panel singles out ABB and ALFA
specifically ("Complete evidence for ABB — Missing evidence") as High
Priority items, while 23 other holdings with an apparently identical
`conviction: insufficient_evidence` status are not flagged there at all. The
Holdings table's own per-row "Priority" column shows "Standard review"
uniformly for all of them, including ABB and ALFA.

**Expected behavior:** Not established — this may be correct behavior driven
by a real distinction (recorded Decision without Observations, vs. no
Decision at all) that simply isn't visible in the UI, or it may be a genuine
inconsistency.

**Actual behavior:** As described — the two lists disagree with no visible
explanation in the UI for why ABB/ALFA are singled out.

**User impact:** A real investor scanning both panels would be confused
about why two holdings out of 25 are called out.

**Evidence:** `/portfolio` page content, same session.

**Root cause:** Not investigated in this session — flagging for triage.

**Recommended next action:** Trace `deriveOutstandingWork`/equivalent
backend logic to confirm whether this reflects a real, meaningful
distinction and, if so, surface that distinction in the UI; if not, fix the
inconsistency.

**Implementation required now:** No.

---

## IA-008

**Area:** Portfolio / UX
**Severity:** LOW
**Status:** OBSERVED

**Problem:** Portfolio Summary reads "Needs attention: 1" directly above a
"Today's Priorities" panel that lists 3 distinct items (1 Highest + 2 High).

**Expected behavior:** The summary count should match what's enumerated
immediately below it, or the discrepancy should be explained.

**Actual behavior:** As described.

**User impact:** Minor — a real investor would likely notice the mismatch
and lose a small amount of trust in the surrounding numbers.

**Evidence:** `/portfolio` page content, same session.

**Root cause:** Not investigated.

**Recommended next action:** Confirm whether "Needs attention" counts only
the Highest-priority tier by design, and if so, either relabel it or make it
count everything shown below.

**Implementation required now:** No.

---

## What worked well (do not change)

- Case creation/reuse: all 25 holdings plus the AAPL Watchlist entry each
  resolve to exactly one Case; zero duplicates found.
- The Company Data Foundation v1 provider pipeline (SEC EDGAR + Alpha
  Vantage) worked flawlessly live against two freshly-enriched real
  companies (AMZN, GOOG) with zero provider errors on the second pass.
- Provider failure isolation is real and honest: a genuinely uncovered
  holding (INVE-B, Swedish OMX-only) produced zero fabricated records and
  clear, typed, per-provider error messages — no partial/fake data.
- Investment Case pages render rich, accurate, correctly-signed multi-decade
  financial histories (AMZN back to 2007, including real negative-income
  years) with an honest "—" placeholder for genuinely missing periods.
- Change Intelligence and Daily Brief correctly detected and surfaced both
  real enrichments the moment they landed — the mechanism works; only the
  framing (IA-004) needs work.
- Unallocated capital (22.07%) is computed and shown honestly, never
  silently normalized to 100%.

# Architecture Consolidation (Sprint 44)

This document records the current state of Atlas architecture as of Sprint 44,
clarifies which layers are current vs. legacy, and defines guardrails for
future sprints. It does not change runtime behavior.

## Current Layers

Atlas currently has two parallel layers that have not yet been merged:

### 1. Blueprint-aligned layer (current architecture)

- `atlas/domains/` — owns canonical concepts and contracts: `portfolio`,
  `watchlist`, `research`, `decision`, `decision_journal`, `daily_brief`,
  `knowledge`, `ai`, `authentication`. Domains depend only on
  `atlas.shared` entities.
- `atlas/capabilities/` — composes domains into product-level, deterministic
  reasoning: `company_analysis`, `discovery`, `watchlist_intelligence`.
  Capabilities depend on domains, not on providers or legacy engines.
- `atlas/shared/` — canonical, immutable entities (`Portfolio`, `Holding`,
  `Company`, `Watchlist`, `ResearchNote`, `JournalEntry`, `User`,
  `MarketEvent`, `Decision`, `KnowledgeNode`).

This is the architecture all new product work should build on.

### 2. Legacy / engine layer (compatibility, not for expansion)

Modules such as `atlas/analysis/`, `atlas/portfolio_review/`,
`atlas/watchlist_review/`, `atlas/comparison/`, `atlas/conversation/`,
`atlas/dashboard/`, `atlas/daily/`, `atlas/decision_journal/` (top-level),
`atlas/economics/`, `atlas/evidence/`, `atlas/home/`, `atlas/intelligence/`,
`atlas/language/`, `atlas/market/`, `atlas/memory/`, `atlas/monitoring/`,
`atlas/principles/`, `atlas/profile/`, `atlas/reasoning/`, `atlas/risk/`,
`atlas/risk_drift/`, `atlas/suitability/`, `atlas/themes/`, `atlas/database/`,
`atlas/services/`, `atlas/models/` are the original working engines that
predate the domain/capability split. They remain functional and fully
tested, and the CLI currently calls them exclusively.

These modules are compatibility layers. They should not gain new
responsibilities; new product capabilities belong in
`atlas/domains`/`atlas/capabilities`.

### 3. Provider layer

`atlas/providers/` defines `CompanyDataProvider` (interface),
`MockCompanyAnalysisProvider` (default, no network access), and
`YahooFinanceProvider` (live HTTP calls via `urllib.request.urlopen`,
`atlas/providers/yahoo.py`).

### 4. CLI / runtime layer

`atlas/cli/main.py` is the Typer entry point (`atlas` console script). As of
Sprint 44, every CLI command imported exclusively from the legacy engine
layer and `atlas.services`, with nothing wired to `atlas.domains` or
`atlas.capabilities`.

**Sprint 45 update:** `atlas portfolio summary <portfolio.json>` is the
first CLI command that calls `atlas.domains.portfolio` (via the new
`atlas.adapters.portfolio` bridge described below). It is read-only,
additive, and does not call providers or external APIs. The two pre-existing
portfolio commands (`atlas portfolio analyze`, `atlas portfolio review`)
were left untouched — they answer different questions (ticker-fit analysis,
CIO-style review with profile/market dependencies) that do not map cleanly
onto the Portfolio Domain's allocation/concentration/validation scope, so
migrating them was judged unsafe for this sprint. All other CLI commands
still call the legacy engine layer exclusively.

**Sprint 46 update:** `atlas portfolio analyze <portfolio.json> TICKER` now
also calls `atlas.domains.portfolio` via the same adapter, appending a
"Portfolio Summary (Portfolio Domain)" section after its existing,
unchanged `PortfolioAnalysis` output. The command's proprietary fit-scoring
logic (diversification impact, sector/country/market-cap concentration
impact, overlap, expected quality/risk impact, the `Strong Add`/`Add`/
`Neutral`/`Reduce`/`Avoid` recommendation) was **not** migrated and remains
on `atlas.analysis.portfolio.PortfolioIntelligenceEngine` unchanged — it
answers "how well would this new ticker fit the portfolio", a question the
Portfolio Domain does not (and should not) attempt to answer, since the
domain is about understanding existing portfolio structure, not scoring
hypothetical additions. `atlas portfolio review` remains entirely legacy
and out of scope for this sprint.

### 5. Adapter layer

`atlas/adapters/` is the one layer permitted to import both the legacy
engine layer and `atlas.domains`/`atlas.shared`. Adapters translate legacy
runtime data shapes into domain entities. They must stay deterministic,
must not call external APIs, and must not mutate persisted data. Domains
must never import adapters back (enforced by
`tests/test_architecture_boundaries.py`), keeping the dependency direction
one-way: legacy/CLI -> adapters -> domains.

`atlas.adapters.portfolio.legacy_portfolio_to_domain_portfolio` translates
the legacy CLI portfolio JSON (positions with a relative `weight`, no
absolute market value) into `atlas.shared.Portfolio`/`Holding` entities,
using each position's `weight` as a stand-in `market_value`. This preserves
all relative domain calculations (allocation, concentration, top holdings)
exactly, but does not produce a meaningful absolute currency total — that
limitation is documented in the adapter module itself.

## Known Duplication

- Portfolio reasoning exists both as `atlas.analysis.portfolio` (legacy,
  CLI-wired) and `atlas.domains.portfolio` (Blueprint-aligned, not
  CLI-wired).
- Decision/decision-journal logic exists both as top-level
  `atlas/decision/`, `atlas/decision_journal/` (legacy, CLI-wired) and
  `atlas.domains.decision`, `atlas.domains.decision_journal`
  (Blueprint-aligned, not CLI-wired).
- Watchlist reasoning exists both as `atlas.analysis.watchlist` /
  `atlas.watchlist_review` (legacy, CLI-wired) and `atlas.domains.watchlist`
  / `atlas.capabilities.watchlist_intelligence` (Blueprint-aligned, not
  CLI-wired).

This duplication is expected during a deliberate migration and is not itself
a defect. It becomes a defect if the legacy layer keeps growing instead of
shrinking.

## Migration Path

1. Pick one duplicated concern at a time (e.g. portfolio).
2. Migrate the corresponding CLI command(s) to call the
   `atlas.domains`/`atlas.capabilities` structures instead of the legacy
   module. If the legacy and domain data shapes differ, add a small,
   deterministic adapter under `atlas/adapters/` rather than reshaping the
   domain to fit legacy assumptions.
3. Add tests proving behavioral parity with the legacy command before
   removing the legacy call site. If a legacy command has no equivalent
   domain computation (different question, different inputs), prefer adding
   a new, additive read-only command over forcing parity — see Sprint 45's
   `atlas portfolio summary`.
4. Only delete legacy code once nothing references it and parity is proven.
5. Repeat per concern. Do not attempt a single big-bang rewrite.

**Sprint 45 status:** portfolio summary/allocation/concentration reporting
now has a proven bridge (`atlas portfolio summary`) from legacy JSON input
to `atlas.domains.portfolio`. `atlas portfolio analyze` and
`atlas portfolio review` remain fully legacy and are the next candidates,
but require either extending the Portfolio Domain (ticker-fit analysis,
CIO review) or a larger adapter — out of scope for a narrow sprint.

**Sprint 46 status:** `atlas portfolio analyze` now surfaces Portfolio
Domain context (allocation, concentration, cash weight, top holdings)
alongside its unchanged legacy fit-score output, reusing the Sprint 45
adapter unmodified. `atlas portfolio review` remains the only fully-legacy
portfolio command and is the next candidate; it depends on investor profile
and optional market snapshot data that have no Portfolio Domain equivalent
yet, so migrating it will likely require either a profile/market domain or
a narrower additive approach similar to this sprint's.

## Rules for Future Sprints

- New product capabilities are built in `atlas/domains` and
  `atlas/capabilities`, not in the legacy engine layer.
- Domains must not import capabilities, providers, the CLI, or
  frontend/backend/database/services modules.
- Capabilities must not call external APIs or providers directly.
- Providers remain opt-in: importing Atlas, running its test suite, or
  invoking default CLI commands must never trigger network access. Live
  providers are only reachable through explicit flags (e.g.
  `atlas analyze TICKER --provider yahoo`).
- Legacy engine modules may be bug-fixed but should not gain new features.
- No naming that implies "Atlas Edge" (a separate, unrelated product) should
  appear in code, filenames, or docs. If found, it is technical debt to
  rename or remove.

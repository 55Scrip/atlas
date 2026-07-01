# Atlas

Private investment research platform. Local-only. Deterministic. Non-advisory.

**Version:** v0.1.0 — Internal Release Candidate 2 (Sprint 71)

---

## What Atlas Is

Atlas is a local deterministic investment research platform. It organises
structured data — research notes, company analysis, watchlist intelligence,
discovery candidates, and knowledge facts — into a calm, readable Daily Brief.

Atlas does not provide investment recommendations. It does not call external
APIs. It does not use AI or LLMs. It does not fetch live market data or news.

## What Atlas Is Not

- Not an AI trading assistant
- Not a recommendation engine
- Does not produce forecasts or targets
- Does not call external APIs
- Does not use LLMs or AI
- Does not fetch live market data or news
- Does not compare companies as investment opportunities

## Current Capabilities (RC2)

| Capability | Module | Status |
|---|---|---|
| Portfolio Domain | `atlas.domains.portfolio` | Current |
| Research Domain | `atlas.domains.research` | Current |
| Knowledge Domain | `atlas.domains.knowledge` | Current |
| Decision Engine | `atlas.domains.decision` | Current |
| Company Analysis | `atlas.capabilities.company_analysis` | Current |
| Watchlist Intelligence | `atlas.capabilities.watchlist_intelligence` | Current — `--knowledge` flag added (RC2) |
| Discovery | `atlas.capabilities.discovery` | Current |
| Daily Brief | `atlas.capabilities.daily_brief` | Current — all five input surfaces (RC2) |
| JSON export pipeline | `atlas.cli` + `atlas.adapters` | Current |
| Local demo | `examples/daily_brief_demo/` | Current — portfolio + evidence link resolution (RC2) |

Legacy engines (`atlas/analysis/`, `atlas/daily/`, `atlas/intelligence/`, etc.)
remain functional. New product work belongs in `atlas/domains/` and
`atlas/capabilities/` only. See [Architecture State](#architecture-state).

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Run Tests

```bash
.venv/bin/python -m compileall atlas tests
.venv/bin/python -m pytest
```

947 tests pass as of RC2.

## Quickstart: Daily Brief Demo

```bash
bash scripts/run_daily_brief_demo.sh
```

Runs a 7-step local pipeline (AMD + NVDA demo data) with no network calls.
Outputs to `tmp/atlas_demo/` including `daily_brief.txt`.

```bash
rm -rf tmp/atlas_demo   # clean up
```

Full details: [examples/daily_brief_demo/README.md](examples/daily_brief_demo/README.md)

## Architecture State

Atlas has two layers:

**Current (Blueprint-aligned):**
- `atlas/domains/` — canonical concepts: portfolio, research, knowledge, decision, daily_brief, watchlist, ai, authentication
- `atlas/capabilities/` — product capabilities: company_analysis, discovery, watchlist_intelligence, daily_brief
- `atlas/shared/` — immutable canonical entities
- `atlas/adapters/` — bridges between domain types and legacy types
- `atlas/providers/` — opt-in market data providers (not called by demo or Daily Brief)
- `atlas/cli/` — CLI commands

**Legacy (preserved, not for expansion):**
- `atlas/analysis/`, `atlas/daily/`, `atlas/dashboard/`, `atlas/home/`,
  `atlas/intelligence/`, `atlas/portfolio_review/`, `atlas/watchlist_review/`,
  and others — original working engines. Remain functional and fully tested.
  New capabilities belong in `atlas/domains/` and `atlas/capabilities/`.

See [docs/ArchitectureConsolidation.md](docs/ArchitectureConsolidation.md) for guardrails.

## Documentation

| Document | Purpose |
|---|---|
| [docs/ATLAS_CONSTITUTION.md](docs/ATLAS_CONSTITUTION.md) | Mission and values |
| [docs/ATLAS_PRODUCT.md](docs/ATLAS_PRODUCT.md) | Product scope |
| [docs/ATLAS_ARCHITECTURE.md](docs/ATLAS_ARCHITECTURE.md) | Architecture intent |
| [docs/ArchitectureConsolidation.md](docs/ArchitectureConsolidation.md) | Current layer map and guardrails |
| [docs/LegacyConsolidationPlan.md](docs/LegacyConsolidationPlan.md) | Legacy module inventory and migration plan |
| [docs/DailyBrief.md](docs/DailyBrief.md) | Daily Brief capability reference |
| [docs/CompanyAnalysis.md](docs/CompanyAnalysis.md) | Company Analysis reference |
| [docs/DecisionLog.md](docs/DecisionLog.md) | Sprint decision history |
| [docs/ReleaseCandidate.md](docs/ReleaseCandidate.md) | RC1 and RC2 release notes |
| [docs/DevelopmentGuide.md](docs/DevelopmentGuide.md) | Developer guide |
| [docs/SprintHistory.md](docs/SprintHistory.md) | Historical sprint notes (Sprints 37–72) |
| [examples/daily_brief_demo/README.md](examples/daily_brief_demo/README.md) | Demo walkthrough |

## Constraints

Providers are opt-in. The demo pipeline and Daily Brief make no network calls.
No UI. No AI. No external APIs. No recommendation language.

---

## Sprint History

Historical sprint notes (Sprints 37–72) have been moved to
[docs/SprintHistory.md](docs/SprintHistory.md).

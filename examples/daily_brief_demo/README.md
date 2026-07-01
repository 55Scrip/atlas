# Atlas Daily Brief Demo

## Purpose

This demo shows how Atlas produces a Daily Brief from local structured inputs.

All steps are local-only, deterministic, and make no network calls. This is not
live market analysis. The data represents demo research context, not real-time facts.

## Files

| File | Purpose |
|---|---|
| `knowledge.json` | Structured knowledge facts about AMD for the demo |
| `research_input.json` | Research project input (`{"projects": [...]}` format) |
| `watchlist_input.json` | Watchlist input (`{"name": ..., "items": [...]}` format) |

## Prerequisites

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Quick Start

Run the demo script from the repository root:

```bash
bash scripts/run_daily_brief_demo.sh
```

## Manual Step-by-Step

```bash
mkdir -p tmp/atlas_demo

# Step 1 — Export research projects to Daily Brief–compatible JSON
atlas research export \
  --input examples/daily_brief_demo/research_input.json \
  --output tmp/atlas_demo/research.json

# Step 2 — Run watchlist intelligence
atlas watchlist intelligence \
  --input examples/daily_brief_demo/watchlist_input.json \
  --output tmp/atlas_demo/watchlist.json

# Step 3 — Generate discovery candidates
atlas discovery export \
  --knowledge examples/daily_brief_demo/knowledge.json \
  --research tmp/atlas_demo/research.json \
  --watchlist tmp/atlas_demo/watchlist.json \
  --output tmp/atlas_demo/discovery.json

# Step 4 — Run company analysis engine (no network calls)
atlas company-analysis export \
  --ticker AMD \
  --company-name "AMD Corporation" \
  --sector "Semiconductors" \
  --country "USA" \
  --business-description "AMD designs high-performance CPUs and GPUs." \
  --knowledge examples/daily_brief_demo/knowledge.json \
  --research tmp/atlas_demo/research.json \
  --output tmp/atlas_demo/company_analysis.json

# Step 5 — Generate Daily Brief
atlas daily summary \
  --research tmp/atlas_demo/research.json \
  --watchlist tmp/atlas_demo/watchlist.json \
  --discovery tmp/atlas_demo/discovery.json \
  --company-analysis tmp/atlas_demo/company_analysis.json
```

## Expected Output

The Daily Brief will include:

- **What Deserves Attention** — always present
- **Research Context** — from the AMD research project
- **Watchlist Context** — from the AMD watchlist item
- **Discovery Context** — discovery candidates derived from the demo knowledge
- **Company Analysis Context** — engine-derived AMD analysis with knowledge facts

Unknowns will reflect the state of the demo data. With all metadata flags and
knowledge facts supplied, only research-level unknowns remain (e.g. open
questions about GPU market share).

## Clean Up

```bash
rm -rf tmp/atlas_demo
```

## Known Limitations

- Company analysis confidence depends on how many knowledge facts are supplied.
  The demo provides five facts; adding more would increase evidence coverage.
- Discovery candidates depend on the overlap between knowledge facts, research
  topics, and watchlist tickers.
- The pipeline does not fetch live data at any step.

## What This Is Not

- Not live market analysis.
- Not investment advice.
- Not a recommendation to buy, sell, or take any action.
- Not a price target or forecast.

## Recommendation for Sprint 59

Add a second demo company (e.g. NVDA) to the example dataset to demonstrate
multi-company Daily Brief composition, showing Research Context, Watchlist
Context, and Company Analysis Context for two companies in a single summary.

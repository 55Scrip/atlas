# Atlas Daily Brief Demo — AMD + NVDA

## Purpose

This demo shows how Atlas produces a Daily Brief from local structured inputs
for two companies: AMD and NVDA.

All steps are local-only, deterministic, and make no network calls. This is not
live market analysis. The data represents demo research context, not real-time
facts. AMD and NVDA are used as demo examples only — no comparisons between
them as investment opportunities are made or implied.

## Files

| File | Purpose |
|---|---|
| `knowledge.json` | Structured knowledge facts for AMD (5 facts) and NVDA (4 facts) |
| `research_input.json` | Research projects for AMD (4 questions) and NVDA (3 questions) |
| `watchlist_input.json` | Watchlist items for AMD and NVDA |

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

# Step 1 — Export research projects (AMD + NVDA)
atlas research export \
  --input examples/daily_brief_demo/research_input.json \
  --output tmp/atlas_demo/research.json

# Step 2 — Run watchlist intelligence (AMD + NVDA)
atlas watchlist intelligence \
  --input examples/daily_brief_demo/watchlist_input.json \
  --output tmp/atlas_demo/watchlist.json

# Step 3 — Generate discovery candidates
atlas discovery export \
  --knowledge examples/daily_brief_demo/knowledge.json \
  --research tmp/atlas_demo/research.json \
  --watchlist tmp/atlas_demo/watchlist.json \
  --output tmp/atlas_demo/discovery.json

# Step 4 — Run AMD company analysis engine
atlas company-analysis export \
  --ticker AMD \
  --company-name "AMD Corporation" \
  --sector "Semiconductors" \
  --country "USA" \
  --business-description "AMD designs high-performance CPUs and GPUs." \
  --knowledge examples/daily_brief_demo/knowledge.json \
  --research tmp/atlas_demo/research.json \
  --output tmp/atlas_demo/company_analysis_amd.json

# Step 5 — Run NVDA company analysis engine
atlas company-analysis export \
  --ticker NVDA \
  --company-name "NVIDIA Corporation" \
  --sector "Semiconductors" \
  --country "USA" \
  --business-description "NVIDIA designs GPUs and accelerated computing platforms." \
  --knowledge examples/daily_brief_demo/knowledge.json \
  --research tmp/atlas_demo/research.json \
  --output tmp/atlas_demo/company_analysis_nvda.json

# Step 6 — Merge company analysis exports into a single list
atlas company-analysis merge \
  --inputs tmp/atlas_demo/company_analysis_amd.json \
  --inputs tmp/atlas_demo/company_analysis_nvda.json \
  --output tmp/atlas_demo/company_analysis.json

# Step 7 — Generate Daily Brief
atlas daily summary \
  --research tmp/atlas_demo/research.json \
  --watchlist tmp/atlas_demo/watchlist.json \
  --discovery tmp/atlas_demo/discovery.json \
  --company-analysis tmp/atlas_demo/company_analysis.json
```

## Multi-Company Daily Brief Behavior

`atlas daily summary --company-analysis` accepts a JSON array of company
analysis reports. Both AMD and NVDA appear in:

- **Research Context** — two research projects, 7 open questions total
- **Watchlist Context** — 4 open watchlist questions across both companies
- **Discovery Context** — 2 discovery candidates (one per company)
- **Company Analysis Context** — 2 company analysis reports
- **Unresolved Questions** — 7 questions, 4 AMD + 3 NVDA

Step 6 uses `atlas company-analysis merge` to combine the two individual
exports into a single JSON array. The full demo is now expressible entirely
in Atlas CLI commands — no `python3 -c` step required.

## Expected Output Structure

```
Atlas Daily Brief

Opening Summary
7 research question(s) remain unresolved. 2 company analysis report(s) available
for review. Watchlist context is available for review. 2 discovery candidate(s)
identified.
Overall priority: moderate

What Deserves Attention
Research Context      ← AMD Research, NVDA Research
Watchlist Context     ← 4 open questions across AMD + NVDA
Discovery Context     ← 2 candidates
Company Analysis Context  ← AMD + NVDA
Unresolved Questions  ← 7 questions from both projects
```

## Clean Up

```bash
rm -rf tmp/atlas_demo
```

## Known Limitations

- The CLI `--company-analysis` flag accepts one file. Multiple company analysis
  reports are supported by merging them with `atlas company-analysis merge` first
  (step 6 above).
- Knowledge facts from both companies are passed to each individual company
  analysis export. The engine filters by subject_node_id match internally.

## Evidence Gaps Behavior

When full metadata (`--sector`, `--country`, `--business-description`) and
knowledge facts (`--knowledge`) are supplied, the daily brief will **not** show
an Evidence Gaps section — this is correct. Evidence gaps only appear when a
company analysis report contains "Missing Evidence" unknowns, which happens when
no knowledge facts are available for that company.

## What This Is Not

- Not live market analysis.
- Not investment advice.
- Not a comparison of AMD and NVDA as investment opportunities.
- Not a recommendation to buy, hold, or take any action.
- Not a price target or forecast.

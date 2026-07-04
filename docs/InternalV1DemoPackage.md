# Atlas Internal v1 Demo Package

**Sprint:** 235
**Date:** 2026-07-04
**Audience:** Internal testers and developers

Atlas supports better judgment. It does not replace it.

---

## What This Demo Shows

Atlas is a CLI-first, local-only, deterministic investment research platform.
This demo shows the complete safe user journey that Atlas can perform today:

1. Validate a Snapshot Draft
2. Review a Snapshot Draft (read-only)
3. Create a confirmed draft copy
4. Create a rejected draft copy
5. Export confirmed research notes to a local file
6. Export confirmed company facts to a local file
7. Run Weekly Investment Review using those local files

All steps are local-only. No network calls. No broker login. No AI. No OCR.
No live data. No external APIs. No investment recommendations.

---

## Prerequisites

Atlas must be installed in a local virtualenv:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Verify:

```bash
atlas --help
```

---

## Safety Boundary

This demo:

- makes no broker connections (no Avanza, Nordnet, or any other)
- makes no network calls of any kind
- uses no live market data or live prices
- uses no external APIs
- uses no AI, LLM, or computer vision
- uses no OCR or image parsing
- executes no trades or orders
- does not mutate any example files in the repository
- writes only to `/tmp/atlas_internal_v1_demo/`
- can be reset by deleting that directory

---

## Demo Commands

Run from the repository root. All commands use example files from the repository.
Temporary outputs go to `/tmp/atlas_internal_v1_demo/`.

### Stage 1 — Validate Snapshot Drafts

Validation checks that a draft file is well-formed and schema-compliant.
No files are written.

```bash
atlas snapshot validate examples/snapshot_drafts/research_notes_snapshot.json
atlas snapshot validate examples/snapshot_drafts/research_notes_snapshot_confirmed.json
atlas snapshot validate examples/snapshot_drafts/company_facts_snapshot_confirmed.json
```

Expected checkpoints:
- `Status: valid`
- Snapshot Type is visible (e.g. `research_notes_snapshot`, `company_facts_snapshot`)
- Confirmation Status is visible (e.g. `draft`, `confirmed`)
- Safety boundary is shown

### Stage 2 — Review Snapshot Drafts

Review shows a read-only confirmation checklist. No files are written.

```bash
atlas snapshot review examples/snapshot_drafts/research_notes_snapshot.json
atlas snapshot review examples/snapshot_drafts/company_facts_snapshot_confirmed.json
```

Expected checkpoints:
- `Status: reviewable`
- Exportable status shown (`yes` or `no` with reason)
- Extracted fields summarised (no unbounded output)
- Uncertainties and missing fields listed
- Blocking issues listed
- Safety boundary: "Review is read-only. Review does not confirm the draft."

### Stage 3 — Confirm a Draft Copy

Confirm writes a new confirmed draft copy. The original draft is never modified.

```bash
atlas snapshot confirm \
  examples/snapshot_drafts/research_notes_snapshot.json \
  --output-draft /tmp/atlas_internal_v1_demo/research_notes_confirmed.json \
  --overwrite
```

Expected checkpoints:
- `Status: confirmed`
- Input and output paths both shown
- "Original draft was not modified."
- "No Atlas local input files were changed."
- "Export commands must still be run separately."

Verify original unchanged:
```bash
atlas snapshot validate examples/snapshot_drafts/research_notes_snapshot.json
# confirmation_status should still show: draft
```

### Stage 4 — Reject a Draft Copy

Reject writes a new rejected draft copy. The original draft is never modified.
Rejected drafts cannot be exported.

```bash
atlas snapshot reject \
  examples/snapshot_drafts/research_notes_snapshot.json \
  --output-draft /tmp/atlas_internal_v1_demo/research_notes_rejected.json \
  --overwrite
```

Expected checkpoints:
- `Status: rejected`
- Input and output paths both shown
- "Original draft was not modified."
- "Rejected drafts are not exportable."

Verify rejected draft is not exportable:
```bash
atlas snapshot export-research-notes \
  /tmp/atlas_internal_v1_demo/research_notes_rejected.json \
  --output-dir /tmp/atlas_internal_v1_demo/notes_from_rejected
# Expected: Status: blocked
```

### Stage 5 — Export Research Notes

Export the confirmed draft to a local research notes file.
Only the research notes file is written. No other files are changed.

```bash
atlas snapshot export-research-notes \
  /tmp/atlas_internal_v1_demo/research_notes_confirmed.json \
  --output-dir /tmp/atlas_internal_v1_demo/research_notes \
  --overwrite
```

Expected checkpoints:
- `Status: written`
- Ticker and output file path shown
- "Only local research notes were written."
- "No portfolio, watchlist, journal, or company facts files were changed."

Output file: `/tmp/atlas_internal_v1_demo/research_notes/ASML/notes.md`

### Stage 6 — Export Company Facts

Export the confirmed company facts draft to a local JSON file.
Only the company facts file is written. No other files are changed.

```bash
atlas snapshot export-company-facts \
  examples/snapshot_drafts/company_facts_snapshot_confirmed.json \
  --output-dir /tmp/atlas_internal_v1_demo/company_facts \
  --overwrite
```

Expected checkpoints:
- `Status: written`
- Ticker and output file path shown
- "Only local company facts were written."
- "No portfolio, watchlist, journal, or research notes files were changed."

Output file: `/tmp/atlas_internal_v1_demo/company_facts/ASML.json`

### Stage 7 — Run Weekly Investment Review

Run the Weekly Review using all available local inputs including the exported
research notes and company facts from the previous stages.

```bash
atlas weekly-review \
  --portfolio examples/weekly_review/portfolio.json \
  --watchlist examples/weekly_review/watchlist.json \
  --profile examples/weekly_review/investor_profile.json \
  --journal examples/weekly_review/decision_journal.json \
  --company-facts /tmp/atlas_internal_v1_demo/company_facts \
  --financials examples/weekly_review/financials \
  --research-notes /tmp/atlas_internal_v1_demo/research_notes \
  --as-of 2026-01-01 \
  --scope-notes examples/weekly_review/scope_notes.md
```

Expected checkpoints:
- All 10 sections render
- Input Status shows `Company facts: Available` and `Research notes: N ticker(s) with local notes`
- Section 1 lists company facts and research notes as optional inputs loaded
- Section 8 shows per-ticker evidence gaps from watchlist and research notes; ASML company facts gap absent
- Section 9 shows follow-up questions and risks from research notes
- Section 10 shows reasons to wait from evidence gaps and research notes
- No input warnings
- No forbidden language in output

---

## Automated Demo Script

The full demo flow above is available as a reproducible script:

```bash
bash scripts/run_internal_v1_demo.sh
```

The script:
- writes only to `/tmp/atlas_internal_v1_demo/`
- cleans and recreates that directory on each run
- prints stage headings and pass/fail checkpoints
- exits non-zero on any failure
- makes no network calls
- requires no credentials

---

## User Journey in Plain Language

A user has written notes about a company. They encode those notes as an Atlas
Snapshot Draft — a local JSON file that describes what they found and how
confident they are in it.

Atlas can validate the draft (is it well-formed?), review it (is it ready to
export?), and help the user decide whether to confirm or reject it.

If confirmed, Atlas exports the content to a local research notes file or a
local company facts file. These files are the inputs to the Weekly Review.

The Weekly Review reads the local files and produces a deterministic 10-section
output that surfaces portfolio context, watchlist state, evidence gaps, open
questions, and reasons to wait. It does not make recommendations. It does not
fetch external data. It does not connect to a broker.

All output is derived from user-supplied local files. All judgment remains with
the user.

---

## What Is Intentionally Out of Scope

The following capabilities are not part of Atlas internal v1 and are not shown
in this demo:

| Capability | Status |
|-----------|--------|
| Portfolio snapshot draft conversion | Deferred |
| Watchlist snapshot draft conversion | Deferred |
| Journal snapshot draft conversion | Deferred |
| Company facts content analysis | Deferred |
| Financial CSV numerical analysis | Presence check only |
| OCR / image parsing | Not implemented |
| Screenshot ingestion | Not implemented |
| AI / LLM extraction | Not implemented |
| Broker sync (Avanza, Nordnet, or any other) | Not implemented |
| Live market data or live prices | Not implemented |
| Live news or earnings release ingestion | Not implemented |
| Multilingual renderer output | Deferred |
| User interface or dashboard | Deferred |
| Investment recommendations of any kind | Not implemented — by design |
| Valuation forecasts or analyst-style targets | Not implemented — by design |
| Market-timing signals | Not implemented — by design |

---

## Cleanup

The demo writes only to `/tmp/atlas_internal_v1_demo/`. To reset:

```bash
rm -rf /tmp/atlas_internal_v1_demo
```

No repository files are modified by the demo.

---

## What Atlas Can Demonstrate Today

| Capability | Command |
|-----------|---------|
| Snapshot Draft validation | `atlas snapshot validate` |
| Snapshot Draft review (read-only) | `atlas snapshot review` |
| Draft confirmation (non-mutating copy) | `atlas snapshot confirm` |
| Draft rejection (non-mutating copy) | `atlas snapshot reject` |
| Research notes export | `atlas snapshot export-research-notes` |
| Company facts export | `atlas snapshot export-company-facts` |
| Weekly Investment Review (10 sections) | `atlas weekly-review` |

All commands are local-only, deterministic, and provider-free.

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [docs/AtlasWeeklyReviewUsageGuide.md](AtlasWeeklyReviewUsageGuide.md) | Full Weekly Review usage guide |
| [docs/AtlasSnapshotInputWorkflow.md](AtlasSnapshotInputWorkflow.md) | Snapshot Input workflow specification |
| [docs/InternalV1ReleaseCandidate.md](InternalV1ReleaseCandidate.md) | v1 release candidate status |
| [docs/DecisionLog.md](DecisionLog.md) | Sprint-by-sprint decision record |
